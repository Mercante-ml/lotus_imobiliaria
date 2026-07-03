import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from clientes.models import Client

clients = Client.objects.exclude(schema_name='public')
for c in clients:
    print(f"Tenant: {c.nome}")
    print(f"  Tag: {repr(c.home_hero_tag)}")
    print(f"  Titulo: {repr(c.home_hero_titulo)}")
    print(f"  Destaque: {repr(c.home_hero_destaque)}")
