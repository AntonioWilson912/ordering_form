from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("orders/all", views.view_orders, name="all_orders"),
    path("orders/new", views.new_order, name="new_order"),
    path("orders/company/get_products", views.get_company_products),
    path("orders/create", views.create_order),

    path("all", views.view_products, name="all_products"),
    path("new", views.new_product, name="new_product"),
    path("create", views.create_product)
]