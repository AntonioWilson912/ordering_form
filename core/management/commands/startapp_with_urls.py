import os
from django.core.management.commands.startapp import Command as StartAppCommand


class Command(StartAppCommand):
    help = 'Creates a Django app with a urls.py file included'

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

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {app_name} with urls.py')
        )