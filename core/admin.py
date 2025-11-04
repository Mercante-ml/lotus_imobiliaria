from django.contrib import admin
from .models import (
    Imovel, ImagemImovel, Corretor, Bairro, Lead, 
    ConteudoPagina, TipoImovel, Caracteristica  # Modelos evoluídos
)

# --- Registos Simples (Evoluído) ---
admin.site.register(Bairro)
admin.site.register(Lead)
admin.site.register(ConteudoPagina)
# Novos modelos registados:
admin.site.register(TipoImovel)
admin.site.register(Caracteristica)


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

