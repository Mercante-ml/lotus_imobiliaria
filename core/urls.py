from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('sobre/', views.sobre, name='sobre'),
    path('imoveis/', views.lista_imoveis, name='lista_imoveis'),
    path('equipa/', views.lista_corretores, name='lista_corretores'),
    path('contato/', views.contato, name='contato'),
    path('contato/sucesso/', views.contato_sucesso, name='contato_sucesso'),
    path('imovel/<int:imovel_id>/', views.detalhe_imovel, name='detalhe_imovel'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('minha-conta/', views.minha_conta, name='minha_conta'),    
    path('toggle-favorito/', views.toggle_favorito, name='toggle_favorito'),
    path('sync-favoritos/', views.sync_favoritos, name='sync_favoritos'),            
    path('api/toggle_favorito/', views.toggle_favorito, name='toggle_favorito'),
    path('api/sync_favoritos/', views.sync_favoritos, name='sync_favoritos'),    
    path('blog/', views.lista_blog, name='lista_blog'),
    path('blog/<int:post_id>/', views.detalhe_post, name='detalhe_post'),
    path('termos-de-uso/', views.termos_de_uso, name='termos_de_uso'),
    path('politica-de-privacidade/', views.lgpd, name='lgpd'),
    path('trabalhe-conosco/', views.trabalhe_conosco, name='trabalhe_conosco'),
    path('trabalhe-conosco/sucesso/', views.trabalhe_conosco_sucesso, name='trabalhe_conosco_sucesso'),
]