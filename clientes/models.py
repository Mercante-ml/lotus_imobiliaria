from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    nome = models.CharField(max_length=100)
    criado_em = models.DateField(auto_now_add=True)
    
    # --- DADOS ONBOARDING ---
    tipo_documento = models.CharField(max_length=4, choices=[('CPF', 'CPF'), ('CNPJ', 'CNPJ')], default='CNPJ')
    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    
    # --- ENDEREÇO ---
    cep = models.CharField(max_length=10, blank=True, null=True)
    rua = models.CharField(max_length=150, blank=True, null=True)
    numero = models.CharField(max_length=20, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    
    # --- BRANDING ---
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)
    cor_primaria = models.CharField(max_length=7, default='#C6A87C') # Dourado Padrão
    texto_quem_somos = models.TextField(blank=True, null=True)
    
    # --- PORTFÓLIO ---
    portfolio_lancamento = models.BooleanField(default=True)
    portfolio_revenda = models.BooleanField(default=True)
    portfolio_aluguel = models.BooleanField(default=False)

    # default true, tenant will be ready to be accessed
    auto_create_schema = True

    def __str__(self):
        return self.nome

class Domain(DomainMixin):
    pass
