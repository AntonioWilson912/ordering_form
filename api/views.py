from rest_framework import status, generics, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
import csv

from company_app.models import Company
from product_app.models import Product
from order_app.models import Order, ProductOrder, EmailDraft
from user_app.models import User
from core.api_mixins import AjaxRequiredMixin, StandardResponseMixin
from .serializers import (
    ProductSerializer, ProductCreateSerializer, OrderSerializer,
    OrderCreateSerializer, EmailDraftSerializer, SendEmailSerializer
)


# ============================================================================
# Function-Based Views with DRF Decorators
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_company_products(request, company_id):
    """
    AJAX endpoint to fetch products for a company.
    Demonstrates function-based view with DRF decorators.
    """
    # Check AJAX
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return Response({'error': 'AJAX request required'}, status=status.HTTP_400_BAD_REQUEST)

    if company_id == -1 or str(company_id) == "-1":
        return Response({
            'success': False,
            'message': 'Please select a company.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        company = Company.objects.prefetch_related('company_products').get(id=company_id)
        products = company.company_products.filter(active=True)

        if not products.exists():
            return Response({
                'success': False,
                'message': f'{company.name} does not have any active products.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProductSerializer(products, many=True)

        return Response({
            'success': True,
            'company_id': company.id,
            'company_name': company.name,
            'products': serializer.data
        })

    except Company.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Company not found.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_order_csv(request, order_id):
    """
    Export order as CSV.
    Function-based view for file downloads.
    """
    try:
        order = Order.objects.get(id=order_id)
        product_orders = order.productorder_set.select_related('product').all()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="order_{order_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Order Details'])
        writer.writerow(['Order ID', order.id])
        writer.writerow(['Date', order.date.strftime('%Y-%m-%d %H:%M')])
        writer.writerow(['Created By', order.creator.username])
        writer.writerow([])
        writer.writerow(['Item No', 'Product Name', 'Type', 'Quantity'])

        for po in product_orders:
            writer.writerow([
                po.product.item_no or 'N/A',
                po.product.name,
                po.product.get_item_type_display_name(),
                po.quantity
            ])

        return response

    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# Class-Based Views with DRF
# ============================================================================

class CreateOrderView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """
    Class-based view for creating orders.
    Demonstrates CBV with custom mixins.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # Parse order items from form data
        order_items = {}
        for key, value in request.data.items():
            if key.startswith('product_'):
                product_id = key.replace('product_', '')
                try:
                    quantity = int(value)
                    if quantity > 0:
                        order_items[product_id] = quantity
                except (ValueError, TypeError):
                    pass

        serializer = OrderCreateSerializer(data={'items': order_items})
        if not serializer.is_valid():
            return self.error_response(
                message='Validation failed',
                errors=serializer.errors
            )

        try:
            # Create order
            order = Order.objects.create(creator=request.user)

            # Create order items
            for product_id, quantity in serializer.validated_data['items'].items():
                product = Product.objects.select_related('company').get(id=product_id)
                ProductOrder.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity
                )

            order_serializer = OrderSerializer(order)
            return self.success_response(
                data={'order': order_serializer.data},
                message='Order created successfully!',
                status_code=status.HTTP_201_CREATED
            )

        except Product.DoesNotExist:
            return self.error_response(
                message='One or more products not found.',
                status_code=status.HTTP_404_NOT_FOUND
            )


class CreateProductView(AjaxRequiredMixin, StandardResponseMixin, generics.CreateAPIView):
    """
    Generic view for creating products.
    Demonstrates DRF generics with custom mixins.
    """
    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            # Format errors for frontend compatibility
            errors = {}
            for field, messages in serializer.errors.items():
                error_key = f'{field}_error'
                errors[error_key] = messages[0] if messages else 'Invalid value'

            return self.error_response(
                message='Validation failed',
                errors=errors
            )

        product = serializer.save()
        product_serializer = ProductSerializer(product)

        return self.success_response(
            data={'product': product_serializer.data},
            message='Product created successfully!',
            status_code=status.HTTP_201_CREATED
        )


class SendOrderEmailView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """
    View for sending order emails.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendEmailSerializer(data=request.data)

        if not serializer.is_valid():
            return self.error_response(
                message='Missing required fields',
                errors=serializer.errors
            )

        data = serializer.validated_data

        try:
            order = Order.objects.get(id=data['order_id'])

            send_mail(
                subject=data['subject'],
                message=data['content'],
                from_email=data.get('from_email', settings.DEFAULT_FROM_EMAIL),
                recipient_list=[data['to']],
                fail_silently=False,
            )

            # Delete draft after successful send
            EmailDraft.objects.filter(order=order, user=request.user).delete()

            return self.success_response(message='Email sent successfully!')

        except Order.DoesNotExist:
            return self.error_response(
                message='Order not found',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return self.error_response(
                message=f'Failed to send email: {str(e)}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailDraftView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """
    View for managing email drafts (get and save).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """Get email draft for an order"""
        try:
            order = Order.objects.get(id=order_id)
            draft = EmailDraft.objects.filter(order=order, user=request.user).first()

            if draft:
                return self.success_response(data={
                    'draft': {
                        'to': draft.to_email,
                        'from': draft.from_email,
                        'subject': draft.subject,
                        'content': draft.content,
                        'updated_at': draft.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                    }
                })
            else:
                return self.error_response(message='No draft found')

        except Order.DoesNotExist:
            return self.error_response(
                message='Order not found',
                status_code=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """Save email draft"""
        order_id = request.data.get('order_id')

        required_fields = ['order_id', 'to', 'from', 'subject', 'content']
        missing = [f for f in required_fields if not request.data.get(f)]

        if missing:
            return self.error_response(
                message=f'Missing required fields: {", ".join(missing)}'
            )

        try:
            order = Order.objects.get(id=order_id)

            draft, created = EmailDraft.objects.update_or_create(
                order=order,
                user=request.user,
                defaults={
                    'to_email': request.data.get('to'),
                    'from_email': request.data.get('from'),
                    'subject': request.data.get('subject'),
                    'content': request.data.get('content')
                }
            )

            return self.success_response(
                data={
                    'draft_id': draft.id,
                    'updated_at': draft.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                },
                message='Draft saved successfully!'
            )

        except Order.DoesNotExist:
            return self.error_response(
                message='Order not found',
                status_code=status.HTTP_404_NOT_FOUND
            )