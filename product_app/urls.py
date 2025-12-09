from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('new/', views.NewProductView.as_view(), name='new_product'),
    path('create/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
]