from django.contrib import admin
# --- NOVAS IMPORTAÇÕES ---
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# --- FIM DAS IMPORTAÇÕES ---

from .models import (
    Imovel, ImagemImovel, Corretor, Bairro, Lead, 
    ConteudoPagina, TipoImovel, Caracteristica,
    Profile,  # <-- Importar o novo modelo Profile
    PostBlog, AlertaBusca
)

# --- Registos Simples (Evoluído) ---
admin.site.register(Bairro)
admin.site.register(Lead)
admin.site.register(ConteudoPagina)
admin.site.register(TipoImovel)
admin.site.register(Caracteristica)

@admin.register(PostBlog)
class PostBlogAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo_conteudo', 'data_publicacao')
    list_filter = ('tipo_conteudo', 'data_publicacao')
    search_fields = ('titulo', 'resumo')

@admin.register(AlertaBusca)
class AlertaBuscaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'email', 'resumo_busca', 'data_criacao', 'ativo')
    list_filter = ('ativo', 'data_criacao')
    search_fields = ('nome', 'email', 'resumo_busca')


@admin.register(Corretor)
class CorretorAdmin(admin.ModelAdmin):
    # ... (seu CorretorAdmin sem mudança)
    list_display = ('nome', 'creci', 'telefone', 'get_foto_preview') 
    search_fields = ('nome', 'creci')
    readonly_fields = ('get_foto_preview',) 
    fields = ('nome', 'email', 'telefone', 'creci', 'foto', 'get_foto_preview', 'bio')


# --- Painel do Imóvel (EVOLUÍDO) ---
class ImagemImovelInline(admin.TabularInline):
    # ... (seu ImagemImovelInline sem mudança)
    model = ImagemImovel
    extra = 3
    readonly_fields = ('get_imagem_preview',) 

@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    # ... (seu ImovelAdmin sem mudança)
    list_display = ( 'titulo', 'finalidade', 'categoria', 'tipo_imovel', 'valor', 'em_destaque', 'get_imagem_preview')
    list_filter = ( 'finalidade', 'categoria', 'tipo_imovel', 'bairro', 'em_destaque', 'caracteristicas')
    search_fields = ('titulo', 'descricao', 'bairro__nome', 'endereco')
    readonly_fields = ('get_imagem_preview', 'data_cadastro', 'data_atualizacao')
    filter_horizontal = ('caracteristicas',)
    inlines = [ImagemImovelInline]
    fieldsets = (
        (None, {'fields': ('titulo', 'descricao')}),
        ('Classificação (Filtros)', {'fields': ('finalidade', 'categoria', 'tipo_imovel', 'em_destaque')}),
        ('Valores e Medidas (Filtros)', {'fields': ('valor', 'taxa_condominio', 'iptu', 'quartos', 'suites', 'banheiros', 'vagas', 'area_util', 'andar')}),
        ('Localização e Corretor', {'fields': ('bairro', 'endereco', 'corretor')}),
        ('Mídia (Capa)', {'fields': ('imagem_principal', 'get_imagem_preview')}),
        ('Características (Filtros)', {'classes': ('collapse',), 'fields': ('caracteristicas',)}),
        ('Datas (Automático)', {'classes': ('collapse',), 'fields': ('data_cadastro', 'data_atualizacao')}),
    )

# --- REMOVIDO: O ProfileInline causava erro no Admin Público, pois a tabela Profile só existe nos tenants. ---