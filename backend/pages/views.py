from django.shortcuts import render


def home(request):
    """
    Render the public homepage.
    """
    return render(request, "pages/home.html")


def about(request):
    """
    Render the public about page.
    """
    return render(request, "pages/about.html")


def contact(request):
    """
    Render the public contact page.
    """
    return render(request, "pages/contact.html")
