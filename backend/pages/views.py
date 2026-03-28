from django.shortcuts import render

def home(request):
    """
    Homepage for SwedeSweets.

    Acts as entrypoint to the site
    """
    return render(request, "pages/home.html") 
