import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from django.test import Client
from clientes.models import Client as TenantClient
from django.db import connection

tenant = TenantClient.objects.get(schema_name='alpha')
connection.set_tenant(tenant)

client = Client(SERVER_NAME='alpha-imob.dsprime.org')

response = client.get('/imoveis/')
content = response.content.decode('utf-8')

print("Status Code:", response.status_code)
# Check if "0 Imóveis" is in the HTML
if "0 imóveis encontrados" in content.lower() or "0 imoveis" in content.lower() or "não encontramos nenhum imóvel" in content.lower() or "nao encontramos" in content.lower():
    print("PAGE SAYS 0 IMOVEIS")
else:
    print("PAGE HAS IMOVEIS")
    
# Count how many times 'imovel-card' appears
print("Imovel cards:", content.count('imovel-card'))
