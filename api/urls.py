from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Product endpoints
    path('products/company/<int:company_id>/', views.get_company_products, name='get_company_products'),
    path('products/create/', views.CreateProductView.as_view(), name='create_product'),

    # Order endpoints
    path('orders/create/', views.CreateOrderView.as_view(), name='create_order'),
    path('orders/<int:order_id>/update/', views.UpdateOrderView.as_view(), name='update_order'),
    path('orders/send-email/', views.SendOrderEmailView.as_view(), name='send_order_email'),
    path('orders/<int:order_id>/draft/', views.EmailDraftView.as_view(), name='get_email_draft'),
    path('orders/save-draft/', views.EmailDraftView.as_view(), name='save_email_draft'),
    path('orders/<int:order_id>/export-csv/', views.export_order_csv, name='export_order_csv'),

    # User/Email endpoints
    path('user/email-info/', views.UserEmailInfoView.as_view(), name='user_email_info'),
    path('email/render-template/', views.RenderTemplateView.as_view(), name='render_template'),
]