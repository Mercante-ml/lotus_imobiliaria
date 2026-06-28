import os
import sys
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from clientes.models import Client
from django.test import RequestFactory
from core.views import api_import_status
from django.db import connection
from django.core.cache import cache
from django.contrib.auth import get_user_model
import json

tenant = Client.objects.get(schema_name='alpha')
connection.set_tenant(tenant)

cache_key = f'sync_{tenant.schema_name}'
cache.set(cache_key, {'status': 'done', 'current': 2203, 'total': 2203}, timeout=60)

User = get_user_model()
user = User.objects.first()

factory = RequestFactory()
request = factory.get('/crm/api/import-status/')
request.tenant = tenant
request.user = user
connection.set_tenant(tenant)

response = api_import_status(request)
print("Response content:", response.content.decode('utf-8'))
