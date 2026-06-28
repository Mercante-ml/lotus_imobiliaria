import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from clientes.models import Client
from django.db import connection
from core.models import Imovel

tenant = Client.objects.get(schema_name='alpha')
connection.set_tenant(tenant)

total = Imovel.objects.count()
with_valor = Imovel.objects.filter(valor__isnull=False).count()
without_valor = Imovel.objects.filter(valor__isnull=True).count()

print(f"Total: {total}")
print(f"With valor: {with_valor}")
print(f"Without valor: {without_valor}")
