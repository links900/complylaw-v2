# reports/views.py
import os
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from weasyprint import HTML
from .models import ComplianceReport
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy
from users.models import FirmProfile
from scanner.models import ScanResult


class ReportListView(LoginRequiredMixin, ListView):
    model = ComplianceReport
    template_name = 'reports/report_list.html'   # <-- Will exist now
    context_object_name = 'reports'
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return ComplianceReport.objects.filter(
            scan__firm=self.request.user.firmprofile  # <-- use your firm profile
        ).select_related('scan').order_by('-generated_at')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if any scan exists
        context['has_scans'] = self.get_queryset().exists()
        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    model = ComplianceReport
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'

    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get_queryset(self):
        return ComplianceReport.objects.filter(scan__firm=self.request.user.firmprofile)


class ReportDownloadView(LoginRequiredMixin, View):
    
    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get(self, request, pk):
        report = get_object_or_404(ComplianceReport, pk=pk, scan__firm=request.user.firmprofile)
        if not report.pdf_file or not os.path.exists(report.pdf_file.path):
            raise Http404("PDF not generated yet.")
        return FileResponse(
            open(report.pdf_file.path, 'rb'),
            as_attachment=True,
            filename=f"ComplyNet_Report_{report.scan.domain}_{report.pk}.pdf"
        )


'''
class ReportPreviewView(LoginRequiredMixin, View):
    
    
    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get(self, request, pk):
        report = get_object_or_404(ComplianceReport, pk=pk, scan__firm=request.user.firmprofile)
        if not report.pdf_file or not os.path.exists(report.pdf_file.path):
            report.generate_pdf(request)  # Pass request for base_url
        return FileResponse(
            open(report.pdf_file.path, 'rb'),
            content_type='application/pdf'
        )
        
    def generate_pdf(self, report):
        html_string = render(request, 'reports/pdf_template.html', {
            'report': report,
            'scan': report.scan,
            'firm': report.scan.firm,
            'generated_at': timezone.now(),
        }).content.decode('utf-8')

        pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(
            stylesheets=[os.path.join('static', 'css', 'pdf-styles.css')]
        )

        # Save to model
        from django.core.files.base import ContentFile
        pdf_file = ContentFile(pdf)
        report.pdf_file.save(f"report_{report.pk}.pdf", pdf_file, save=True)
        
'''

class ReportPreviewView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        report = get_object_or_404(ComplianceReport, pk=pk, scan__firm=request.user.firmprofile)
        if not report.pdf_file or not os.path.exists(report.pdf_file.path):
            # Generate PDF on-the-fly with all computed fields
            report.generate_pdf(request)  # request needed for base_url in template

        return FileResponse(
            open(report.pdf_file.path, 'rb'),
            content_type='application/pdf'
        )
