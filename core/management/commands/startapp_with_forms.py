import os
from django.core.management.commands.startapp import Command as StartAppCommand


class Command(StartAppCommand):
    help = 'Creates a Django app with urls.py and forms.py files included'

    def handle(self, *args, **options):
        # First, run the standard startapp command
        super().handle(*args, **options)

        # Get the app name and directory
        app_name = options['name']
        target = options.get('directory')

        if target is None:
            app_dir = app_name
        else:
            app_dir = os.path.join(target, app_name)

        # Create urls.py
        urls_path = os.path.join(app_dir, 'urls.py')
        urls_content = f'''from django.urls import path
from . import views

app_name = "{app_name}"

urlpatterns = [
    # Add your URL patterns here
    # Example:
    # path('', views.index, name='index'),
]
'''

        with open(urls_path, 'w') as f:
            f.write(urls_content)

        # Create forms.py
        forms_path = os.path.join(app_dir, 'forms.py')
        forms_content = f'''from django import forms
# from .models import YourModel


# Example ModelForm:
# class YourModelForm(forms.ModelForm):
#     class Meta:
#         model = YourModel
#         fields = ['field1', 'field2']
#         widgets = {{
#             'field1': forms.TextInput(attrs={{'class': 'form-control'}}),
#             'field2': forms.Textarea(attrs={{'class': 'form-control', 'rows': 4}}),
#         }}


# Example regular Form:
# class YourForm(forms.Form):
#     field1 = forms.CharField(
#         max_length=100,
#         widget=forms.TextInput(attrs={{'class': 'form-control'}})
#     )
#     field2 = forms.EmailField(
#         widget=forms.EmailInput(attrs={{'class': 'form-control'}})
#     )
'''

        with open(forms_path, 'w') as f:
            f.write(forms_content)

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {app_name} with urls.py and forms.py')
        )