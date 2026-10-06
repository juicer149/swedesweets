from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from customers.errors import InvalidCustomerData
from customers.models import Customer
from customers.selectors import list_customers
from customers.services import create_customer, update_customer
from ops_portal.customers.detail_viewmodels import (
    build_customer_detail_context,
)
from ops_portal.customers.form_viewmodels import (
    build_create_customer_form_context,
    build_edit_customer_form_context,
)
from ops_portal.customers.forms import (
    CustomerForm,
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
            try:
                updated_customer = update_customer(
                    customer=customer,
                    user=request.user,
                    **form.cleaned_data,
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
                    **form.cleaned_data,
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
