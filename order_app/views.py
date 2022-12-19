from django.shortcuts import render, redirect
from company_app.models import Company
from .models import Product

# Create your views here.
def dashboard(request):
    # For later
    # if not "user_id" in request.session:
    #    return redirect("/")
    return render(request, "dashboard.html")


# Order related pages
def view_orders(request):
    # For later
    # if not "user_id" in request.session:
    #     return redirect("/")
    return render(request, "view_orders.html")

# Product related pages
def view_products(request):
    # For later
    # if not "user_id" in request.session:
    #     return redirect("/")

    first_company = Company.objects.all().first()

    # Get all associated products if there are any
    company_products = Product.objects.filter(company=first_company)

    context = {
        "company": first_company,
        "company_products": company_products
    }

    return render(request, "view_products.html", context)