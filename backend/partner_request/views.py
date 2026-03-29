from django.shortcuts import render, redirect
from .models import PartnerRequest


def apply(request):
    """
    Display and process partner application form.
    """

    if request.method == "POST":
        PartnerRequest.objects.create(
            name=request.POST.get("name"),
            store_name=request.POST.get("store_name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            message=request.POST.get("message"),
        )

        return redirect("apply_thanks")

    return render(request, "partner_request/apply.html")


def apply_thanks(request):
    """
    Simple confirmation page after submission.
    """
    return render(request, "partner_request/thanks.html")
