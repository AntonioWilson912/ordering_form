from django import forms
from .models import Order, ProductOrder, EmailDraft


class OrderForm(forms.ModelForm):
    """Form for creating/editing orders (used in admin or future features)"""

    class Meta:
        model = Order
        fields = ['creator']
        widgets = {
            'creator': forms.Select(attrs={'class': 'form-control'}),
        }


class ProductOrderForm(forms.ModelForm):
    """Form for individual order line items"""

    class Meta:
        model = ProductOrder
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control quantity-input',
                'min': '0'
            }),
        }


class ProductOrderFormSet(forms.BaseInlineFormSet):
    """Custom formset for product orders"""

    def clean(self):
        """Validate that at least one product has quantity > 0"""
        super().clean()

        if any(self.errors):
            return

        has_items = False
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                quantity = form.cleaned_data.get('quantity', 0)
                if quantity > 0:
                    has_items = True
                    break

        if not has_items:
            raise forms.ValidationError(
                "Order must have at least one product with quantity greater than 0."
            )


# Create the inline formset
ProductOrderInlineFormSet = forms.inlineformset_factory(
    Order,
    ProductOrder,
    form=ProductOrderForm,
    formset=ProductOrderFormSet,
    extra=0,
    can_delete=True
)


class EmailDraftForm(forms.ModelForm):
    """Form for email drafts"""

    class Meta:
        model = EmailDraft
        fields = ['to_email', 'subject', 'content']
        widgets = {
            'to_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'recipient@example.com'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Order Request'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Email content...'
            }),
        }
        labels = {
            'to_email': 'To',
            'subject': 'Subject',
            'content': 'Message',
        }


class OrderFilterForm(forms.Form):
    """Form for filtering orders in the list view"""

    SORT_CHOICES = [
        ('-date', 'Newest First'),
        ('date', 'Oldest First'),
        ('-id', 'Order # (Descending)'),
        ('id', 'Order # (Ascending)'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search orders...'
        })
    )
    company = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-date',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        companies = kwargs.pop('companies', [])
        super().__init__(*args, **kwargs)

        # Build company choices
        company_choices = [('', 'All Companies')]
        company_choices.extend([(c.id, c.name) for c in companies])
        self.fields['company'].choices = company_choices