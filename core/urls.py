from django.urls import path
from . import views

# Damos um 'namespace' para organizar
app_name = 'core'

urlpatterns = [
    # As nossas rotas existentes
    path('', views.index, name='index'),
    path('sobre/', views.sobre, name='sobre'),
    path('imoveis/', views.lista_imoveis, name='lista_imoveis'),
    path('equipa/', views.lista_corretores, name='lista_corretores'),
    path('contato/', views.contato, name='contato'),
    path('contato/sucesso/', views.contato_sucesso, name='contato_sucesso'),

    # --- A NOVA ROTA (Passo 2 do Plano) ---
    # Esta rota espera um ID (ex: /imoveis/123/)
    path('imoveis/<int:imovel_id>/', views.detalhe_imovel, name='detalhe_imovel'),
]

