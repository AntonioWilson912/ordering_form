from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.urls import reverse_lazy
from django.db import models
from core.mixins import LoginRequiredMixin, PageTitleMixin
from .models import Company
from .forms import CompanyForm


class CompanyListView(LoginRequiredMixin, PageTitleMixin, ListView):
    model = Company
    template_name = 'company_app/company_list.html'
    context_object_name = 'companies'
    page_title = 'All Companies'

    def get_queryset(self):
        return Company.objects.annotate(
            product_count=models.Count('company_products'),
            active_product_count=models.Count(
                'company_products',
                filter=models.Q(company_products__active=True)
            )
        ).order_by('name')


class CompanyDetailView(LoginRequiredMixin, PageTitleMixin, DetailView):
    model = Company
    template_name = 'company_app/company_detail.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"{self.object.name} - Details"
        context['products'] = self.object.company_products.all().order_by('item_no')
        return context


class CompanyUpdateView(LoginRequiredMixin, PageTitleMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company_app/company_form.html'

    def get_success_url(self):
        return reverse_lazy('companies:company_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Edit {self.object.name}"
        context['is_update'] = True
        return context


class CompanyCreateView(LoginRequiredMixin, PageTitleMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company_app/company_form.html'
    success_url = reverse_lazy('companies:company_list')
    page_title = 'Create New Company'