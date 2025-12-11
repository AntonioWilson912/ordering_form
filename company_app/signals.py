from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from .models import Company


@receiver(pre_save, sender=Company)
def log_company_status_changes(sender, instance, **kwargs):
    """
    Track when a company is activated or deactivated.
    Useful for notifying admins or logging changes.
    """
    if instance.pk:
        try:
            old_instance = Company.objects.get(pk=instance.pk)
            if old_instance.is_active != instance.is_active:
                # Status changed
                if instance.is_active:
                    print(f"Company '{instance.name}' was activated")
                    # Could send notification to admins
                else:
                    print(f"Company '{instance.name}' was deactivated")
                    # Could send notification to users with pending orders
        except Company.DoesNotExist:
            pass


@receiver(post_save, sender=Company)
def create_company_welcome_data(sender, instance, created, **kwargs):
    """
    When a new company is created, you could:
    - Create sample products
    - Send welcome email to company contact
    - Create default categories
    """
    if created:
        # Example: Log company creation
        print(f"New company created: {instance.name}")


@receiver(pre_delete, sender=Company)
def prevent_company_deletion_with_orders(sender, instance, **kwargs):
    """
    Prevent deletion of companies that have associated orders.
    Or alternatively, mark them as inactive instead.
    """
    from order_app.models import Order

    # Check if company has any orders
    order_count = Order.objects.filter(
        productorder__product__company=instance
    ).distinct().count()

    if order_count > 0:
        raise Exception(
            f"Cannot delete company '{instance.name}' - it has {order_count} associated order(s). "
            f"Consider marking it as inactive instead."
        )