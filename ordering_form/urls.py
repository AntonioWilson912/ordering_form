from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user_app.urls')),
    path('dashboard/', include('dashboard.urls')),  # Separate dashboard app
    path('orders/', include('order_app.urls')),
    path('products/', include('product_app.urls')),
    path('companies/', include('company_app.urls')),
    path('api/', include('api.urls')),
]