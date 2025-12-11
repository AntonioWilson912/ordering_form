import os
from django.core.management.commands.startapp import Command as StartAppCommand


class Command(StartAppCommand):
    help = 'Creates a Django app with urls.py, forms.py, and serializers.py files included'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            '--with-api',
            action='store_true',
            dest='with_api',
            help='Include serializers.py for Django REST Framework',
        )
        parser.add_argument(
            '--with-signals',
            action='store_true',
            dest='with_signals',
            help='Include signals.py and configure apps.py',
        )

    def handle(self, *args, **options):
        # First, run the standard startapp command
        super().handle(*args, **options)

        # Get the app name and directory
        app_name = options['name']
        target = options.get('directory')
        with_api = options.get('with_api', False)
        with_signals = options.get('with_signals', False)

        if target is None:
            app_dir = app_name
        else:
            app_dir = os.path.join(target, app_name)

        # Create urls.py
        self._create_urls(app_dir, app_name)

        # Create forms.py
        self._create_forms(app_dir, app_name)

        # Optionally create serializers.py
        if with_api:
            self._create_serializers(app_dir, app_name)

        # Optionally create signals.py and update apps.py
        if with_signals:
            self._create_signals(app_dir, app_name)
            self._update_apps_for_signals(app_dir, app_name)

        created_files = ['urls.py', 'forms.py']
        if with_api:
            created_files.append('serializers.py')
        if with_signals:
            created_files.append('signals.py')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {app_name} with: {", ".join(created_files)}'
            )
        )

    def _create_urls(self, app_dir, app_name):
        urls_path = os.path.join(app_dir, 'urls.py')
        urls_content = f'''from django.urls import path
from . import views

app_name = "{app_name}"

urlpatterns = [
    # Add your URL patterns here
    # Example:
    # path('', views.IndexView.as_view(), name='index'),
    # path('<int:pk>/', views.DetailView.as_view(), name='detail'),
]
'''
        with open(urls_path, 'w') as f:
            f.write(urls_content)

    def _create_forms(self, app_dir, app_name):
        forms_path = os.path.join(app_dir, 'forms.py')
        forms_content = '''from django import forms
# from .models import YourModel


# Example ModelForm:
# class YourModelForm(forms.ModelForm):
#     class Meta:
#         model = YourModel
#         fields = ['field1', 'field2']
#         widgets = {
#             'field1': forms.TextInput(attrs={'class': 'form-control'}),
#             'field2': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
#         }
'''
        with open(forms_path, 'w') as f:
            f.write(forms_content)

    def _create_serializers(self, app_dir, app_name):
        serializers_path = os.path.join(app_dir, 'serializers.py')
        serializers_content = '''from rest_framework import serializers
# from .models import YourModel


# Example ModelSerializer:
# class YourModelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = YourModel
#         fields = ['id', 'field1', 'field2', 'created_at']
#         read_only_fields = ['id', 'created_at']


# Example regular Serializer:
# class YourSerializer(serializers.Serializer):
#     field1 = serializers.CharField(max_length=100)
#     field2 = serializers.EmailField()
#
#     def validate_field1(self, value):
#         if len(value) < 3:
#             raise serializers.ValidationError("Field1 must be at least 3 characters.")
#         return value
'''
        with open(serializers_path, 'w') as f:
            f.write(serializers_content)

    def _create_signals(self, app_dir, app_name):
        signals_path = os.path.join(app_dir, 'signals.py')
        signals_content = '''from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
# from .models import YourModel


# Example post_save signal:
# @receiver(post_save, sender=YourModel)
# def your_model_post_save(sender, instance, created, **kwargs):
#     if created:
#         # Handle new instance creation
#         pass
#     else:
#         # Handle instance update
#         pass


# Example pre_save signal:
# @receiver(pre_save, sender=YourModel)
# def your_model_pre_save(sender, instance, **kwargs):
#     # Modify instance before saving
#     pass


# Example post_delete signal:
# @receiver(post_delete, sender=YourModel)
# def your_model_post_delete(sender, instance, **kwargs):
#     # Clean up after deletion
#     pass
'''
        with open(signals_path, 'w') as f:
            f.write(signals_content)

    def _update_apps_for_signals(self, app_dir, app_name):
        apps_path = os.path.join(app_dir, 'apps.py')

        # Convert app_name to CamelCase for class name
        class_name = ''.join(word.capitalize() for word in app_name.split('_')) + 'Config'

        apps_content = f'''from django.apps import AppConfig


class {class_name}(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app_name}'

    def ready(self):
        # Import signals to register them
        from . import signals  # noqa: F401
'''
        with open(apps_path, 'w') as f:
            f.write(apps_content)