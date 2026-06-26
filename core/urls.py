from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('sobre/', views.sobre, name='sobre'),
    path('imoveis/', views.lista_imoveis, name='lista_imoveis'),
    path('equipe/', views.lista_corretores, name='lista_corretores'),
    path('contato/', views.contato, name='contato'),
    path('contato/sucesso/', views.contato_sucesso, name='contato_sucesso'),
    path('imovel/<int:imovel_id>/', views.detalhe_imovel, name='detalhe_imovel'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('minha-conta/', views.minha_conta, name='minha_conta'),

    # --- ROTA ADICIONADA ---
    # Esta URL será chamada pelo JavaScript para salvar os favoritos no banco de dados
    path('sync-favoritos/', views.sync_favoritos, name='sync_favoritos'),
    
    # Comparador
    path('comparar/', views.comparar, name='comparar'),
    
    # Alerta de Busca
    path('salvar-alerta/', views.salvar_alerta, name='salvar_alerta'),
    path('excluir-alerta/<int:alerta_id>/', views.excluir_alerta, name='excluir_alerta'),

    # Políticas (Legal)
    path('politica-privacidade/', views.politica_privacidade, name='politica_privacidade'),
    path('termos-de-uso/', views.termos_uso, name='termos_uso'),
    
    # Blog
    path('blog/', views.lista_blog, name='lista_blog'),
    path('blog/post/<int:post_id>/', views.detalhe_post, name='detalhe_post'),
    
    # SaaS
    path('plataforma/', views.saas_landing, name='saas_landing'),
]