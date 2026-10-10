from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property
from typing import Any

from django import forms
from django.forms import BaseFormSet, formset_factory
from django.utils.translation import gettext as _

from business.datatypes import BusinessOfferLineInput
from business.offer_choices import build_business_offer_choice_context
from customers.models import Customer
from ops_portal.products.presentation import (
    translated_product_catalog_label,
    translated_product_name,
)
from orders.models import Order
from orders.order_limits import (
    MAX_QUANTITY_PER_PRODUCT_PER_ORDER,
    is_unusually_large_order_line,
)
from pricing.models import CommercialPrice
from products.images import product_image_url
from products.models import Product

# extra=0 below - lines are never pre-rendered blank; they only ever appear
# via order_lines.js in response to a selection in AddOrderLineProductForm.
DEFAULT_ORDER_LINE_COUNT = 0

MAX_UNITS_PER_PRODUCT_PER_ORDER = MAX_QUANTITY_PER_PRODUCT_PER_ORDER


class CustomerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, customer: Customer) -> str:
        city = getattr(customer, "city", "")

        if city:
            return f"{customer.name} — {city}"

        return customer.name


class BusinessOfferSelect(forms.Select):
    """A select whose options carry the product's picture, name, weight,
    stock and offer, for the enhanced dropdown (enhanced_selects.js) to
    draw. The field fills the data (BusinessOfferChoiceField.option_data):
    Django asks the widget, not the field, for each option."""

    option_field: BusinessOfferChoiceField | None = None

    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )

        if value and self.option_field is not None:
            option["attrs"].update(
                self.option_field.option_data(
                    value.instance
                )
            )

        return option


class BusinessOfferChoiceField(forms.ModelChoiceField):
    widget = BusinessOfferSelect

    def __init__(
        self,
        *args,
        available_units_by_offer_id: dict[int, int] | None = None,
        language_code: str | None = None,
        show_available_units: bool = True,
        **kwargs,
    ) -> None:
        self.available_units_by_offer_id = (
            available_units_by_offer_id or {}
        )
        self.language_code = language_code
        self.show_available_units = show_available_units
        super().__init__(*args, **kwargs)
        self.widget.option_field = self

    def __deepcopy__(self, memo):
        # Each form gets its own copy of the field and its widget: point
        # the copied widget at the copied field (its stock numbers).
        result = super().__deepcopy__(memo)
        result.widget.option_field = result
        return result

    def label_from_instance(
        self,
        offer: CommercialPrice,
    ) -> str:
        available_units = (
            self.available_units_by_offer_id.get(
                offer.id
            )
        )
        offer_label = self._offer_label(
            offer
        )

        if (
            available_units is None
            or not self.show_available_units
        ):
            return offer_label

        return _(
            "%(offer_label)s · %(available_quantity)s left"
        ) % {
            "offer_label": offer_label,
            "available_quantity": available_units,
        }

    def option_data(
        self,
        offer: CommercialPrice,
    ) -> dict[str, str]:
        product = offer.product

        return {
            "data-code": product.code_label,
            "data-name": self._product_name(
                product
            ),
            "data-weight": product.unit_weight_label,
            "data-offer-detail": _offer_detail(
                offer
            ),
            "data-image": product_image_url(product) or "",
            "data-stock": self._stock_label(offer),
            "search": (
                f"{product.code_label} "
                f"{product.internal_number or ''} "
                f"{product.brand} "
                f"{product.name} "
                f"{product.display_name} "
                f"{self._product_name(product)} "
                f"{self._product_label(product)} "
                f"{product.sku} "
                f"{_offer_detail(offer)}"
            ),
        }

    def _stock_label(
        self,
        offer: CommercialPrice,
    ) -> str:
        available_units = (
            self.available_units_by_offer_id.get(
                offer.id
            )
        )

        if (
            available_units is None
            or not self.show_available_units
        ):
            return ""

        return _("%(available_quantity)s left") % {
            "available_quantity": available_units,
        }

    def _offer_label(
        self,
        offer: CommercialPrice,
    ) -> str:
        product_label = self._product_label(
            offer.product
        )
        offer_detail = _offer_detail(
            offer
        )

        if not offer_detail:
            return product_label

        return (
            f"{product_label} · "
            f"{offer_detail}"
        )

    def _product_label(
        self,
        product: Product,
    ) -> str:
        if self.language_code:
            return translated_product_catalog_label(
                product,
                language_code=self.language_code,
            )

        return (
            f"{product.code_label} · "
            f"{product.display_name} · "
            f"{product.unit_weight_label}"
        )

    def _product_name(
        self,
        product: Product,
    ) -> str:
        if self.language_code:
            return translated_product_name(
                product,
                language_code=self.language_code,
            )

        return product.display_name


