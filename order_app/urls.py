from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path('', views.OrderListView.as_view(), name='order_list'),
    path('new/', views.NewOrderView.as_view(), name='new_order'),
    path('<int:pk>/edit/', views.EditOrderView.as_view(), name='edit_order'),
]