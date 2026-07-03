import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from clientes.models import Client, Domain

for d in Domain.objects.all():
    print(f"Domain: {d.domain} -> Tenant: {d.tenant.schema_name}")