class OrderCreateForm(forms.Form):
    customer = CustomerChoiceField(
        queryset=Customer.objects.order_by("name"),
        label="Customer",
        empty_label="Choose customer",
        error_messages={
            "required": "Choose a customer.",
            "invalid_choice": "Choose a valid customer.",
        },
        widget=forms.Select(
            attrs={
                "data-enhanced-select": "true",
                "data-enhanced-select-search": "true",
            }
        ),
    )


class AddOrderLineProductForm(forms.Form):
    """Standalone BUSINESS offer picker used to create formset lines.

    The selected value is a CommercialPrice id. The field is not itself
    submitted as an order line; order_lines.js copies the selected offer id
    into the hidden field of a newly created OrderLineForm.
    """

    commercial_offer = BusinessOfferChoiceField(
        queryset=CommercialPrice.objects.none(),
        required=False,
        label="Add product offer",
        empty_label="Choose a product offer to add",
        error_messages={
            "invalid_choice": "Choose a valid available offer.",
        },
        widget=BusinessOfferSelect(
            attrs={
                "placeholder": "Search by product name or number",
                "data-add-order-line-select": "true",
                "data-enhanced-select": "true",
                "data-enhanced-select-search": "true",
            }
        ),
    )

    def __init__(
        self,
        *args,
        offer_queryset=None,
        available_units_by_offer_id: dict[int, int] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        offer_field = self.fields["commercial_offer"]
        # Each option shows the product's picture: load the profiles
        # with the offers, not one query per option.
        offer_field.queryset = (
            offer_queryset.select_related("product__profile")
            if offer_queryset is not None
            else CommercialPrice.objects.none()
        )
        offer_field.available_units_by_offer_id = (
            available_units_by_offer_id or {}
        )


class OrderLineForm(forms.Form):
    commercial_offer = BusinessOfferChoiceField(
        queryset=CommercialPrice.objects.none(),
        required=False,
        error_messages={
            "invalid_choice": "Choose a valid available offer.",
        },
        widget=forms.HiddenInput(
            attrs={
                "data-order-line-offer-input": "true",
            }
        ),
    )

    # How many of the product's stock unit (boxes, pieces).
    quantity = forms.IntegerField(
        required=False,
        min_value=1,
        error_messages={
            "invalid": "Enter a whole number.",
            "min_value": "Quantity must be greater than 0.",
        },
        widget=forms.NumberInput(
            attrs={
                "class": "quantity-stepper__input",
                "inputmode": "numeric",
                "autocomplete": "off",
                "data-quantity-input": "true",
            }
        ),
    )

    def __init__(
        self,
        *args,
        offer_queryset=None,
        available_units_by_offer_id: dict[int, int] | None = None,
        **kwargs,
    ) -> None:
        self.available_units_by_offer_id = (
            available_units_by_offer_id or {}
        )

        super().__init__(*args, **kwargs)

        offer_field = self.fields["commercial_offer"]
        offer_field.queryset = (
            offer_queryset
            if offer_queryset is not None
            else CommercialPrice.objects.none()
        )

        if isinstance(
            offer_field,
            BusinessOfferChoiceField,
        ):
            offer_field.available_units_by_offer_id = (
                self.available_units_by_offer_id
            )

        self.fields["quantity"].widget.attrs["step"] = "1"

    @cached_property
    def offer_view(self) -> OrderLineOfferView | None:
        """The line's offer as the line shows it, from the submitted or
        initial value, so a line keeps its picture and name when the form
        comes back with an error. None for the empty template line."""

        try:
            offer_id = int(
                self["commercial_offer"].value()
            )
        except (TypeError, ValueError):
            return None

        offer = (
            CommercialPrice.objects
            .select_related(
                "product__profile",
                "batch",
            )
            .filter(pk=offer_id)
            .first()
        )

        if offer is None:
            return None

        return build_order_line_offer_view(offer)

    def clean(self) -> dict:
        cleaned_data = super().clean()

        offer = cleaned_data.get(
            "commercial_offer"
        )
        quantity = cleaned_data.get(
            "quantity"
        )

        if offer is None and quantity is None:
            return cleaned_data

        if offer is None:
            self.add_error(
                "commercial_offer",
                "Choose an offer for this line.",
            )

        if quantity is None:
            self.add_error(
                "quantity",
                "Enter a quantity for this line.",
            )

        if offer is None or quantity is None:
            return cleaned_data

        product = offer.product

        available_units = (
            self.available_units_by_offer_id.get(
                offer.id
            )
        )

        if is_unusually_large_order_line(
            quantity=quantity
        ) and not _is_stock_shortage(
            requested_quantity=quantity,
            available_quantity=available_units,
        ):
            maximum = product.stock_quantity_label(
                MAX_QUANTITY_PER_PRODUCT_PER_ORDER
            )
            self.add_error(
                "quantity",
                (
                    "This line is unusually large. "
                    f"Maximum is {maximum} per product."
                ),
            )

        return cleaned_data

    @property
    def has_line_data(self) -> bool:
        if not hasattr(
            self,
            "cleaned_data",
        ):
            return False

        return bool(
            self.cleaned_data.get(
                "commercial_offer"
            )
            or self.cleaned_data.get(
                "quantity"
            ) is not None
        )

    def to_business_offer_line_input(
        self,
    ) -> BusinessOfferLineInput:
        offer = self.cleaned_data[
            "commercial_offer"
        ]

        return BusinessOfferLineInput(
            commercial_offer_id=offer.pk,
            quantity=self.cleaned_data[
                "quantity"
            ],
        )


class BaseOrderLineFormSet(BaseFormSet):
    def __init__(
        self,
        *args,
        order: Order | None = None,
        **kwargs,
    ) -> None:
        self.order = order
        self.offer_choice_context = (
            build_business_offer_choice_context(
                order=order,
            )
        )
        super().__init__(
            *args,
            **kwargs,
        )

    def get_form_kwargs(
        self,
        index: int | None,
    ) -> dict[str, Any]:
        kwargs = super().get_form_kwargs(
            index
        )

        kwargs.update(
            {
                "offer_queryset": (
                    self.offer_choice_context.queryset
                ),
                "available_units_by_offer_id": (
                    self.offer_choice_context
                    .available_units_by_offer_id
                ),
            }
        )

        return kwargs

    def clean(self) -> None:
        super().clean()

        if any(
            form.errors
            for form in self.forms
        ):
            return

        if not self.order_line_forms:
            raise forms.ValidationError(
                "Add at least one order line."
            )

        requested_quantity_by_offer_id: dict[
            int,
            int,
        ] = defaultdict(int)
        requested_quantity_by_product_id: dict[
            int,
            int,
        ] = defaultdict(int)
        offers_by_id: dict[
            int,
            CommercialPrice,
        ] = {}
        products_by_id: dict[
            int,
            Product,
        ] = {}

        for form in self.order_line_forms:
            offer = form.cleaned_data[
                "commercial_offer"
            ]
            quantity = form.cleaned_data[
                "quantity"
            ]
            product = offer.product

            requested_quantity_by_offer_id[
                offer.id
            ] += quantity
            requested_quantity_by_product_id[
                product.id
            ] += quantity

            offers_by_id[
                offer.id
            ] = offer
            products_by_id[
                product.id
            ] = product

        for (
            offer_id,
            requested_quantity,
        ) in requested_quantity_by_offer_id.items():
            available_quantity = (
                self.offer_choice_context
                .available_units_by_offer_id
                .get(
                    offer_id,
                    0,
                )
            )

            if (
                requested_quantity
                > available_quantity
            ):
                offer = offers_by_id[
                    offer_id
                ]
                product = offer.product

                offer_detail = _offer_detail(
                    offer
                )
                offer_description = (
                    f" ({offer_detail})"
                    if offer_detail
                    else ""
                )

                raise forms.ValidationError(
                    f"Only "
                    f"{product.stock_quantity_label(available_quantity)} "
                    f"available for "
                    f"{product.display_name}"
                    f"{offer_description}."
                )

        for (
            product_id,
            requested_quantity,
        ) in requested_quantity_by_product_id.items():
            if is_unusually_large_order_line(
                quantity=requested_quantity
            ):
                product = products_by_id[
                    product_id
                ]

                maximum = product.stock_quantity_label(
                    MAX_QUANTITY_PER_PRODUCT_PER_ORDER
                )
                raise forms.ValidationError(
                    f"{product.display_name} is unusually large. "
                    f"Maximum is {maximum} per order."
                )

    @property
    def order_line_forms(
        self,
    ) -> list[OrderLineForm]:
        return [
            form
            for form in self.forms
            if form.has_line_data
        ]


OrderLineFormSet = formset_factory(
    OrderLineForm,
    formset=BaseOrderLineFormSet,
    extra=DEFAULT_ORDER_LINE_COUNT,
)


class OrderCancelForm(forms.Form):
    reason = forms.ChoiceField(
        choices=Order.CancelReason.choices,
        label="Cancellation reason",
        error_messages={
            "required": "Choose a cancellation reason.",
            "invalid_choice": "Choose a valid cancellation reason.",
        },
    )

    note = forms.CharField(
        required=False,
        label="Cancellation note",
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Optional: add a short note.",
            }
        ),
    )


