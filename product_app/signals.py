from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import Product


@receiver(pre_save, sender=Product)
def track_product_status_changes(sender, instance, **kwargs):
    """
    Track when products are activated/deactivated.
    Could be used to notify users with products in their carts, etc.
    """
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            if old_instance.active != instance.active:
                if not instance.active:
                    # Product was deactivated
                    print(f"Product '{instance.name}' was deactivated")
                    # Could check if it's in any pending orders
                else:
                    # Product was reactivated
                    print(f"Product '{instance.name}' was reactivated")
        except Product.DoesNotExist:
            pass


@receiver(post_save, sender=Product)
def log_new_product(sender, instance, created, **kwargs):
    """
    Log when new products are added.
    Could be used for inventory notifications, etc.
    """
    if created:
        print(f"New product created: {instance.name} for {instance.company.name}")


@receiver(post_delete, sender=Product)
def log_product_deletion(sender, instance, **kwargs):
    """
    Log product deletions for audit purposes.
    """
    print(f"Product deleted: {instance.name} (ID: {instance.id})")