from django.db import models
from django.utils.text import slugify
from django.utils.html import mark_safe
from django.core.validators import RegexValidator

# Importações para o Perfil de Usuário e o "Sinal"
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

# Pega o modelo de User padrão do Django
User = get_user_model()


# --- Modelos de Apoio (Conteúdo, Bairro, etc.) ---

class ConteudoPagina(models.Model):
    chave = models.CharField(max_length=50, unique=True, help_text="Identificador único (ex: 'pagina_corretores')")
    titulo = models.CharField(max_length=200, blank=True)
    subtitulo = models.TextField(blank=True)

    def __str__(self):
        return self.titulo or self.chave

class Bairro(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    def __str__(self):
        return self.nome

class TipoImovel(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

class Caracteristica(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nome

class Corretor(models.Model):
    nome = models.CharField(max_length=80)
    email = models.EmailField(blank=True, null=True)
    
    telefone_validator = RegexValidator(
        regex=r'^\(\d{2}\) 9\d{4}-\d{4}$',  
        message='O telefone deve estar no formato (DD) 9XXXX-XXXX'
    )
    telefone = models.CharField(max_length=20, blank=True, null=True, validators=[telefone_validator], help_text="Formato: (62) 99999-9999")
    
    # Validador do CRECI (que corrigimos)
    creci_validator = RegexValidator(
        regex=r'^\d+$',  
        message='O CRECI deve conter apenas números.'
    )    
    creci = models.CharField(
        max_length=20, 
        validators=[creci_validator]
    )
    
    foto = models.ImageField(upload_to='fotos_corretores/', blank=True, null=True)
    bio = models.TextField(blank=True, help_text="Uma breve biografia ou citação do corretor.")

    def __str__(self):
        return self.nome

    @property
    def whatsapp_numero(self):
        if not self.telefone:
            return ""
        import re
        return re.sub(r'\D', '', self.telefone)

    def get_foto_preview(self):
        if self.foto:
            return mark_safe(f'<img src="{self.foto.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Sem foto"
    get_foto_preview.short_description = "Prévia"


# --- Modelo Principal (Imovel) ---
# (Este modelo precisa estar DEFINIDO ANTES do Profile, que o usa)

class Imovel(models.Model):
    
    # --- Identificação e Classificação ---
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True)
    FINALIDADE_CHOICES = [('lancamento', 'Lançamento'), ('revenda', 'Revenda')]
    finalidade = models.CharField(max_length=20, choices=FINALIDADE_CHOICES, default='revenda', help_text="Deduzido do Título (ex: 'lançamento') ou 'Revenda' como padrão")
    CATEGORIA_CHOICES = [('residencial', 'Residencial'), ('comercial', 'Comercial'),]
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='residencial', help_text="Baseado no <UsageType> do XML (Residencial/Comercial)")
    tipo_imovel = models.ForeignKey(TipoImovel, on_delete=models.SET_NULL, null=True, blank=True, help_text="Baseado no <PropertySubType> ou <PropertyType> do XML")
    
    # --- Valores (Para Filtros Min/Max) ---
    valor = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Deixe em branco se for 'Sob Consulta'")
    taxa_condominio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Baseado no <PropertyAdministrationFee> do XML")
    iptu = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Baseado no <Iptu> do XML")

    # --- Detalhes (Para Filtros Exatos) ---
    quartos = models.IntegerField(null=True, blank=True)
    suites = models.IntegerField(null=True, blank=True)
    banheiros = models.IntegerField(null=True, blank=True)
    vagas = models.IntegerField(null=True, blank=True)
    area_util = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    andar = models.IntegerField(null=True, blank=True, help_text="Baseado no <UnitFloor> do XML")

    # --- Localização e Mídia ---
    bairro = models.ForeignKey(Bairro, on_delete=models.SET_NULL, null=True, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)
    imagem_principal = models.ImageField(upload_to='fotos_imoveis/', null=True, blank=True)
    
    # --- Relacionamentos ---
    caracteristicas = models.ManyToManyField(Caracteristica, blank=True, help_text="Baseado nas <Features> do XML")
    corretor = models.ForeignKey(Corretor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # --- Status e Datas ---
    em_destaque = models.BooleanField(default=False)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titulo

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

    def get_imagem_preview(self):
        if self.imagem:
            return mark_safe(f'<img src="{self.imagem.url}" style="max-height: 100px; max-width: 100px;" />')
        return "Sem foto"
    get_imagem_preview.short_description = "Prévia"

class Lead(models.Model):
    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('atendimento', 'Em Atendimento'),
        ('visita', 'Visita Agendada'),
        ('proposta', 'Proposta / Negociação'),
        ('fechado', 'Fechamento'),
        ('standby', 'Standby'),
        ('arquivado', 'Arquivado'),
        ('lixeira', 'Lixeira'),
    ]
    
    nome = models.CharField(max_length=80)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    mensagem = models.TextField(blank=True, null=True)
    
    # Novos campos para o Kanban CRM
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='novo')
    imovel = models.ForeignKey(Imovel, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    corretor = models.ForeignKey(Corretor, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead de {self.nome} em {self.data_criacao.strftime('%d/%m/%Y')}"


# --- Modelo de Perfil de Usuário (ATUALIZADO) ---
class Profile(models.Model):
    # Usamos DO_NOTHING para evitar que o Django tente deletar o profile (que é Tenant-specific)
    # quando um User (Shared) for deletado do schema public, causando erro de tabela inexistente.
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    
    # --- CAMPO ADICIONADO AQUI ---
    # É aqui que vamos salvar os imóveis favoritos do usuário logado
    favoritos = models.ManyToManyField(Imovel, blank=True, related_name="favoritado_por")
    # --- FIM DA ADIÇÃO ---

    def __str__(self):
        return self.user.email # Usa o email do usuário como nome

# --- "Sinal" para criar o Profile automaticamente ---
# (Roda sempre que um novo 'User' é criado)
from django.db import connection

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if connection.schema_name == 'public':
        return
    if created:
        Profile.objects.create(user=instance)
    
    # Esta verificação garante que o perfil exista antes de salvar
    # (Resolve o bug do superuser que você teve)
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

# --- MODELO DO BLOG ---

class PostBlog(models.Model):
    TIPO_CONTEUDO_CHOICES = [
        ('link', 'Link Externo (Artigo, PDF, Notícia)'),
        ('embed', 'Conteúdo Incorporado (Vídeo, Gamma, Facebook)'),
    ]    
    titulo = models.CharField(max_length=200)
    resumo = models.TextField(help_text="Um parágrafo curto sobre o conteúdo.")
    imagem_card = models.ImageField(upload_to='blog_cards/', help_text="Imagem de capa que aparecerá no card do site.")
    
    tipo_conteudo = models.CharField(max_length=10, choices=TIPO_CONTEUDO_CHOICES, default='link')
    
    link_url = models.URLField(max_length=500, blank=True, null=True, 
                               help_text="Se 'Tipo' for Link Externo, cole a URL completa aqui.")
    
    embed_code = models.TextField(blank=True, null=True, 
                                  help_text="Se 'Tipo' for Conteúdo Incorporado, cole o código HTML (iframe, etc.) aqui.")
    
    data_publicacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_publicacao'] # Mais novos primeiro
        verbose_name = "Post do Blog"
        verbose_name_plural = "Posts do Blog"

    def __str__(self):
        return self.titulo

class AlertaBusca(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='alertas', null=True, blank=True)
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    
    # A query original em formato querystring (urlencode)
    query_string = models.TextField(blank=True, help_text="Parâmetros da busca salvos")
    
    # Resumo para exibir no admin
    resumo_busca = models.CharField(max_length=255, blank=True, help_text="Resumo amigável. Ex: Lançamentos em Setor Bueno até R$ 2M")
    
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"Alerta de {self.nome} ({self.email}) - {self.data_criacao.strftime('%d/%m/%Y')}"

    @property
    def resumo_legivel(self):
        if not self.query_string:
            return "Busca em todos os imóveis"
        
        from urllib.parse import parse_qs
        params = parse_qs(self.query_string)
        partes = []
        
        if 'tipo_imovel' in params:
            slugs = params['tipo_imovel']
            partes.append(", ".join([s.replace('-', ' ').title() for s in slugs]))
        
        if 'finalidade' in params:
            finalidade = params['finalidade'][0]
            if finalidade == 'lancamento':
                partes.append("Lançamentos")
            elif finalidade == 'revenda':
                partes.append("Revenda")
                
        if 'bairro' in params:
            bairro_ids = params['bairro']
            try:
                bairros = Bairro.objects.filter(id__in=bairro_ids).values_list('nome', flat=True)
                if bairros:
                    partes.append("em " + ", ".join(bairros))
            except Exception:
                pass
                
        if 'valor_max' in params and params['valor_max'][0]:
            try:
                v_max = float(params['valor_max'][0])
                partes.append(f"até R$ {v_max:,.0f}".replace(',', '.'))
            except Exception:
                pass
                
        if 'quartos' in params and params['quartos'][0]:
            partes.append(f"{params['quartos'][0]} quartos")
            
        if not partes:
            return "Busca Personalizada"
            
        return " ".join(partes)

from urllib.parse import parse_qs
import re
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=Imovel)
def disparar_alertas_busca(sender, instance, created, **kwargs):
    if not created:
        return # Idealmente, checaríamos se ele ficou ativo/disponível, mas por ora no cadastro

    alertas = AlertaBusca.objects.filter(ativo=True)
    for alerta in alertas:
        params = parse_qs(alerta.query_string)
        match = True
        
        if 'finalidade' in params and instance.finalidade not in params['finalidade']:
            match = False
            
        if match and 'bairro' in params:
            if str(instance.bairro_id) not in params['bairro']:
                match = False
                
        if match and 'tipo_imovel' in params and instance.tipo_imovel:
            if instance.tipo_imovel.slug not in params['tipo_imovel']:
                match = False
                
        if match and 'valor_max' in params and params['valor_max'][0]:
            try:
                v_max = float(params['valor_max'][0])
                if not instance.valor or float(instance.valor) > v_max:
                    match = False
            except ValueError:
                pass

        if match and 'quartos' in params and params['quartos'][0]:
            num = int(re.sub(r'\D', '', params['quartos'][0]) or 0)
            if not instance.quartos or instance.quartos < num:
                match = False

        if match and 'banheiros' in params and params['banheiros'][0]:
            num = int(re.sub(r'\D', '', params['banheiros'][0]) or 0)
            if not instance.banheiros or instance.banheiros < num:
                match = False

        if match and 'vagas' in params and params['vagas'][0]:
            num = int(re.sub(r'\D', '', params['vagas'][0]) or 0)
            if not instance.vagas or instance.vagas < num:
                match = False
                
        if match:
            # Enviar e-mail simulado / print (pode ser adaptado para envio real)
            assunto = f"Lotus Imobiliária: Encontramos um imóvel para você!"
            mensagem = (
                f"Olá {alerta.nome},\n\n"
                f"Um novo imóvel que bate com a sua busca acabou de ser cadastrado:\n\n"
                f"{instance.titulo} - R$ {instance.valor}\n"
                f"Confira no nosso site!\n\n"
                f"Equipe Lotus"
            )
            print(f"--- DISPARANDO ALERTA DE BUSCA PARA {alerta.email} ---")
            print(mensagem)
            
            # send_mail(assunto, mensagem, settings.DEFAULT_FROM_EMAIL, [alerta.email], fail_silently=True)