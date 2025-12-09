from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Product endpoints
    path('products/company/<int:company_id>/', views.get_company_products, name='get_company_products'),
    path('products/create/', views.create_product, name='create_product'),

    # Order endpoints
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/send-email/', views.send_order_email, name='send_order_email'),
    path('orders/<int:order_id>/draft/', views.get_email_draft, name='get_email_draft'),
    path('orders/save-draft/', views.save_email_draft, name='save_email_draft'),
    path('orders/<int:order_id>/export-csv/', views.export_order_csv, name='export_order_csv'),
]