from django.shortcuts import render, redirect
from django.http import JsonResponse
from company_app.models import Company
from .models import *
from .forms import *

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
    context = {
        #"logged_in_user": User.objects.get(id=request.session["user_id"])
    }
    return render(request, "dashboard.html", context)


# Order related pages
def new_order(request):
    # if not "user_id" in request.session:
    #     return redirect("/")
    context = {
        #"logged_in_user": User.objects.get(id=request.session["user_id"]),
        "all_companies": Company.objects.all()
    }

    return render(request, "new_order.html", context)

def create_order(request):
    # if not "user_id" in request.session:
    #     return redirect("/")

    # Extract all the ordered_product pairs and put each pair in a list as a dictionary
    ordered_products = []
    ordered_products_dict_list = []

    for key, value in request.POST.items():
        if key.startswith("ordered_products"):
            ordered_products.append(value)

    for i in range(0, len(ordered_products) - 1, 2):
        ordered_products_dict_list.append({ ordered_products[i]: int(ordered_products[i + 1])})

    if len(ordered_products_dict_list) == 0:
        return JsonResponse({ "message": "No products were ordered." })

    # Get the logged in user
    #logged_in_user = User.objects.get(id=request.session["user_id"])

    # Create an order
    #new_order = Order.objects.create(creator=logged_in_user)

    # Find the associated products
    for ordered_product_dict in ordered_products_dict_list:
        for product_name, product_qty in ordered_product_dict.items():
            product_id = int(product_name.replace("product", ""))
            current_product = Product.objects.get(id=product_id)

            # Add the current product to the order
            #ProductOrder.objects.create(product=current_product, order=new_order)

            print(current_product.name, "has an order for", product_qty)


    return JsonResponse({ "message": "Received at least one ordered product." })

def view_orders(request):
    # For later
    # if not "user_id" in request.session:
    #     return redirect("/")
    context = {
        #"logged_in_user": User.objects.get(id=request.session["user_id"])
    }
    return render(request, "view_orders.html", context)

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
        # "logged_in_user": User.objects.get(id=request.session["user_id"])
        "all_companies": Company.objects.all(),
        "new_product_form": NewProductForm()
    }

    return render(request, "new_product.html", context)

def create_product(request):
    # if not "user_id" in request.session:
        # return redirect("/")

    errors = Product.objects.validate_new_product(request.POST)
    if len(errors) > 0:
        return JsonResponse({ "errors": errors })

    selected_company = Company.objects.get(id=int(request.POST["company_id"]))
    Product.objects.create(company=selected_company, name=request.POST["name"], item_no=request.POST["item_no"], item_type=request.POST["item_type"])

    return JsonResponse({ "success": "All fields were good."})

def view_products(request):
    # For later
    # if not "user_id" in request.session:
    #     return redirect("/")

    first_company = Company.objects.all().first()

    # Get all associated products if there are any
    company_products = Product.objects.filter(company=first_company)

    all_products = Product.objects.all()

    context = {
        #"logged_in_user": User.objects.get(id=request.session["user_id"]),
        "all_products": all_products,
        "company": first_company,
        "company_products": company_products
    }

    return render(request, "view_products.html", context)