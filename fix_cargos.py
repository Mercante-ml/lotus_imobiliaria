from django_tenants.utils import schema_context
from core.models import Corretor

for schema in ['beta', 'public', 'alpha']:
    try:
        with schema_context(schema):
            Corretor.objects.filter(cargo='gerente').update(cargo='Gerente')
            Corretor.objects.filter(cargo='diretor').update(cargo='Diretor')
            Corretor.objects.filter(cargo='corretor').update(cargo='Corretor')
    except Exception as e:
        print(f"Skipped {schema}: {e}")
