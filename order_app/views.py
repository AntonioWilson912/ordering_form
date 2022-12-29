from django.shortcuts import render, redirect
from django.http import JsonResponse
from company_app.models import Company
from .models import *

# Create your views here.
def convert_product_to_json(product):
    product_dict = {}

    product_dict["id"] = product.id
    product_dict["name"] = product.name
    product_dict["item_no"] = product.item_no
    product_dict["qty"] = product.qty
    product_dict["item_type"] = product.item_type

    return product_dict


def dashboard(request):
    # For later
    # if not "user_id" in request.session:
    #    return redirect("/")
    return render(request, "dashboard.html")


# Order related pages
def new_order(request):
    # if not "user_id" in request.session:
    #     return redirect("/")
    context = {
        "all_companies": Company.objects.all()
    }

    return render(request, "new_order.html", context)

def view_orders(request):
    # For later
    # if not "user_id" in request.session:
    #     return redirect("/")
    return render(request, "view_orders.html")

def get_company_products(request):
    # For later
    # if not "user_id" in request.session:
    #     return redirect("/")
    if request.POST["company_id"] == "-1":
        return JsonResponse({"company_error": "Must select a company."})

    selected_company = Company.objects.filter(id=request.POST["company_id"]).first()
    if not selected_company:
        return JsonResponse({"company_error": "You've reached an unknown company."})

    company_products = Product.objects.filter(company=selected_company, active=True)
    all_products = []
    for this_product in company_products:
        all_products.append(convert_product_to_json(this_product))

    if len(all_products) == 0:
        return JsonResponse({ "company_error": "This company does not feature any products." })

    return JsonResponse({ "company_products": all_products, "company_name": selected_company.name })

# Product related pages
def new_product(request):
    # if not "user_id" in request.session:
    #     return redirect("/")

    context = {
        "all_companies": Company.objects.all()
    }

    return render(request, "new_product.html", context)

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