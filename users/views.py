# users/views.py — FINAL & CLEAN
from django.views.generic import TemplateView, UpdateView, CreateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from .models import FirmProfile, UserAccount
from .forms import FirmProfileForm


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firm'] = self.request.user.firm  # ← ForeignKey
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = UserAccount
    fields = ['first_name', 'last_name']
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)


class FirmSettingsView(LoginRequiredMixin, UpdateView):
    model = FirmProfile
    form_class = FirmProfileForm
    template_name = 'users/firm_settings.html'
    success_url = reverse_lazy('users:firm_settings')
    
    def dispatch(self, request, *args, **kwargs):
        """Check for FirmProfile before rendering form."""
        try:
            request.user.firmprofile
        except FirmProfile.DoesNotExist:
            # Only show message if coming from /firm/
            if request.path == reverse_lazy('users:firm_settings'):
                messages.warning(request, "Please set up your firm first.")
            return redirect("users:firm_wizard")
        return super().dispatch(request, *args, **kwargs)
    
    
    def get_object(self, queryset=None):
        return self.request.user.firmprofile    # ← OneToOneField via related_name
        
        
    
    
    def form_valid(self, form):
        messages.success(self.request, "Firm settings saved.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


class SignupWizardView(FormView):
    template_name = 'users/signup.html'
    success_url = reverse_lazy('dashboard:home')

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return redirect('account_signup')


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        if not request.user.firm:
            return redirect('users:firm_wizard')
        return redirect('dashboard:home')


class FirmSetupWizardView(LoginRequiredMixin, CreateView):
    model = FirmProfile
    form_class = FirmProfileForm
    template_name = 'users/firm_wizard.html'
    success_url = reverse_lazy('dashboard:home')

    def get(self, request, *args, **kwargs):
        # Clear any stale warnings
        storage = messages.get_messages(request)
        storage.used = True
        return super().get(request, *args, **kwargs)
        
    def form_valid(self, form):
        firm = form.save(commit=False)
        firm.user = self.request.user  # ← SET OneToOne user
        firm.save()

        self.request.user.firm = firm  # ← SET ForeignKey
        self.request.user.save()

        messages.success(self.request, f"Welcome to {firm.firm_name}! Your firm is ready.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_wizard'] = True
        return context
        

from django.views.generic import TemplateView
from django.contrib.messages.views import SuccessMessageMixin

class EmailConfirmationSentView(SuccessMessageMixin, TemplateView):
    template_name = "account/email_confirmation_sent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Try to get email from session (set during signup)
        context["email"] = self.request.session.get("account_verified_email") or "your inbox"
        return context
        
        
from allauth.account.views import SignupView
from django.contrib import messages
from django.shortcuts import render

class CustomSignupView(SignupView):
    def form_valid(self, form):
        # Let allauth do the normal signup + send email
        response = super().form_valid(form)
        
        # Show beautiful success message on the SAME page
        messages.success(
            self.request,
            "Check your inbox! We sent a confirmation link to your email. "
            "Click it to activate your account."
        )
        
        # Stay on the same page (don't redirect)
        return render(self.request, "account/signup.html", self.get_context_data(form=form))
        
        
####################
## DELETE IN PRODUCTION

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.conf import settings

def create_admin_user(request):
    # Only allow this on DEBUG or from a secret key (optional)
    if not settings.DEBUG:
        return HttpResponse("Not allowed.", status=403)

    User = get_user_model()
    username = "admin"
    email = "complylaw@alhambra-solutions.com"
    password = "1234abcd@dmin"  # CHANGE this to a strong password

    if User.objects.filter(username=username).exists():
        return HttpResponse("Admin user already exists.")

    User.objects.create_superuser(username=username, email=email, password=password)
    return HttpResponse(f"Superuser '{username}' created successfully!")