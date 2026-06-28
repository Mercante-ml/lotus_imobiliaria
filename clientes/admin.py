from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain

@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'schema_name', 'cpf_cnpj', 'telefone', 'criado_em')
    search_fields = ('nome', 'schema_name', 'cpf_cnpj')

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    search_fields = ('domain', 'tenant__nome')
