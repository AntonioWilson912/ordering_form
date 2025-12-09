from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from core.decorators import ajax_required
from company_app.models import Company
from core.mixins import login_required_ajax
from product_app.models import Product
from order_app.models import Order, ProductOrder, EmailDraft
from user_app.models import User
from .serializers import ProductDTO, OrderDTO
import csv

@ajax_required
@login_required_ajax
@require_POST
def get_company_products(request, company_id):
    """AJAX endpoint to fetch products for a company"""
    try:
        if company_id == -1 or company_id == "-1":
            return JsonResponse({
                'success': False,
                'message': 'Please select a company.'
            }, status=400)

        company = Company.objects.prefetch_related('company_products').get(id=company_id)
        products = company.company_products.filter(active=True)

        if not products.exists():
            return JsonResponse({
                'success': False,
                'message': f'{company.name} does not have any active products.'
            }, status=400)

        # Convert to DTOs
        product_dtos = [ProductDTO.from_model(p) for p in products]

        return JsonResponse({
            'success': True,
            'company_id': company.id,
            'company_name': company.name,
            'products': [dto.to_dict() for dto in product_dtos]
        })

    except Company.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Company not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@ajax_required
@login_required_ajax
@require_POST
@transaction.atomic
def create_order(request):
    """AJAX endpoint to create a new order"""
    try:
        # Parse order data
        order_items = []

        for key in request.POST:
            if key.startswith('product_'):
                product_id = int(key.replace('product_', ''))
                quantity = int(request.POST[key])

                if quantity > 0:
                    order_items.append({
                        'product_id': product_id,
                        'quantity': quantity
                    })

        if not order_items:
            return JsonResponse({
                'success': False,
                'message': 'Please select at least one product with quantity greater than 0.'
            }, status=400)

        # Get user (use session for now, replace with proper auth later)
        user_id = request.session.get('user_id')
        if not user_id:
            # Temporary: use first user
            user = User.objects.first()
            if not user:
                return JsonResponse({
                    'success': False,
                    'message': 'No users found in system.'
                }, status=400)
        else:
            user = User.objects.get(id=user_id)

        # Create order
        order = Order.objects.create(creator=user)

        # Create order items
        for item_data in order_items:
            product = Product.objects.select_related('company').get(
                id=item_data['product_id']
            )
            ProductOrder.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity']
            )

        # Return DTO
        order_dto = OrderDTO.from_model(order)

        return JsonResponse({
            'success': True,
            'message': 'Order created successfully!',
            'order': order_dto.to_dict()
        })

    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'One or more products not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@ajax_required
@login_required_ajax
@require_POST
@transaction.atomic
def create_product(request):
    """AJAX endpoint to create a new product"""
    try:
        company_id = request.POST.get('company_id')
        name = request.POST.get('name')
        item_no = request.POST.get('item_no', '')
        item_type = request.POST.get('item_type')

        # Validate
        errors = Product.objects.validate_new_product(request.POST)
        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

        # Create product
        company = Company.objects.get(id=int(company_id))
        product = Product.objects.create(
            company=company,
            name=name,
            item_no=item_no,
            item_type=item_type
        )

        product_dto = ProductDTO.from_model(product)

        return JsonResponse({
            'success': True,
            'message': 'Product created successfully!',
            'product': product_dto.to_dict()
        })

    except Company.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Company not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)

@ajax_required
@login_required_ajax
@require_POST
def send_order_email(request):
    """Send order email"""
    try:
        to_email = request.POST.get('to')
        from_email = request.POST.get('from', settings.DEFAULT_FROM_EMAIL)
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        order_id = request.POST.get('order_id')

        if not all([to_email, subject, content, order_id]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields'
            }, status=400)

        # Get order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            }, status=404)

        # Send email
        send_mail(
            subject=subject,
            message=content,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )

        # Delete draft after successful send
        if request.user.is_authenticated:
            EmailDraft.objects.filter(
                order=order,
                user=request.user
            ).delete()

        return JsonResponse({
            'success': True,
            'message': 'Email sent successfully!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to send email: {str(e)}'
        }, status=500)

@ajax_required
@login_required_ajax
@require_POST
def save_email_draft(request):
    """Save email draft"""
    try:
        order_id = request.POST.get('order_id')
        to_email = request.POST.get('to')
        from_email = request.POST.get('from')
        subject = request.POST.get('subject')
        content = request.POST.get('content')

        if not all([order_id, to_email, from_email, subject, content]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields'
            }, status=400)

        # Get order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            }, status=404)

        # Get user (for now use first user if not authenticated)
        user = request.user if request.user.is_authenticated else User.objects.first()

        # Update or create draft
        draft, created = EmailDraft.objects.update_or_create(
            order=order,
            user=user,
            defaults={
                'to_email': to_email,
                'from_email': from_email,
                'subject': subject,
                'content': content
            }
        )

        return JsonResponse({
            'success': True,
            'message': 'Draft saved successfully!',
            'draft_id': draft.id,
            'updated_at': draft.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to save draft: {str(e)}'
        }, status=500)

@ajax_required
@login_required_ajax
@require_GET
def get_email_draft(request, order_id):
    """Get email draft for an order"""
    try:
        order = Order.objects.get(id=order_id)
        user = request.user if request.user.is_authenticated else User.objects.first()

        draft = EmailDraft.objects.filter(
            order=order,
            user=user
        ).first()

        if draft:
            return JsonResponse({
                'success': True,
                'draft': {
                    'to': draft.to_email,
                    'from': draft.from_email,
                    'subject': draft.subject,
                    'content': draft.content,
                    'updated_at': draft.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No draft found'
            })

    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required_ajax
@require_GET
def export_order_csv(request, order_id):
    """Export order as CSV"""
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
        return JsonResponse({'error': 'Order not found'}, status=404)