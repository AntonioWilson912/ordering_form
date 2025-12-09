from django import forms
from .models import Product
from core.constants import ITEM_TYPE_CHOICES

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['company', 'name', 'item_no', 'item_type', 'active']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'item_no': forms.TextInput(attrs={'class': 'form-control'}),
            'item_type': forms.Select(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_item_no(self):
        item_no = self.cleaned_data.get('item_no')
        company = self.cleaned_data.get('company')

        if item_no and company:
            existing = Product.objects.filter(
                company=company,
                item_no=item_no
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError(
                    "This item number already exists for the selected company."
                )

        return item_no

class NewProductForm(forms.Form):
    """Form for AJAX product creation"""
    name = forms.CharField(
        label="Name:",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter the product's name..."
        })
    )
    item_no = forms.CharField(
        label="Item No (optional):",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter the vendor number..."
        })
    )
    item_type = forms.ChoiceField(
        label="Item Type:",
        choices=ITEM_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"})
    )