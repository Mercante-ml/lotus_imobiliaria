from clientes.models import Client, Domain

# 1. Create Public Tenant
public_tenant = Client(schema_name='public', nome='ImobGold Plataforma')
public_tenant.save()

# Add domain to public
domain = Domain(domain='imob.dsprime.org', tenant=public_tenant, is_primary=True)
domain.save()

# 2. Create first real tenant (Lotus Imobiliaria)
lotus_tenant = Client(schema_name='lotus', nome='Lotus Imobiliária')
lotus_tenant.save()

# Add domain to lotus
lotus_domain = Domain(domain='lotus.imob.dsprime.org', tenant=lotus_tenant, is_primary=True)
lotus_domain.save()

print("Tenants criados com sucesso!")

print("Tenants criados com sucesso!")