def build_add_order_line_product_form(
    *,
    line_formset: OrderLineFormSet,
) -> AddOrderLineProductForm:
    return AddOrderLineProductForm(
        offer_queryset=(
            line_formset.offer_choice_context.queryset
        ),
        available_units_by_offer_id=(
            line_formset.offer_choice_context
            .available_units_by_offer_id
        ),
    )


def build_order_line_inputs(
    formset: BaseFormSet,
) -> list[BusinessOfferLineInput]:
    return [
        form.to_business_offer_line_input()
        for form in formset.order_line_forms
    ]


def build_order_line_initial_data(
    order: Order,
) -> list[dict[str, object]]:
    return [
        {
            "commercial_offer": (
                line.commercial_offer_id
            ),
            "quantity": line.quantity_in_units,
        }
        for line in (
            order.lines
            .order_by("id")
        )
    ]


def _offer_detail(
    offer: CommercialPrice,
) -> str:
    # Ops is choosing a commercial offer, so show the commercial reason,
    # not the physical batch identity behind it. Standard is the normal
    # case and stays unlabeled to keep the picker visually quiet.
    if offer.batch_id is None:
        return ""

    if offer.reason:
        return str(
            offer.get_reason_display()
        )

    # Defensive fallback for legacy/incomplete batch offers.
    return f"Batch {offer.batch.batch_id}"


@dataclass(frozen=True, slots=True)
class OrderLineOfferView:
    """A line of the order form, drawn like the lines of a cart or an
    order: the picture circle, the name, and the grey lines under it."""

    name: str
    meta: str
    offer_detail: str
    image_url: str | None


def build_order_line_offer_view(
    offer: CommercialPrice,
) -> OrderLineOfferView:
    product = offer.product

    return OrderLineOfferView(
        name=product.display_name,
        meta=(
            f"{product.code_label} · "
            f"{product.unit_weight_label}"
        ),
        offer_detail=_offer_detail(offer),
        image_url=product_image_url(product),
    )


def _is_stock_shortage(
    *,
    requested_quantity: int,
    available_quantity: int | None,
) -> bool:
    if available_quantity is None:
        return False

    return requested_quantity > available_quantity
