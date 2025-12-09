from django.db import models
from company_app.models import Company
from core.constants import ITEM_TYPES, get_item_type_display

class ProductManager(models.Manager):
    def validate_new_product(self, product_data):
        errors = {}

        company_id = product_data.get("company_id", -1)
        try:
            company_id = int(company_id)
        except (ValueError, TypeError):
            company_id = -1

        if company_id == -1:
            errors["company_error"] = "Must select a company."

        name = product_data.get("name", "")
        if len(name) < 3:
            errors["name_error"] = "Name must be at least 3 characters long."

        item_type = product_data.get("item_type", "")
        if item_type not in ["C", "W"]:
            errors["item_type_error"] = "Must choose a valid item type."

        item_no = product_data.get("item_no", "")
        if item_no and company_id != -1:
            if self.filter(company_id=company_id, item_no=item_no).exists():
                errors["item_no_error"] = (
                    "That item number for the selected company is already in use."
                )

        return errors

    def active(self):
        return self.filter(active=True)

    def by_company(self, company):
        return self.filter(company=company)

class Product(models.Model):
    company = models.ForeignKey(
        Company,
        related_name="company_products",
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    item_no = models.CharField(max_length=12, default="", blank=True)
    qty = models.PositiveIntegerField(default=0)
    item_type = models.CharField(max_length=1, choices=ITEM_TYPES)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        ordering = ['company', 'item_no']
        unique_together = ['company', 'item_no']
        indexes = [
            models.Index(fields=['company', 'active']),
            models.Index(fields=['item_no']),
        ]

    def __str__(self):
        display = f"{self.company.name} - {self.name}"
        if self.item_no:
            display += f" ({self.item_no})"
        return display

    def get_item_type_display_name(self):
        return get_item_type_display(self.item_type)