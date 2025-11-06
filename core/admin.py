from django.contrib import admin
# --- NOVAS IMPORTAÇÕES ---
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# --- FIM DAS IMPORTAÇÕES ---

from .models import (
    Imovel, ImagemImovel, Corretor, Bairro, Lead, 
    ConteudoPagina, TipoImovel, Caracteristica,
    Profile, PostBlog
)

# --- Registos Simples (Evoluído) ---
admin.site.register(Bairro)
admin.site.register(Lead)
admin.site.register(ConteudoPagina)
admin.site.register(TipoImovel)
admin.site.register(Caracteristica)


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

# --- 3. MOSTRAR 'PROFILE' DENTRO DO 'USER' NO ADMIN ---

# Define um "inline" para o Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil do Cliente'
    fields = ('telefone',) # Mostra apenas o campo de telefone

# Define um novo User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

# Des-registra o User admin padrão
admin.site.unregister(User)
# Re-registra o User com o nosso Profile inline
admin.site.register(User, UserAdmin)

@admin.register(PostBlog)
class PostBlogAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo_conteudo', 'data_publicacao')
    list_filter = ('tipo_conteudo', 'data_publicacao')
    search_fields = ('titulo', 'resumo')

    fieldsets = (
        (None, {
            'fields': ('titulo', 'resumo', 'imagem_card')
        }),
        ('O Conteúdo (Escolha um tipo e preencha UM campo)', {
            'fields': ('tipo_conteudo', 'link_url', 'embed_code')
        }),
    )

    # Adiciona um pequeno script para mostrar/esconder os campos no admin
    # (Isso é opcional, mas melhora muito a usabilidade)
    class Media:
        js = ('//ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js', 'admin/js/blog_admin.js',)