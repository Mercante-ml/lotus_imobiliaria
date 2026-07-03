import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from clientes.models import Domain

d = Domain.objects.get(domain='Sigma.imobgold.com')
d.domain = 'sigma.imobgold.com'
d.save()
print("Domain fixed successfully.")
