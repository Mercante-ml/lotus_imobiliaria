from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from core import stripe_views
from clientes import views as saas_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('contas/', include('allauth.urls')),
    
    # Redirecionamento após login
    path('login-redirect/', saas_views.login_redirect_view, name='login_redirect'),
    
    # Fluxo SaaS
    path('setup/', saas_views.setup_onboarding, name='saas_setup'),
    path('setup/<int:step>/', saas_views.setup_onboarding, name='saas_setup'),
    path('crm/', saas_views.crm_dashboard, name='saas_crm'),
    
    # Landing Page
    path('', core_views.saas_landing, name='saas_landing'),
    
    # Webhooks Globais (Stripe)
    path('webhooks/stripe/', stripe_views.stripe_webhook, name='stripe_webhook'),
]
