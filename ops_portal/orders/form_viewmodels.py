from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.urls import reverse

from accounts.roles import RoleSpec
from ops_portal.orders.access import can_cancel_order
from ops_portal.orders.detail_viewmodels import (
    build_order_cancel_back_url,
    build_order_detail_context,
    order_cancel_href,
    order_detail_href,
)
from ops_portal.orders.forms import (
    AddOrderLineProductForm,
    OrderCancelForm,
    OrderCreateForm,
    OrderLineFormSet,
    build_add_order_line_product_form,
)
from ops_portal.orders.presentation import order_status_icon
from ops_portal.orders.recent_orders import (
    OpsRecentOrder,
    build_ops_recent_orders,
)
from orders.models import Order


@dataclass(frozen=True)
class OrderFormContext:
    title: str
    description: str
    submit_label: str
    cancel_url: str
    line_formset: OrderLineFormSet
    add_product_form: AddOrderLineProductForm
    form: OrderCreateForm | None = None
    order: Order | None = None
    status_icon: str = ""
    is_edit: bool = False
    cancel_order_url: str = ""
    # The customer's last orders above the product search: drawn here on
    # an edit; on a new order fetched (recent_orders_url) once a customer
    # is chosen.
    recent_orders: tuple[OpsRecentOrder, ...] = ()
    recent_orders_url: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "recent_orders": self.recent_orders,
            "recent_orders_url": self.recent_orders_url,
            "form": self.form,
            "line_formset": self.line_formset,
            "add_product_form": self.add_product_form,
            "order": self.order,
            "status_icon": self.status_icon,
            "title": self.title,
            "description": self.description,
            "submit_label": self.submit_label,
            "cancel_url": self.cancel_url,
            "is_edit": self.is_edit,
            "cancel_order_url": self.cancel_order_url,
        }


@dataclass(frozen=True)
class CancelOrderFormContext:
    order: Order
    form: OrderCancelForm
    title: str
    description: str
    submit_label: str
    cancel_url: str

    def as_dict(self) -> dict[str, Any]:
        context = build_order_detail_context(
            order=self.order,
            title=self.title,
            description=self.description,
            cancel_url=self.cancel_url,
        ).as_dict()

        context["form"] = self.form
        context["submit_label"] = self.submit_label

        return context


def build_create_order_form_context(
    *,
    form: OrderCreateForm,
    line_formset: OrderLineFormSet,
) -> OrderFormContext:
    return OrderFormContext(
        form=form,
        line_formset=line_formset,
        add_product_form=build_add_order_line_product_form(
            line_formset=line_formset,
        ),
        title="Place order",
        description="Create an order and reserve available stock.",
        submit_label="Place order",
        cancel_url=reverse("ops_orders:index"),
        is_edit=False,
        recent_orders_url=reverse("ops_orders:customer_recent_orders"),
    )


def build_edit_order_form_context(
    *,
    order: Order,
    line_formset: OrderLineFormSet,
    role_spec: RoleSpec,
) -> OrderFormContext:
    return OrderFormContext(
        order=order,
        status_icon=order_status_icon(order.status),
        line_formset=line_formset,
        add_product_form=build_add_order_line_product_form(
            line_formset=line_formset,
        ),
        title=f"Edit order #{order.pk}",
        description=(
            "Update this placed order before it is packed. "
            "Reservations will be rebuilt."
        ),
        submit_label="Update order",
        cancel_url=order_detail_href(order),
        is_edit=True,
        recent_orders=build_ops_recent_orders(
            customer=order.customer,
            selectable_offer_ids=set(
                line_formset.offer_choice_context.available_units_by_offer_id
            ),
            exclude_order_id=order.pk,
        ),
        cancel_order_url=(
            order_cancel_href(order)
            if can_cancel_order(
                order=order,
                role_spec=role_spec,
            )
            else ""
        ),
    )


def build_cancel_order_form_context(
    *,
    order: Order,
    form: OrderCancelForm,
    role_spec: RoleSpec,
) -> CancelOrderFormContext:
    return CancelOrderFormContext(
        order=order,
        form=form,
        title="Cancel order",
        description="",
        submit_label="Cancel order",
        cancel_url=build_order_cancel_back_url(
            order=order,
            role_spec=role_spec,
        ),
    )
