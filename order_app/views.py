from django.shortcuts import render

# Create your views here.
def view_products(request):
    return render("view_products.html")