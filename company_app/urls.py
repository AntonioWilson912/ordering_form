from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path('', views.CompanyListView.as_view(), name='company_list'),
    path('new/', views.CompanyCreateView.as_view(), name='company_create'),
    path('<int:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_edit'),
    path('<int:pk>/bulk-upload/', views.BulkProductUploadView.as_view(), name='bulk_upload'),
    path('download-sample-csv/', views.DownloadSampleCSVView.as_view(), name='download_sample_csv'),
]