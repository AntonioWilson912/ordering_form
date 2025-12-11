from django.db import models
from company_app.models import Company
from core.constants import ITEM_TYPES, get_item_type_display


class ProductManager(models.Manager):
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
        ordering = ['company', 'item_no', 'name']
        indexes = [
            models.Index(fields=['company', 'active']),
            models.Index(fields=['company', 'item_no']),
            models.Index(fields=['company', 'name']),
        ]
        constraints = [
            # Name must be unique per company
            models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_product_name_per_company'
            ),
            # Item no must be unique per company, but only when not empty
            models.UniqueConstraint(
                fields=['company', 'item_no'],
                condition=models.Q(item_no__gt=''),
                name='unique_item_no_per_company_when_not_empty'
            ),
        ]

    def __str__(self):
        display = f"{self.company.name} - {self.name}"
        if self.item_no:
            display += f" ({self.item_no})"
        return display

    def get_item_type_display_name(self):
        return get_item_type_display(self.item_type)