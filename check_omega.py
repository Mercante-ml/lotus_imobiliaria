from django_tenants.utils import schema_context
from core.models import Corretor

for schema in ['beta', 'omega']:
    try:
        with schema_context(schema):
            print(f"--- Schema {schema} ---")
            for c in Corretor.objects.all():
                print(f"Nome: {c.nome}, Cargo: {c.cargo}")
    except Exception as e:
        pass
