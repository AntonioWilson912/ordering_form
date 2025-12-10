from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
import csv

from company_app.models import Company
from product_app.models import Product
from order_app.models import Order, ProductOrder, EmailDraft
from user_app.models import User, EmailTemplate
from user_app.services import EmailService
from core.api_mixins import AjaxRequiredMixin, StandardResponseMixin
from .serializers import (
    ProductSerializer,
    ProductCreateSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def get_company_products(request, company_id):
    """AJAX endpoint to fetch products for a company."""
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return Response(
            {"error": "AJAX request required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if company_id == -1 or str(company_id) == "-1":
        return Response(
            {"success": False, "message": "Please select a company."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        company = Company.objects.prefetch_related("company_products").get(
            id=company_id
        )
        products = company.company_products.filter(active=True)

        if not products.exists():
            return Response(
                {
                    "success": False,
                    "message": f"{company.name} does not have any active products.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProductSerializer(products, many=True)

        return Response(
            {
                "success": True,
                "company_id": company.id,
                "company_name": company.name,
                "products": serializer.data,
            }
        )

    except Company.DoesNotExist:
        return Response(
            {"success": False, "message": "Company not found."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_order_csv(request, order_id):
    """Export order as CSV."""
    try:
        order = Order.objects.get(id=order_id)
        product_orders = order.productorder_set.select_related("product").all()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="order_{order_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(["Order Details"])
        writer.writerow(["Order ID", order.id])
        writer.writerow(["Date", order.date.strftime("%Y-%m-%d %H:%M")])
        writer.writerow(["Created By", order.creator.username])
        writer.writerow([])
        writer.writerow(["Item No", "Product Name", "Type", "Quantity"])

        for po in product_orders:
            writer.writerow(
                [
                    po.product.item_no or "N/A",
                    po.product.name,
                    po.product.get_item_type_display_name(),
                    po.quantity,
                ]
            )

        return response

    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)


class CreateOrderView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """Class-based view for creating orders."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        order_items = {}
        for key, value in request.data.items():
            if key.startswith("product_"):
                product_id = key.replace("product_", "")
                try:
                    quantity = int(value)
                    if quantity > 0:
                        order_items[product_id] = quantity
                except (ValueError, TypeError):
                    pass

        serializer = OrderCreateSerializer(data={"items": order_items})
        if not serializer.is_valid():
            return self.error_response(
                message="Validation failed", errors=serializer.errors
            )

        try:
            order = Order.objects.create(creator=request.user)

            for product_id, quantity in serializer.validated_data["items"].items():
                product = Product.objects.select_related("company").get(id=product_id)
                ProductOrder.objects.create(
                    order=order, product=product, quantity=quantity
                )

            order_serializer = OrderSerializer(order)
            return self.success_response(
                data={"order": order_serializer.data},
                message="Order created successfully!",
                status_code=status.HTTP_201_CREATED,
            )

        except Product.DoesNotExist:
            return self.error_response(
                message="One or more products not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )


class UpdateOrderView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """View for updating existing orders."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return self.error_response(
                message="Order not found.", status_code=status.HTTP_404_NOT_FOUND
            )

        # Parse order items
        order_items = {}
        for key, value in request.data.items():
            if key.startswith("product_"):
                product_id = key.replace("product_", "")
                try:
                    quantity = int(value)
                    order_items[product_id] = quantity
                except (ValueError, TypeError):
                    pass

        # Check if at least one item has quantity > 0
        if not any(qty > 0 for qty in order_items.values()):
            return self.error_response(
                message="Order must have at least one item with quantity greater than 0."
            )

        try:
            order.update_items(order_items)

            order_serializer = OrderSerializer(order)
            return self.success_response(
                data={"order": order_serializer.data},
                message="Order updated successfully!",
            )

        except Exception as e:
            return self.error_response(
                message=f"Failed to update order: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateProductView(
    AjaxRequiredMixin, StandardResponseMixin, generics.CreateAPIView
):
    """Generic view for creating products."""

    serializer_class = ProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            errors = {}
            for field, messages in serializer.errors.items():
                error_key = f"{field}_error"
                errors[error_key] = messages[0] if messages else "Invalid value"

            return self.error_response(message="Validation failed", errors=errors)

        product = serializer.save()
        product_serializer = ProductSerializer(product)

        return self.success_response(
            data={"product": product_serializer.data},
            message="Product created successfully!",
            status_code=status.HTTP_201_CREATED,
        )


class SendOrderEmailView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """View for sending order emails using server email with user's name."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        to_email = request.data.get("to")
        subject = request.data.get("subject")
        content = request.data.get("content")
        order_id = request.data.get("order_id")

        if not all([to_email, subject, content, order_id]):
            return self.error_response(message="Missing required fields")

        try:
            order = Order.objects.get(id=order_id)

            EmailService.send_order_email(
                user=request.user, to_email=to_email, subject=subject, content=content
            )

            EmailDraft.objects.filter(order=order, user=request.user).delete()

            return self.success_response(message="Email sent successfully!")

        except Order.DoesNotExist:
            return self.error_response(
                message="Order not found", status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return self.error_response(
                message=f"Failed to send email: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EmailDraftView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """View for managing email drafts (get and save)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """Get email draft for an order"""
        try:
            order = Order.objects.get(id=order_id)
            draft = EmailDraft.objects.filter(order=order, user=request.user).first()

            if draft:
                return self.success_response(
                    data={
                        "draft": {
                            "to": draft.to_email,
                            "subject": draft.subject,
                            "content": draft.content,
                            "updated_at": draft.updated_at.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    }
                )
            else:
                return self.error_response(message="No draft found")

        except Order.DoesNotExist:
            return self.error_response(
                message="Order not found", status_code=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """Save email draft"""
        order_id = request.data.get("order_id")

        required_fields = ["order_id", "to", "subject", "content"]
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
                    "to_email": request.data.get("to"),
                    "from_email": settings.DEFAULT_FROM_EMAIL,
                    "subject": request.data.get("subject"),
                    "content": request.data.get("content"),
                },
            )

            return self.success_response(
                data={
                    "draft_id": draft.id,
                    "updated_at": draft.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                },
                message="Draft saved successfully!",
            )

        except Order.DoesNotExist:
            return self.error_response(
                message="Order not found", status_code=status.HTTP_404_NOT_FOUND
            )


class UserEmailInfoView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """Get user's email info and templates for the composer."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return user's display name, email info, and templates for composer"""
        user = request.user

        # Get user's email templates
        templates = [
            {
                "id": t.id,
                "name": t.name,
                "subject": t.subject_template,
                "body": t.body_template,
                "is_default": t.is_default,
            }
            for t in user.email_templates.all()
        ]

        return self.success_response(
            data={
                "display_name": user.get_display_name(),
                "sender_name": user.get_email_sender_name(),
                "reply_to_email": user.email,
                "signature": user.email_signature or "",
                "templates": templates,
            }
        )


class RenderTemplateView(AjaxRequiredMixin, StandardResponseMixin, APIView):
    """Render an email template with order data."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        template_id = request.data.get("template_id")
        order_id = request.data.get("order_id")

        if not order_id:
            return self.error_response(message="Order ID required")

        try:
            order = (
                Order.objects.select_related("creator")
                .prefetch_related("productorder_set__product__company")
                .get(id=order_id)
            )
        except Order.DoesNotExist:
            return self.error_response(
                message="Order not found", status_code=status.HTTP_404_NOT_FOUND
            )

        user = request.user
        company = order.get_company()

        # Build order items text
        order_items_lines = []
        for po in order.productorder_set.select_related("product").all():
            quantity = po.quantity
            if po.product.item_type == "C":
                unit = "case" if quantity == 1 else "cases"
            else:
                unit = "lb." if quantity == 1 else "lbs."

            item_no = po.product.item_no or "N/A"
            order_items_lines.append(f"{quantity} {unit} - {item_no} {po.product.name}")

        order_items_text = "\n".join(order_items_lines)

        # Build context
        context = {
            "company_name": company.name if company else "Unknown Company",
            "order_id": str(order.id),
            "order_date": order.date.strftime("%B %d, %Y"),
            "order_items": order_items_text,
            "total_items": str(order.get_total_items()),
            "item_count": str(order.get_item_count()),
            "user_name": user.get_display_name(),
            "user_email": user.email,
            "signature": user.email_signature or "",
        }

        if template_id:
            try:
                template = EmailTemplate.objects.get(id=template_id, user=user)
                subject, body = template.render(context)
            except EmailTemplate.DoesNotExist:
                return self.error_response(message="Template not found")
        else:
            # Use default template or fallback
            default_template = user.get_default_template()
            if default_template:
                subject, body = default_template.render(context)
            else:
                # Fallback
                subject = f"Order Request for {context['company_name']}"
                body = f"Hello,\n\nHere is my order:\n\n{order_items_text}\n\n{context['signature']}"

        return self.success_response(
            data={
                "subject": subject,
                "body": body,
            }
        )
