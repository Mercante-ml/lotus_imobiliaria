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
    
    # --- ASSINATURA E COBRANÇA (STRIPE) ---
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    plano_ativo = models.CharField(
        max_length=20, 
        choices=[('boutique', 'Boutique'), ('corporate', 'Corporate')],
        default='corporate',
        help_text="Plano atual do cliente"
    )
    status_assinatura = models.CharField(max_length=30, default='active', help_text="Status no Stripe (active, past_due, canceled, etc)")
    gb_extra = models.IntegerField(default=0, help_text="Espaço extra comprado via Add-on (em GB)")

    # default true, tenant will be ready to be accessed
    auto_create_schema = True
    
    def get_gb_limit(self):
        base = 5.0 if self.plano_ativo == 'boutique' else 10.0
        return base + float(self.gb_extra)
        
    def get_gb_used(self):
        from core.models import Imovel, ImagemImovel
        total_imoveis = Imovel.objects.count()
        total_fotos = ImagemImovel.objects.count() + total_imoveis
        if total_fotos == total_imoveis and total_imoveis > 0:
            total_fotos = total_imoveis * 5 # Estimativa
        return (total_fotos * 0.5) / 1024 # em GB

    def get_gb_percentage(self):
        limit = self.get_gb_limit()
        if limit == 0: return 0
        perc = (self.get_gb_used() / limit) * 100
        return round(min(perc, 100), 1)

    def __str__(self):
        return self.nome

class Domain(DomainMixin):
    pass
