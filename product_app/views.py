from django.views.generic import ListView, DetailView, UpdateView, CreateView, FormView
from django.urls import reverse_lazy
from core.mixins import LoginRequiredMixin, PageTitleMixin
from company_app.models import Company
from .models import Product
from .forms import ProductForm, NewProductForm


class ProductListView(LoginRequiredMixin, PageTitleMixin, ListView):
    model = Product
    template_name = "product_app/product_list.html"
    context_object_name = "products"
    paginate_by = 50
    page_title = "All Products"

    def get_queryset(self):
        queryset = Product.objects.select_related("company").order_by(
            "company__name", "item_no"
        )

        company_id = self.request.GET.get("company")
        if company_id:
            queryset = queryset.filter(company_id=company_id)

        return queryset


class ProductDetailView(LoginRequiredMixin, PageTitleMixin, DetailView):
    model = Product
    template_name = "product_app/product_detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"{self.object.name} - Details"
        return context


class ProductUpdateView(LoginRequiredMixin, PageTitleMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "product_app/product_form.html"

    def get_success_url(self):
        return reverse_lazy("products:product_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["is_update"] = True
        return context


class ProductCreateView(LoginRequiredMixin, PageTitleMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "product_app/product_form.html"
    success_url = reverse_lazy("products:product_list")
    page_title = "Create New Product"

    def get_initial(self):
        initial = super().get_initial()
        company_id = self.request.GET.get("company")
        if company_id:
            initial["company"] = company_id
        return initial


class NewProductView(LoginRequiredMixin, PageTitleMixin, FormView):
    """AJAX-based product creation view"""

    template_name = "product_app/new_product_ajax.html"
    form_class = NewProductForm
    page_title = "Create New Product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["companies"] = Company.objects.all().order_by("name")

        # Pre-select company if specified
        company_id = self.request.GET.get("company")
        if company_id:
            context["selected_company_id"] = int(company_id)

        return context
