from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from business_portal.selectors import (
    get_portal_customer_for_user,
)
from business_portal.store.forms import (
    CustomerProfileForm,
    build_customer_profile_initial_data,
)
from customers.errors import InvalidCustomerData
from customers.services import (
    update_customer,
    update_store_listing,
)


@login_required
def edit_store(request):
    customer = get_portal_customer_for_user(
        user=request.user,
    )
    # First visit after the invitation: the details are still missing.
    onboarding = not customer.is_complete

    if request.method == "POST":
        form = CustomerProfileForm(
            request.POST,
            customer=customer,
            login_email=request.user.get_username(),
        )

        if form.is_valid():
            data = form.cleaned_data

            try:
                with transaction.atomic():
                    update_customer(
                        customer=customer,
                        user=request.user,
                        **{name: data[name] for name in form.DELIVERY_FIELDS},
                    )
                    update_store_listing(
                        customer=customer,
                        is_listed=data["is_listed"],
                        address_line=data["store_address_line"],
                        city=data["store_city"],
                    )
            except InvalidCustomerData as error:
                form.add_error(
                    None,
                    str(error),
                )
            else:
                messages.success(
                    request,
                    (
                        _("Thank you! You can now order.")
                        if onboarding
                        else _("Store information updated.")
                    ),
                )

                return redirect(
                    "business_portal:index"
                )
    else:
        form = CustomerProfileForm(
            initial=build_customer_profile_initial_data(
                customer
            ),
            customer=customer,
            login_email=request.user.get_username(),
        )

    return render(
        request,
        (
            "business_portal/store_onboarding.html"
            if onboarding
            else "business_portal/store_edit.html"
        ),
        {
            "form": form,
            "customer": customer,
            "onboarding": onboarding,
        },
    )
