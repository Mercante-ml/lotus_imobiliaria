"""
URL configuration for lotus_imobiliaria project.
"""
from django.contrib import admin
from django.urls import path, include

# --- Importações necessárias para servir média ---
from django.conf import settings
from django.conf.urls.static import static
# ------------------------------------------------

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # Inclui as URLs do seu app 'core'
]

# --- ADIÇÃO IMPORTANTE ---
# Isto diz ao Django para servir ficheiros da pasta /mediafiles/ em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
