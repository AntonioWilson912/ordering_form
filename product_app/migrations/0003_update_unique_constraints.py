from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_app', '0002_alter_product_unique_together_and_more'),
    ]

    operations = [
        # Remove old unique_together if it exists
        migrations.AlterUniqueTogether(
            name='product',
            unique_together=set(),
        ),

        # Add proper unique constraints
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(
                fields=['company', 'name'],
                name='unique_product_name_per_company'
            ),
        ),
        migrations.AddConstraint(
            model_name='product',
            constraint=models.UniqueConstraint(
                fields=['company', 'item_no'],
                condition=models.Q(item_no__gt=''),
                name='unique_item_no_per_company_when_not_empty'
            ),
        ),
    ]