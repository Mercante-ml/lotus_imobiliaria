import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from django.core.cache import cache
from clientes.models import Client

for c in Client.objects.all():
    val = cache.get(f'sync_{c.schema_name}')
    if val:
        print(f"Tenant {c.schema_name} cache: {val}")
