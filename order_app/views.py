from django.views.generic import ListView, TemplateView
from django.db import models
from core.mixins import PageTitleMixin, LoginRequiredMixin
from company_app.models import Company
from .models import Order

class OrderListView(LoginRequiredMixin, PageTitleMixin, ListView):
    model = Order
    template_name = 'order_app/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    page_title = 'All Orders'

    def get_queryset(self):
        return Order.objects.select_related('creator').prefetch_related(
            'productorder_set__product__company'
        ).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders_with_details = []
        for order in context['orders']:
            product_orders = order.productorder_set.select_related(
                'product__company'
            ).all()

            orders_with_details.append({
                'order': order,
                'items': product_orders,
                'company': product_orders[0].product.company if product_orders else None,
                'total_quantity': sum(po.quantity for po in product_orders)
            })

        context['orders_with_details'] = orders_with_details
        return context

class NewOrderView(LoginRequiredMixin, PageTitleMixin, TemplateView):
    template_name = 'order_app/new_order.html'
    page_title = 'Create New Order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.annotate(
            active_product_count=models.Count(
                'company_products',
                filter=models.Q(company_products__active=True)
            )
        ).filter(active_product_count__gt=0)

        # Pre-select company if specified
        company_id = self.request.GET.get('company')
        if company_id:
            context['selected_company_id'] = int(company_id)

        return context