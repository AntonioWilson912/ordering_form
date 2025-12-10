from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from product_app.models import Product
from order_app.models import Order
from company_app.models import Company


@login_required(login_url="/login/")
def dashboard(request):
    """Main dashboard view"""
    total_orders = Order.objects.count()
    total_products = Product.objects.filter(active=True).count()
    total_companies = Company.objects.count()

    recent_orders = (
        Order.objects.select_related("creator")
        .prefetch_related("productorder_set__product")
        .order_by("-date")[:5]
    )

    context = {
        "page_title": "Dashboard",
        "total_orders": total_orders,
        "total_products": total_products,
        "total_companies": total_companies,
        "recent_orders": recent_orders,
    }
    return render(request, "dashboard/dashboard.html", context)
