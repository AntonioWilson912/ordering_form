from django.db import models
from django.utils.timezone import now
from company_app.models import Company
from user_app.models import User
from .item_types import *

# Create your models here.

class Product(models.Model):
    company = models.ForeignKey(Company, related_name="company_products", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    item_no = models.CharField(default="")
    qty = models.PositiveIntegerField(default=0)
    item_type = models.CharField(choices=ITEM_TYPES)
    active = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['item_no']

    def __str__(self):
        return self.name

class Order(models.Model):
    date = models.DateTimeField(default=now, blank=True)
    creator = models.ForeignKey(User, related_name="user_orders")

    product_orders = models.ManyToManyField(Product, related_name="product_orders", through="ProductOrder")

    class Meta:
        ordering = ['date', 'creator']

    def __str__(self):
        return f"Order #{self.id}"

class ProductOrder(models.Model):
    product = models.ForeignKey(Product)
    order = models.ForeignKey(Order)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)