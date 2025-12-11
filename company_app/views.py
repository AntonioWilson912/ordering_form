from django import forms
from django.views.generic import ListView, DetailView, UpdateView, CreateView, View
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models, transaction
from core.mixins import LoginRequiredMixin, PageTitleMixin
from product_app.models import Product
from .models import Company
from .forms import CompanyForm, BulkProductUploadForm


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


class BulkProductUploadView(LoginRequiredMixin, PageTitleMixin, View):
    """View for bulk uploading products via CSV"""
    template_name = 'company_app/bulk_upload.html'

    def get_page_title(self):
        company = get_object_or_404(Company, pk=self.kwargs['pk'])
        return f'Bulk Upload Products - {company.name}'

    def get(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        form = BulkProductUploadForm()

        return render(request, self.template_name, {
            'company': company,
            'form': form,
            'page_title': self.get_page_title(),
        })

    def post(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        form = BulkProductUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                valid_products, errors = form.parse_csv(company)

                # If there are validation errors, show them
                if errors:
                    return render(request, self.template_name, {
                        'company': company,
                        'form': form,
                        'page_title': self.get_page_title(),
                        'csv_errors': errors,
                        'valid_count': len(valid_products),
                        'error_count': len(errors),
                    })

                # If no errors, create all products in a transaction
                with transaction.atomic():
                    created_products = []
                    for product_data in valid_products:
                        product = Product.objects.create(**product_data)
                        created_products.append(product)

                messages.success(
                    request,
                    f'Successfully imported {len(created_products)} product(s) for {company.name}.'
                )
                return redirect('companies:company_detail', pk=company.pk)

            except forms.ValidationError as e:
                # Handle form-level validation errors (headers, encoding, etc.)
                form.add_error('csv_file', e)

        return render(request, self.template_name, {
            'company': company,
            'form': form,
            'page_title': self.get_page_title(),
        })


class DownloadSampleCSVView(LoginRequiredMixin, View):
    """Download a sample CSV template"""

    def get(self, request):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="product_import_template.csv"'

        writer = csv.writer(response)
        writer.writerow(['Item No.', 'Name', 'Type'])
        writer.writerow(['SKU-001', 'Sample Product 1', 'C'])
        writer.writerow(['SKU-002', 'Sample Product 2', 'W'])
        writer.writerow(['', 'Sample Product 3 (no item no)', 'C'])

        return response