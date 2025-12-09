from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'item_no', 'item_type', 'active', 'created_at']
    list_filter = ['company', 'item_type', 'active']
    search_fields = ['name', 'item_no']
    ordering = ['company', 'item_no']