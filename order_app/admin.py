from django.contrib import admin
from .models import Order, ProductOrder, EmailDraft

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'creator', 'date', 'get_total_items']
    list_filter = ['date', 'creator']
    ordering = ['-date']

    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'

@admin.register(ProductOrder)
class ProductOrderAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'created_at']
    list_filter = ['order', 'product__company']
    ordering = ['-created_at']

@admin.register(EmailDraft)
class EmailDraftAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'to_email', 'subject', 'updated_at']
    list_filter = ['user', 'updated_at']
    ordering = ['-updated_at']
    readonly_fields = ['created_at', 'updated_at']