"""
URL configuration for lotus_imobiliaria project.
"""
from django.contrib import admin
from django.urls import path, include, reverse_lazy

# --- Importações necessárias para servir média ---
from django.conf import settings
from django.conf.urls.static import static
# ------------------------------------------------

# --- 1. IMPORTAR AS VIEWS NECESSÁRIAS ---
from core.views import custom_password_change_done
# Importa a view padrão do allauth que queremos sobrescrever
from allauth.account.views import PasswordChangeView 

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- 2. URLS DO ALLAUTH (CUSTOMIZADAS) ---
    
    # Esta é a NOSSA view customizada de "Sucesso"
    # Ela NÃO mudou e está correta.
    path(
        'accounts/password/change/done/', 
        custom_password_change_done, 
        name='account_password_change_done'
    ),

    # ESTA É A NOVA REGRA (A CORREÇÃO):
    # Nós estamos sobrescrevendo a view de "Alterar Senha" do allauth
    # e passando a NOSSA url de sucesso para ela.
    path(
        "accounts/password/change/",
        PasswordChangeView.as_view(
            template_name="account/password_change.html", # O seu template
            success_url=reverse_lazy("account_password_change_done") # A NOSSA view
        ),
        name="account_change_password",
    ),

    # O resto das URLs do allauth (login, logout, etc.)
    path('accounts/', include('allauth.urls')),
    # --- FIM DA MUDANÇA ---

    # Nossas URLs do app 'core'
    path('', include('core.urls')), 
]

# Servir arquivos de mídia em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)