from django.shortcuts import redirect, render

from .forms import PartnerRequestForm


def apply(request):
    """
    Display and process the public partner interest form.

    DESIGN:
    - GET: render an empty form
    - POST: validate and persist
    - Success redirects to a thank-you page (PRG pattern)

    Why this shape:
    - keeps HTTP concerns in the view
    - keeps validation in the form
    - keeps persistence rules in the model
    """
    if request.method == "POST":
        form = PartnerRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("apply_thanks")
    else:
        form = PartnerRequestForm()

    return render(
        request,
        "partner_request/apply.html",
        {"form": form},
    )


def apply_thanks(request):
    """
    Simple confirmation page after successful submission.
    """
    return render(request, "partner_request/thanks.html")
