from django import forms

class CompanyForm(forms.Form):
    name = forms.CharField(label="Name:", max_length=255)