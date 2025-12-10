# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='report_list'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('<int:pk>/download/', views.ReportDownloadView.as_view(), name='report_download'),
    path('<int:pk>/preview/', views.ReportPreviewView.as_view(), name='report_preview'),
    
]