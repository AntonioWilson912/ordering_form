from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("orders/all", views.view_orders, name="all_orders"),
    path("orders/new", views.new_order, name="new_order"),

    path("all", views.view_products, name="all_products"),
    path("new", views.new_product, name="new_product")
]