from django import forms
from company_app.models import Company

class NewProductForm(forms.Form):
    company = forms.ChoiceField(choices=Company.objects.all)