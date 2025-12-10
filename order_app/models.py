from django.db import models
from django.utils.timezone import now
from product_app.models import Product
from user_app.models import User


class OrderManager(models.Manager):
    def with_details(self):
        """Optimize query with related data"""
        return self.select_related("creator").prefetch_related(
            "productorder_set__product__company"
        )


class Order(models.Model):
    date = models.DateTimeField(default=now)
    creator = models.ForeignKey(
        User, related_name="user_orders", on_delete=models.CASCADE
    )
    product_orders = models.ManyToManyField(
        Product, related_name="product_orders", through="ProductOrder"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["-date"]),
            models.Index(fields=["creator"]),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.date.strftime('%Y-%m-%d')}"

    def get_total_items(self):
        """Get total number of items in order"""
        return (
            self.productorder_set.aggregate(total=models.Sum("quantity"))["total"] or 0
        )

    def get_item_count(self):
        """Get number of different products in order"""
        return self.productorder_set.count()

    def get_company(self):
        """Get the company for this order (assumes all items from same company)"""
        first_item = self.productorder_set.select_related("product__company").first()
        return first_item.product.company if first_item else None

    def get_products_dict(self):
        """Get dict of product_id: quantity for this order"""
        return {po.product_id: po.quantity for po in self.productorder_set.all()}

    def update_items(self, items_dict):
        """
        Update order items from a dict of product_id: quantity.
        Removes items with quantity 0, adds new items, updates existing.
        """
        current_items = {po.product_id: po for po in self.productorder_set.all()}

        for product_id, quantity in items_dict.items():
            product_id = int(product_id)
            quantity = int(quantity)

            if quantity > 0:
                if product_id in current_items:
                    # Update existing
                    po = current_items[product_id]
                    if po.quantity != quantity:
                        po.quantity = quantity
                        po.save(update_fields=["quantity", "updated_at"])
                else:
                    # Add new
                    ProductOrder.objects.create(
                        order=self, product_id=product_id, quantity=quantity
                    )
            else:
                # Remove if exists
                if product_id in current_items:
                    current_items[product_id].delete()

        # Update the order's updated_at timestamp
        self.save(update_fields=["updated_at"])


class ProductOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["product", "order"]
        indexes = [
            models.Index(fields=["order", "product"]),
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class EmailDraft(models.Model):
    """Store email drafts for orders"""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="email_drafts"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="email_drafts"
    )

    to_email = models.EmailField()
    from_email = models.EmailField()
    subject = models.CharField(max_length=255)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Draft for Order #{self.order.id} - {self.updated_at.strftime('%Y-%m-%d %H:%M')}"
