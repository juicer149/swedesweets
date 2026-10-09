from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.errors import AccountCreationError
from accounts.invitations import send_account_invitation_on_commit
from accounts.services import create_customer_account
from customers.errors import InvalidCustomerData
from customers.models import Customer
from customers.selectors import list_customers
from customers.services import (
    create_customer,
    update_customer,
    update_store_listing,
)
from ops_portal.customers.detail_viewmodels import (
    build_customer_detail_context,
)
from ops_portal.customers.form_viewmodels import (
    build_create_customer_form_context,
    build_edit_customer_form_context,
    build_invite_login_form_context,
    build_invite_shop_form_context,
)
from ops_portal.customers.forms import (
    CustomerForm,
    InviteLoginForm,
    InviteShopForm,
    build_customer_edit_initial_data,
)
from ops_portal.customers.list_viewmodels import (
    build_customer_page_rows,
    build_customer_quick_jump_search,
    build_customers_page_header,
)
from orders.selectors import (
    get_customer_order_summary,
)
from orders.selectors import (
    list_customer_orders as list_orders_for_customer,
)


@login_required
def index(request):
    customer_rows = build_customer_page_rows(list(list_customers()))

    return render(
        request,
        "ops_portal/customers/index.html",
        {
            "page_header": build_customers_page_header(
                role_spec=request.role_spec,
            ),
            "customer_rows": customer_rows,
            "quick_jump_search": build_customer_quick_jump_search(customer_rows),
        },
    )


@login_required
def detail(
    request,
    customer_pk: int,
):
    customer = _get_customer_or_404(customer_pk)
    orders = list(
        list_orders_for_customer(
            customer=customer,
        )
    )

    context = build_customer_detail_context(
        customer=customer,
        order_summary=get_customer_order_summary(
            customer=customer,
        ),
        orders=orders,
        role_spec=request.role_spec,
        back_url=reverse("ops_customers:index"),
    ).as_dict()

    return render(
        request,
        "ops_portal/customers/detail.html",
        context,
    )


@login_required
def edit(
    request,
    customer_pk: int,
):
    customer = _get_customer_or_404(customer_pk)

    if request.method == "POST":
        form = CustomerForm(
            request.POST,
            customer=customer,
        )

        if form.is_valid():
            data = form.cleaned_data

            try:
                with transaction.atomic():
                    updated_customer = update_customer(
                        customer=customer,
                        user=request.user,
                        **form.delivery_data,
                    )
                    update_store_listing(
                        customer=updated_customer,
                        is_listed=data["is_listed"],
                        address_line=data["store_address_line"],
                        city=data["store_city"],
                    )
            except InvalidCustomerData as error:
                form.add_error(None, str(error))
            else:
                messages.success(
                    request,
                    (
                        f"Customer "
                        f"{updated_customer.name} updated."
                    ),
                )
                return redirect(
                    "ops_customers:detail",
                    customer_pk=updated_customer.pk,
                )
    else:
        form = CustomerForm(
            initial=build_customer_edit_initial_data(
                customer
            ),
            customer=customer,
        )

    context = build_edit_customer_form_context(
        form=form,
        customer=customer,
    ).as_dict()

    return render(
        request,
        "ops_portal/customers/customer_form.html",
        context,
    )


@login_required
def create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)

        if form.is_valid():
            try:
                customer = create_customer(
                    **form.delivery_data,
                    user=request.user,
                )
            except InvalidCustomerData as error:
                form.add_error(None, str(error))
            else:
                messages.success(
                    request,
                    f"Customer {customer.name} added.",
                )
                return redirect(
                    "ops_customers:index"
                )
    else:
        form = CustomerForm()

    context = build_create_customer_form_context(
        form=form,
    ).as_dict()

    return render(
        request,
        "ops_portal/customers/customer_form.html",
        context,
    )


def _get_customer_or_404(
    customer_pk: int,
) -> Customer:
    return get_object_or_404(
        Customer.objects,
        pk=customer_pk,
    )


@login_required
def invite(request):
    """A new shop and its login in one go; the shop gets an invitation to
    choose a password and fill in the rest of its details."""

    if request.method == "POST":
        form = InviteShopForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    customer = create_customer(
                        **form.delivery_data,
                        user=request.user,
                    )
                    result = create_customer_account(
                        email=customer.email,
                        customer=customer,
                    )
                    _invite(request, user=result.user, customer=customer)
            except (InvalidCustomerData, AccountCreationError) as error:
                form.add_error(None, str(error))
            else:
                messages.success(
                    request,
                    f"{customer.name} invited. The invitation is on its way "
                    f"to {customer.email}.",
                )
                return redirect(
                    "ops_customers:detail",
                    customer_pk=customer.pk,
                )
    else:
        form = InviteShopForm()

    return render(
        request,
        "ops_portal/customers/customer_form.html",
        build_invite_shop_form_context(form=form).as_dict(),
    )


@login_required
def invite_login(request, customer_pk: int):
    """A login for a customer we have already (or a second person)."""

    customer = get_object_or_404(Customer, pk=customer_pk)

    if request.method == "POST":
        form = InviteLoginForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    result = create_customer_account(
                        email=form.cleaned_data["email"],
                        customer=customer,
                    )
                    _invite(request, user=result.user, customer=customer)
            except AccountCreationError as error:
                form.add_error(None, str(error))
            else:
                messages.success(
                    request,
                    f"Invitation on its way to {result.user.email}.",
                )
                return redirect(
                    "ops_customers:detail",
                    customer_pk=customer.pk,
                )
    else:
        form = InviteLoginForm(initial={"email": customer.email})

    return render(
        request,
        "ops_portal/customers/customer_form.html",
        build_invite_login_form_context(
            form=form,
            customer=customer,
        ).as_dict(),
    )


def _invite(request, *, user, customer: Customer) -> None:
    send_account_invitation_on_commit(
        user=user,
        site_url=settings.SITE_URL or request.build_absolute_uri("/"),
        # Shops in France get it in French.
        language="fr" if customer.country == "FR" else "en",
    )
