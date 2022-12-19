from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("orders/all", views.view_orders, name="all_orders"),
    path("all", views.view_products, name="all_products"),
]