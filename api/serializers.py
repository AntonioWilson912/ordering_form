from rest_framework import serializers
from product_app.models import Product
from order_app.models import Order, ProductOrder, EmailDraft
from company_app.models import Company
from user_app.models import User


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model"""
    product_count = serializers.SerializerMethodField()
    active_product_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['id', 'name', 'email', 'product_count', 'active_product_count', 'created_at']

    def get_product_count(self, obj):
        return obj.company_products.count()

    def get_active_product_count(self, obj):
        return obj.company_products.filter(active=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    item_type_display = serializers.CharField(source='get_item_type_display_name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'item_no', 'qty', 'item_type', 'item_type_display',
            'company', 'company_name', 'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductCreateSerializer(serializers.Serializer):
    """Serializer for creating products via AJAX"""
    company_id = serializers.IntegerField()
    name = serializers.CharField(min_length=3, max_length=255)
    item_no = serializers.CharField(required=False, allow_blank=True, max_length=12)
    item_type = serializers.ChoiceField(choices=['C', 'W'])

    def validate_company_id(self, value):
        if value == -1:
            raise serializers.ValidationError("Must select a company.")
        if not Company.objects.filter(id=value).exists():
            raise serializers.ValidationError("Company not found.")
        return value

    def validate(self, data):
        item_no = data.get('item_no', '')
        company_id = data.get('company_id')

        if item_no and company_id:
            if Product.objects.filter(company_id=company_id, item_no=item_no).exists():
                raise serializers.ValidationError({
                    'item_no': "This item number already exists for the selected company."
                })
        return data

    def create(self, validated_data):
        company = Company.objects.get(id=validated_data['company_id'])
        return Product.objects.create(
            company=company,
            name=validated_data['name'],
            item_no=validated_data.get('item_no', ''),
            item_type=validated_data['item_type']
        )


class ProductOrderSerializer(serializers.ModelSerializer):
    """Serializer for ProductOrder (order line items)"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    item_no = serializers.CharField(source='product.item_no', read_only=True)
    item_type = serializers.CharField(source='product.item_type', read_only=True)
    item_type_display = serializers.CharField(source='product.get_item_type_display_name', read_only=True)

    class Meta:
        model = ProductOrder
        fields = ['product', 'product_name', 'item_no', 'item_type', 'item_type_display', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model"""
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    items = ProductOrderSerializer(source='productorder_set', many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'date', 'creator', 'creator_username', 'items',
            'total_items', 'company_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date', 'creator', 'created_at', 'updated_at']

    def get_total_items(self, obj):
        return obj.get_total_items()

    def get_company_name(self, obj):
        company = obj.get_company()
        return company.name if company else None


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders"""
    items = serializers.DictField(child=serializers.IntegerField(min_value=0))

    def validate_items(self, value):
        # Filter out zero quantities
        filtered_items = {k: v for k, v in value.items() if v > 0}
        if not filtered_items:
            raise serializers.ValidationError(
                "Please select at least one product with quantity greater than 0."
            )
        return filtered_items


class EmailDraftSerializer(serializers.ModelSerializer):
    """Serializer for EmailDraft model"""
    class Meta:
        model = EmailDraft
        fields = ['id', 'order', 'to_email', 'from_email', 'subject', 'content', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class SendEmailSerializer(serializers.Serializer):
    """Serializer for sending emails"""
    to = serializers.EmailField()
    from_email = serializers.EmailField(source='from', required=False)
    subject = serializers.CharField(max_length=255)
    content = serializers.CharField()
    order_id = serializers.IntegerField()

    def validate_order_id(self, value):
        if not Order.objects.filter(id=value).exists():
            raise serializers.ValidationError("Order not found.")
        return value