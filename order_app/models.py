from django.db import models
from django.utils.timezone import now
from product_app.models import Product
from user_app.models import User

class OrderManager(models.Manager):
    def with_details(self):
        """Optimize query with related data"""
        return self.select_related('creator').prefetch_related(
            'productorder_set__product__company'
        )

class Order(models.Model):
    date = models.DateTimeField(default=now)
    creator = models.ForeignKey(
        User,
        related_name="user_orders",
        on_delete=models.CASCADE
    )
    product_orders = models.ManyToManyField(
        Product,
        related_name="product_orders",
        through="ProductOrder"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['creator']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.date.strftime('%Y-%m-%d')}"

    def get_total_items(self):
        """Get total number of items in order"""
        return self.productorder_set.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    def get_company(self):
        """Get the company for this order (assumes all items from same company)"""
        first_item = self.productorder_set.select_related(
            'product__company'
        ).first()
        return first_item.product.company if first_item else None

class ProductOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'order']
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class EmailDraft(models.Model):
    """Store email drafts for orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='email_drafts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_drafts')

    to_email = models.EmailField()
    from_email = models.EmailField()
    subject = models.CharField(max_length=255)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Draft for Order #{self.order.id} - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"