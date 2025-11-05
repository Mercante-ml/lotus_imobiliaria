"""
URL configuration for lotus_imobiliaria project.
"""
from django.contrib import admin
from django.urls import path, include

# --- Importações necessárias para servir média ---
from django.conf import settings
from django.conf.urls.static import static
# ------------------------------------------------

# --- 1. IMPORTAR A NOVA VIEW ---
from core.views import custom_password_change_done

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- 2. URLS DO ALLAUTH (CUSTOMIZADAS) ---
    # Nossa URL de "sucesso" personalizada vem ANTES.
    # Ela "rouba" a rota 'accounts/password/change/done/' do allauth.
    path(
        'accounts/password/change/done/', 
        custom_password_change_done, 
        name='account_password_change_done' # O 'name' TEM que ser este
    ),

    # O resto das URLs do allauth vem DEPOIS.
    path('accounts/', include('allauth.urls')),
    # --- FIM DA MUDANÇA ---

    # Nossas URLs do app 'core'
    path('', include('core.urls')), 
]

# Servir arquivos de mídia em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)