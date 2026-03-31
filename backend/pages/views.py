from django.shortcuts import render


def home(request):
    """
    Homepage for SwedeSweets.

    Acts as entrypoint to the site
    """
    return render(request, "pages/home.html") 


def about(request):
    """
    About page for SwedeSweets.

    Contains information about the company and its mission.
    """
    return render(request, "pages/about.html")


def contact(request):
    """
    Contact page for SwedeSweets.

    Contains contact information for users to reach out.
    """
    return render(request, "pages/contact.html")
