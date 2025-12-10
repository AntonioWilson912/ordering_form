from django.db import models


class CompanyManager(models.Manager):
    def active(self):
        """Return only active companies"""
        return self.filter(is_active=True)

    def with_product_counts(self):
        """Return companies with product counts annotated"""
        return self.annotate(
            product_count=models.Count("company_products"),
            active_product_count=models.Count(
                "company_products", filter=models.Q(company_products__active=True)
            ),
        )


class Company(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(
        default=True, help_text="Inactive companies will not appear in order creation."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CompanyManager()

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

    def get_active_products(self):
        """Return active products for this company"""
        return self.company_products.filter(active=True)

    def get_product_count(self):
        """Return total product count"""
        return self.company_products.count()

    def get_active_product_count(self):
        """Return active product count"""
        return self.company_products.filter(active=True).count()
