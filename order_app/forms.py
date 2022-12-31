from django import forms
# from company_app.models import Company
from .item_types import *

class NewProductForm(forms.Form):
    # company = forms.ChoiceField(choices=Company.objects.all)
    name = forms.CharField(label="Name:", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter the product's name..."}))
    item_no = forms.CharField(label="Item No (optional):", required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter the vendor number..."}))
    item_type = forms.ChoiceField(label="Item Type:", choices=ITEM_TYPES, widget=forms.Select(attrs={"class": "form-control"}))