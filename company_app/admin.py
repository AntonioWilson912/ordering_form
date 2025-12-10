from django.contrib import admin
from .models import *


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    pass
