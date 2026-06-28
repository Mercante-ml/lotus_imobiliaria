import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from clientes.models import Client
from django.db import connection
from core.models import Bairro, TipoImovel, Imovel

tenant = Client.objects.get(schema_name='alpha')
connection.set_tenant(tenant)

print(f"Bairros: {Bairro.objects.count()}")
print(f"TipoImovel: {TipoImovel.objects.count()}")
print(f"Imoveis com bairro: {Imovel.objects.filter(bairro__isnull=False).count()}")
