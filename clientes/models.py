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
    texto_quem_somos = models.TextField(blank=True, null=True, default="Inspirados pela flor de lótus, símbolo milenar de pureza, resiliência e renascimento, trazemos renovação e integridade a cada negociação imobiliária.")
    
    # --- TEXTOS SOBRE NÓS ---
    sobre_titulo = models.CharField(max_length=150, default="A Nossa História", blank=True, null=True)
    sobre_subtitulo = models.CharField(max_length=250, default="Descubra o propósito que nos move e a curadoria que nos define.", blank=True, null=True)
    sobre_citacao = models.TextField(default="Tal como a flor de lótus, florescemos onde poucos imaginam: entregando beleza e valor em toda a jornada dos nossos clientes.", blank=True, null=True)
    sobre_missao = models.TextField(default="Proporcionar experiências imobiliárias únicas, que transcendam a simples transação. Construímos relações sólidas baseadas em confiança, clareza e um atendimento de excelência que reflete a mesma qualidade e sofisticação dos imóveis que representamos.", blank=True, null=True)
    sobre_visao = models.TextField(default="Ser a principal referência em curadoria e atendimento personalizado no mercado imobiliário de médio e alto padrão. Aspiramos ser a primeira e única escolha para clientes exigentes que procuram não apenas um endereço, mas um verdadeiro refúgio.", blank=True, null=True)
    
    # --- TEXTOS HOME ---
    home_hero_bg_preset = models.CharField(max_length=20, default="preset_1", help_text="Preset escolhido (preset_1 a preset_4) ou 'custom'")
    home_hero_bg_custom = models.ImageField(upload_to='tenant_hero_bg/', blank=True, null=True)
    home_hero_tag = models.CharField(max_length=50, default="O Padrão de Viver", blank=True, null=True)
    home_hero_titulo = models.CharField(max_length=150, default="O Seu Espaço de", blank=True, null=True)
    home_hero_destaque = models.CharField(max_length=150, default="Renascimento.", blank=True, null=True)
    home_hero_subtitulo = models.TextField(default="Curadoria especializada para transformar a complexidade do mercado na simplicidade do extraordinário. Descubra propriedades que transcendem o comum.", blank=True, null=True)
    
    home_manifesto_titulo = models.CharField(max_length=150, default="Não vendemos imóveis.", blank=True, null=True)
    home_manifesto_destaque = models.CharField(max_length=150, default="Apresentamos novos começos.", blank=True, null=True)
    home_manifesto_texto = models.TextField(default="Nascemos com o propósito de elevar a experiência de encontrar o seu lar. Trabalhamos apenas com uma seleção criteriosa de propriedades que oferecem design imponente, conforto absoluto e exclusividade.", blank=True, null=True)
    
    # --- DADOS DA EMPRESA (RODAPÉ E CONTATO) ---
    empresa_email = models.EmailField(blank=True, null=True, help_text="E-mail público de contato")
    empresa_creci = models.CharField(max_length=20, blank=True, null=True)
    empresa_instagram = models.URLField(blank=True, null=True, help_text="Link do Instagram")
    empresa_facebook = models.URLField(blank=True, null=True, help_text="Link do Facebook")
    
    # --- SITE VISIBILITY & TEXTS ---
    exibir_equipe = models.BooleanField(default=True, help_text="Exibir seção Nossa Equipe")
    titulo_equipe = models.CharField(max_length=150, default="Nossa Equipe", blank=True, null=True)
    subtitulo_equipe = models.CharField(max_length=250, default="Especialistas dedicados a encontrar o imóvel ideal para você.", blank=True, null=True)
    
    exibir_blog = models.BooleanField(default=True, help_text="Exibir seção de Blog/Notícias")
    
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

    # --- MÓDULO FINANCEIRO (COMISSÕES PADRÃO) ---
    comissao_padrao = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, help_text="Comissão padrão da Imobiliária (ex: 5%)")
    taxa_corretor = models.DecimalField(max_digits=5, decimal_places=2, default=1.50, help_text="Taxa padrão para Corretores (%)")
    taxa_gerente = models.DecimalField(max_digits=5, decimal_places=2, default=0.30, help_text="Taxa padrão para Gerentes (%)")
    taxa_diretor = models.DecimalField(max_digits=5, decimal_places=2, default=0.20, help_text="Taxa padrão para Diretores (%)")

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
