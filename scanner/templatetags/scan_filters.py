# scanner/templatetags/scan_filters.py
from django import template

register = template.Library()


@register.filter
def select_gdpr(findings):
    """Return all findings related to GDPR"""
    if not findings:
        return []
    return [
        f for f in findings
        if f.get('module') == 'GDPR' or
           'GDPR' in f.get('standard', '') or
           'GDPR' in f.get('title', '') or
           'GDPR' in str(f.get('details', ''))
    ]


@register.filter
def select_owasp(findings):
    """Return all OWASP-related findings"""
    if not findings:
        return []
    return [
        f for f in findings
        if f.get('module') == 'OWASP' or
           'OWASP' in f.get('standard', '') or
           'OWASP' in f.get('title', '')
    ]


@register.filter
def select_iso(findings):
    if not findings:
        return []
    return [f for f in findings if 'ISO' in f.get('standard', '') or f.get('module') == 'ISO 27001']


@register.filter
def select_pci(findings):
    if not findings:
        return []
    return [f for f in findings if 'PCI' in f.get('standard', '') or f.get('module') == 'PCI DSS']


@register.filter
def select_hipaa(findings):
    if not findings:
        return []
    return [f for f in findings if 'HIPAA' in f.get('standard', '') or f.get('module') == 'HIPAA']


@register.filter
def has_issue(findings, keyword):
    """Check if any finding contains a keyword in title"""
    if not findings:
        return False
    return any(keyword.lower() in f.get('title', '').lower() for f in findings)