from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import (
    Imovel, ImagemImovel, Corretor, Bairro, Lead, 
<<<<<<< HEAD
    ConteudoPagina, TipoImovel, Caracteristica, PaginaSobre
=======
    ConteudoPagina, TipoImovel, Caracteristica, Cliente
>>>>>>> ccc3a18a88ff6b2aa19ec88d8c4e0d186a48fc02
)
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# admin.site.unregister(SocialApp)
# admin.site.register(SocialApp)
admin.site.register(Cliente)

# --- Registos Simples (Evoluído) ---
admin.site.register(Bairro)
admin.site.register(Lead)
admin.site.register(TipoImovel)
admin.site.register(Caracteristica)

# --- Admin Singleton para a Página "Sobre" ---
@admin.register(PaginaSobre)
class PaginaSobreAdmin(admin.ModelAdmin):
    # O objeto que estamos editando é sempre o mesmo
    def get_object(self, request, object_id, from_field=None):
        # Obtém ou cria o objeto único com a chave 'pagina_sobre'
        obj, created = ConteudoPagina.objects.get_or_create(
            chave='pagina_sobre',
            defaults={
                'titulo': 'Sobre Nós',
                'subtitulo': 'Um pouco sobre nossa história e valores.',
                'corpo': '<p>Escreva aqui o conteúdo da página sobre.</p>'
            }
        )
        return obj

    # Redireciona a "changelist" (lista de objetos) para a página de edição
    def changelist_view(self, request, extra_context=None):
        obj = self.get_object(request, None)
        return HttpResponseRedirect(
            reverse(f'admin:{self.opts.app_label}_{self.opts.model_name}_change', args=(obj.pk,))
        )

    # Oculta os botões de "Adicionar" e "Deletar"
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # Define os campos que aparecerão no formulário de edição
    fields = ('titulo', 'subtitulo', 'corpo')


# --- Painel do Corretor (Corrigido) ---
@admin.register(Corretor)
class CorretorAdmin(admin.ModelAdmin):
    # CORRIGIDO: 'foto_preview' -> 'get_foto_preview'
    list_display = ('nome', 'creci', 'telefone', 'get_foto_preview') 
    search_fields = ('nome', 'creci')
    # CORRIGIDO: 'foto_preview' -> 'get_foto_preview'
    readonly_fields = ('get_foto_preview',) 
    fields = ('nome', 'email', 'telefone', 'creci', 'foto', 'get_foto_preview', 'bio')


# --- Painel do Imóvel (EVOLUÍDO) ---

# Define o 'inline' para as imagens secundárias
class ImagemImovelInline(admin.TabularInline):
    model = ImagemImovel
    extra = 3 # Quantos slots de upload extra aparecem
    # CORRIGIDO: 'imagem_preview' -> 'get_imagem_preview'
    readonly_fields = ('get_imagem_preview',) 

@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    
    # -- Corrigido e Evoluído para corresponder ao models.py --
    list_display = (
        'titulo', 
        'finalidade',    # Evoluído (era 'tipo')
        'categoria',     # Evoluído (Novo)
        'tipo_imovel',   # Evoluído (Novo)
        'valor', 
        'em_destaque', 
        'get_imagem_preview' # Corrigido (era 'imagem_preview')
    )
    
    list_filter = (
        'finalidade',    # Evoluído (era 'tipo')
        'categoria',     # Evoluído (Novo)
        'tipo_imovel',   # Evoluído (Novo)
        'bairro', 
        'em_destaque', 
        'caracteristicas' # Evoluído (Novo)
    )
    
    search_fields = ('titulo', 'descricao', 'bairro__nome', 'endereco')
    
    # -- Corrigido para corresponder ao models.py --
    readonly_fields = (
        'get_imagem_preview', # Corrigido (era 'imagem_preview')
        'data_cadastro', 
        'data_atualizacao'
    )
    
    # Usa um widget melhor para ManyToMany
    filter_horizontal = ('caracteristicas',)

    inlines = [ImagemImovelInline] # Adiciona a galeria de fotos dentro do imóvel

    # Organiza os campos em secções (Fieldsets)
    fieldsets = (
        (None, {
            'fields': ('titulo', 'descricao')
        }),
        ('Classificação (Filtros)', {
            'fields': (
                'finalidade',    # Evoluído (era 'tipo')
                'categoria',     # Evoluído (Novo)
                'tipo_imovel',   # Evoluído (Novo)
                'em_destaque'
            )
        }),
        ('Valores e Medidas (Filtros)', {
            'fields': (
                'valor', 
                'taxa_condominio', # Evoluído (Novo)
                'iptu',            # Evoluído (Novo)
                'quartos', 
                'suites',          # Evoluído (Novo)
                'banheiros',       # Evoluído (Novo)
                'vagas', 
                'area_util',       # Evoluído (era 'area')
                'andar'            # Evoluído (Novo)
            )
        }),
        ('Localização e Corretor', {
            'fields': ('bairro', 'endereco', 'corretor')
        }),
        ('Mídia (Capa)', {
            'fields': ('imagem_principal', 'get_imagem_preview')
        }),
        ('Características (Filtros)', {
            'classes': ('collapse',), # Começa fechado
            'fields': ('caracteristicas',), # Evoluído (Novo)
        }),
        ('Datas (Automático)', {
            'classes': ('collapse',),
            'fields': ('data_cadastro', 'data_atualizacao')
        }),
    )

