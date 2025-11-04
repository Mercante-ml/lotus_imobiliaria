from django.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe

# --- Modelos de Apoio ---

class ConteudoPagina(models.Model):
    chave = models.CharField(max_length=50, unique=True, help_text="Identificador único (ex: 'pagina_corretores')")
    titulo = models.CharField(max_length=200, blank=True)
    subtitulo = models.TextField(blank=True)
    corpo = models.TextField(blank=True, help_text="Conteúdo principal da página. Pode usar tags HTML.")

    def __str__(self):
        return self.titulo or self.chave

class PaginaSobre(ConteudoPagina):
    class Meta:
        proxy = True
        verbose_name = 'Página "Sobre"'
        verbose_name_plural = 'Página "Sobre"'

class Bairro(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    def __str__(self):
        return self.nome

class TipoImovel(models.Model):
    """ Ex: Apartamento, Casa de Condomínio, Loft, Sala Comercial """
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

class Caracteristica(models.Model):
    """ Ex: Piscina, Academia, Portaria 24h """
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nome

class Corretor(models.Model):
    nome = models.CharField(max_length=80)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    creci = models.CharField(max_length=20)
    foto = models.ImageField(upload_to='fotos_corretores/', blank=True, null=True)
    bio = models.TextField(blank=True, help_text="Uma breve biografia ou citação do corretor.")

    def __str__(self):
        return self.nome

    # CORRIGIDO para admin: Renomeado de 'foto_preview' para 'get_foto_preview'
    def get_foto_preview(self):
        if self.foto:
            return mark_safe(f'<img src="{self.foto.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Sem foto"
    get_foto_preview.short_description = "Prévia"

# --- Modelo Principal (Evoluído) ---

class Imovel(models.Model):
    
    # --- Identificação e Classificação ---
    titulo = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    
    FINALIDADE_CHOICES = [
        ('lancamento', 'Lançamento'),
        ('revenda', 'Revenda')
    ]
    finalidade = models.CharField(
        max_length=20, choices=FINALIDADE_CHOICES, default='revenda',
        help_text="Deduzido do Título (ex: 'lançamento') ou 'Revenda' como padrão"
    )

    # NOVO CAMPO (Baseado na sua análise do XML)
    CATEGORIA_CHOICES = [
        ('residencial', 'Residencial'),
        ('comercial', 'Comercial'),
    ]
    categoria = models.CharField(
        max_length=20, choices=CATEGORIA_CHOICES, default='residencial',
        help_text="Baseado no <UsageType> do XML (Residencial/Comercial)"
    )

    tipo_imovel = models.ForeignKey(
        TipoImovel, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Baseado no <PropertySubType> ou <PropertyType> do XML"
    )
    
    # --- Valores (Para Filtros Min/Max) ---
    valor = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, 
        help_text="Deixe em branco se for 'Sob Consulta'"
    )
    
    # NOVO CAMPO (Baseado na sua análise do XML)
    taxa_condominio = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Baseado no <PropertyAdministrationFee> do XML"
    )
    
    # NOVO CAMPO (Baseado na sua análise do XML)
    iptu = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Baseado no <Iptu> do XML"
    )

    # --- Detalhes (Para Filtros Exatos) ---
    quartos = models.IntegerField(null=True, blank=True)
    suites = models.IntegerField(null=True, blank=True)
    banheiros = models.IntegerField(null=True, blank=True)
    vagas = models.IntegerField(null=True, blank=True)
    area_util = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    
    # NOVO CAMPO (Baseado na sua análise do XML)
    andar = models.IntegerField(
        null=True, blank=True,
        help_text="Baseado no <UnitFloor> do XML"
    )

    # --- Localização e Mídia ---
    bairro = models.ForeignKey(Bairro, on_delete=models.SET_NULL, null=True, blank=True)
    endereco = models.CharField(max_length=120, blank=True)
    imagem_principal = models.ImageField(upload_to='fotos_imoveis/', null=True, blank=True)
    
    # --- Relacionamentos ---
    caracteristicas = models.ManyToManyField(
        Caracteristica, blank=True,
        help_text="Baseado nas <Features> do XML"
    )
    corretor = models.ForeignKey(Corretor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # --- Status e Datas ---
    em_destaque = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titulo

    # CORRIGIDO para admin: Renomeado de 'imagem_preview' para 'get_imagem_preview'
    def get_imagem_preview(self):
        if self.imagem_principal:
            return mark_safe(f'<img src="{self.imagem_principal.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Sem foto"
    get_imagem_preview.short_description = "Prévia"

class ImagemImovel(models.Model):
    imovel = models.ForeignKey(Imovel, related_name='imagens_secundarias', on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to='fotos_imoveis/galeria/')

    def __str__(self):
        return f"Imagem de {self.imovel.titulo}"

    # CORRIGIDO para admin: Renomeado de 'imagem_preview' para 'get_imagem_preview'
    def get_imagem_preview(self):
        if self.imagem:
            return mark_safe(f'<img src="{self.imagem.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Sem foto"
    get_imagem_preview.short_description = "Prévia"

class Lead(models.Model):
    nome = models.CharField(max_length=80)
    email = models.EmailField()
    telefone = models.CharField(max_length=20, blank=True)
    mensagem = models.TextField()
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead de {self.nome} em {self.data.strftime('%d/%m/%Y')}"

