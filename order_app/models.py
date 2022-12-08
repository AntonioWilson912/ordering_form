from django.db import models
from django.utils.timezone import now
from .item_types import *

# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255)

class Product(models.Model):
    company = models.ForeignKey(Company, related_name="company_products", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    vendor_no = models.CharField(default="")
    qty = models.IntegerField(default=0)
    item_type = models.CharField(choices=ITEM_TYPES)

class Order(models.Model):
    date = models.DateTimeField(default=now, blank=True)