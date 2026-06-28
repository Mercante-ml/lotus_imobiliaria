import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from clientes.models import Client
from django.db import connection
from core.models import Imovel

print("All tenants:")
for c in Client.objects.exclude(schema_name='public'):
    connection.set_tenant(c)
    print(f"  {c.schema_name} Imoveis: {Imovel.objects.count()}")
