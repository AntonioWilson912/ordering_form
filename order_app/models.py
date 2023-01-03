from django.db import models
from django.utils.timezone import now
from company_app.models import Company
from user_app.models import User
from .item_types import *

# Create your models here.
class ProductManager(models.Manager):
    def validate_new_product(self, product_data):
        errors = {}

        if int(product_data["company_id"]) == -1:
            errors["company_error"] = "Must select a company."
        if len(product_data["name"]) < 3:
            errors["name_error"] = "Name must be at least 3 characters long."
        if (product_data["item_type"]) != "C" and product_data["item_type"] != "W":
            errors["item_type_error"] = "Must choose an item type."

        # Test if the selected company already has the input item number
        if len(product_data["item_no"]) > 0:
            selected_company = Company.objects.filter(id=int(product_data["company_id"])).first()
            if not selected_company:
                errors["company_error"] = "You selected a company from the black hole."
            else:
                company_products = Product.objects.filter(company=selected_company, item_no=product_data["item_no"])
                if len(company_products) > 0:
                    errors["item_no_error"] = "That item number for the selected company is already in use."

        return errors

class Product(models.Model):
    company = models.ForeignKey(Company, related_name="company_products", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    item_no = models.CharField(max_length=12, default="")
    qty = models.PositiveIntegerField(default=0)
    item_type = models.CharField(max_length=1, choices=ITEM_TYPES)
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        ordering = ['company', 'item_no']

    def __str__(self):
        return self.name

class Order(models.Model):
    date = models.DateTimeField(default=now, blank=True)
    creator = models.ForeignKey(User, related_name="user_orders", on_delete=models.CASCADE)

    product_orders = models.ManyToManyField(Product, related_name="product_orders", through="ProductOrder")

    class Meta:
        ordering = ['date', 'creator']

    def __str__(self):
        return f"Order #{self.id}"

class ProductOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING) # These on_delete's might have to be changed later
    order = models.ForeignKey(Order, on_delete=models.DO_NOTHING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)