import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from django.contrib.auth.models import User
from clientes.models import Client
from core.models import Corretor
from django_tenants.utils import tenant_context

user = User.objects.filter(email='contato.dsprime@gmail.com').first()
if not user:
    user = User.objects.first()

print(f"Assigning user {user.email} as Diretor for all tenants...")

for tenant in Client.objects.exclude(schema_name='public'):
    with tenant_context(tenant):
        if not Corretor.objects.filter(user=user).exists():
            Corretor.objects.create(
                user=user,
                nome=user.first_name or user.username or "Diretor",
                email=user.email,
                telefone="11999999999",
                cargo='Diretor',
                exibir_no_site=True,
                comissao_venda_direta=100.0,
                comissao_equipe=0.0
            )
            print(f"Created Diretor for {tenant.nome}")
        else:
            print(f"Diretor already exists for {tenant.nome}")
