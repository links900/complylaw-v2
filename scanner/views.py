# scanner/views.py
from django.views.generic import ListView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django_htmx.http import HttpResponseLocation, HttpResponseClientRefresh
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from celery import current_app
import json
import uuid
import re
import io
from weasyprint import HTML
from django.core.files.base import ContentFile

from .models import ScanResult
from .tasks import run_compliance_scan
from reports.models import ComplianceReport



def keep_alive(request):
    return HttpResponse("OK")  # Call this every 10min via cron or external ping
    
    

# === DASHBOARD ===
class ScanDashboardView(LoginRequiredMixin, ListView):
    model = ScanResult
    template_name = 'scanner/dashboard.html'
    context_object_name = 'scans'
    
    def get_queryset(self):
        return ScanResult.objects.filter(
            #firm=self.request.user.firmprofile
            firm=self.request.user.firm
        ).select_related('firm').order_by('-scan_date')


# === SCAN LIST ===
class ScanListView(LoginRequiredMixin, ListView):
    model = ScanResult
    template_name = 'scanner/scan_list.html'
    context_object_name = 'scans'
    paginate_by = 10
    

    def get_queryset(self):
        return ScanResult.objects.filter(firm=self.request.user.firm).order_by('-scan_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['total_scans'] = qs.count()
        context['latest_grade'] = qs.first().grade if qs.exists() else None
        return context


# === RUN SCAN MODAL (HTMX) ===
class RunScanModalView(LoginRequiredMixin, TemplateView):
    template_name = 'scanner/partials/run_scan_modal.html'

    def get(self, request, *args, **kwargs):
        if request.htmx:
            return super().get(request, *args, **kwargs)
        return redirect('scanner:scan_list')


# === START SCAN (WITH RATE LIMIT) ===
@method_decorator(ratelimit(key='user', rate='2/h', method='POST', block=True), name='dispatch')
class StartScanView(LoginRequiredMixin, View):
    
    def post(self, request):
        
        domain = request.POST.get('domain', '').strip().lower()
        if not domain:
            messages.error(request, "Please enter a domain.")
            return redirect('scanner:run_scan')

        if not re.match(r'^[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$', domain):
            messages.error(request, "Invalid domain format.")
            return redirect('scanner:run_scan')

        if ScanResult.objects.filter(
            firm=request.user.firm,
            domain=domain,
            status__in=['PENDING', 'RUNNING']
        ).exists():
            messages.warning(request, f"A scan for {domain} is already in progress.")
            return redirect('scanner:dashboard')
        
        scan = ScanResult.objects.create(
            firm=request.user.firm,
            domain=domain,
            status='PENDING',
            scan_id=str(uuid.uuid4())[:8]
        )
        #print(scan.id)
        #print(scan.status)

        
        run_compliance_scan.delay(scan.pk)
        #messages.success(request, f"Scan started for <strong>{domain}</strong>.")
        messages.success(request, f"Scan started for {domain}", extra_tags="scan_started")
        
        if request.htmx:
            #print("here in htmx")
            return HttpResponseLocation(reverse('scanner:scan_status', args=[scan.id]))
        #print("here after htmx check")
        return redirect('scanner:dashboard')


# === SCAN STATUS (Real-Time via HTMX) ===
class ScanStatusView(LoginRequiredMixin, DetailView):
    model = ScanResult
    template_name = 'scanner/scan_status.html'
    context_object_name = 'scan'
    #print("1>>>>")
    #print(model.id)
    #print(model)

    def get_queryset(self):
        return ScanResult.objects.filter(firm=self.request.user.firm)
        
    


# === HTMX PARTIAL: Progress Update ===
def scan_status_partial(request, pk):
    scan = get_object_or_404(ScanResult, pk=pk, firm=request.user.firm)
    #print("2>>>>")
    #print(scan.id)
    #print(scan)
    #return render(request, 'scanner/partials/scan_progress.html', {'scan': scan})
    
    
    html = render_to_string('scanner/partials/scan_progress.html', {'scan': scan})
    
    if scan.status == 'COMPLETED':
        html += '<script>htmx.remove(htmx.find("#scan-progress"))</script>'
        messages.success(request, f"Scan completed. ", extra_tags="scan_complete")
        
    
    return HttpResponse(html)


# === CANCEL SCAN ===
class CancelScanView(LoginRequiredMixin, View):
    def post(self, request, pk):
        scan = get_object_or_404(ScanResult, pk=pk, firm=request.user.firm)
        if scan.status in ['PENDING', 'RUNNING']:
            scan.status = 'CANCELLED'
            scan.scan_log += '\n[Cancelled by user]'
            scan.save()
        return HttpResponseClientRefresh()


# === RETRY SCAN ===
class RetryScanView(LoginRequiredMixin, View):
    def post(self, request, pk):
        old_scan = get_object_or_404(ScanResult, pk=pk, firm=request.user.firm)
        if old_scan.status != 'FAILED':
            return JsonResponse({'error': 'Only FAILED scans can be retried'}, status=400)

        new_scan = ScanResult.objects.create(
            firm=old_scan.firm,
            domain=old_scan.domain,
            status='PENDING',
            scan_id=str(uuid.uuid4())[:8],
            scan_log='Retrying FAILED scan...'
        )
        run_compliance_scan.delay(new_scan.id)
        return HttpResponseLocation(reverse('scanner:scan_status', args=[new_scan.id]))


# === GENERATE PDF (WeasyPrint) ===ScanListView
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML
import io

def generate_pdf(request, pk):
    scan = get_object_or_404(ScanResult, id=pk, firm=request.user.firm)

    # === Extract findings ===
    raw_findings = scan.get_findings() or []
    
    findings_list = []

    for f in raw_findings:

        # If f is a plain string (older scans), convert it to dict
        if isinstance(f, str):
            findings_list.append({
                'standard': '—',
                'title': f,
                'risk_level': '—',
                'details': f,
                'module': 'General'
            })
            continue

        # If f is not even a dict, skip
        if not isinstance(f, dict):
            continue

        # Normal structured finding
        findings_list.append({
            'standard': f.get('standard') or '—',
            'title': f.get('title') or '—',
            'risk_level': f.get('risk_level') or '—',
            'details': f.get('details') or '—',
            'module': f.get('module') or 'General'
        })

    context = {
        'scan': scan,
        'findings': findings_list,
        'recommendations': scan.get_recommendations() if hasattr(scan, 'get_recommendations') else [],
    }

    # Render template
    html_string = render_to_string('reports/pdf_template.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))

    pdf_file = io.BytesIO()
    html.write_pdf(pdf_file)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Compliance_Report_{scan.domain}_{scan.scan_id}.pdf"'
    response.write(pdf_file.getvalue())
    pdf_file.close()

    return response

    
    
    

from django.http import HttpResponse

def rate_limit_exceeded_view(request, exception=None):
    return HttpResponse(
        "You have exceeded the request limit. Please try again later.",
        status=429
    )