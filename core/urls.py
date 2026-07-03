from django.urls import path
from . import views
from . import stripe_views
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
    
    # SaaS Master Routes
    path('plataforma/', views.saas_landing, name='saas_landing'),
    
    # Tenant CRM
    path('crm/', views.crm_kanban, name='crm_kanban'),
    path('crm/gaveta/', views.crm_gaveta, name='crm_gaveta'),
    path('crm/relatorios/', views.crm_relatorios, name='crm_relatorios'),
    path('crm/assinatura/', views.assinatura, name='assinatura'),
    path('crm/imovel/novo/', views.imovel_criar, name='imovel_criar'),
    path('crm/imoveis/', views.crm_imoveis, name='crm_imoveis'),
    path('crm/importar-xml/', views.importar_xml, name='importar_xml'),
    path('crm/api/import-status/', views.api_import_status, name='api_import_status'),
    path('crm/api/import-clear/', views.api_import_clear, name='api_import_clear'),
    path('crm/api/leads/', views.api_leads, name='api_leads'),
    path('crm/api/leads/update/', views.api_leads_update, name='api_leads_update'),
    path('crm/api/leads/update_corretor/', views.api_leads_update_corretor, name='api_leads_update_corretor'),
    path('crm/marketing/', views.crm_marketing, name='crm_marketing'),
    path('crm/clientes/', views.crm_clientes, name='crm_clientes'),
    path('crm/configuracoes/', views.configuracoes_site, name='configuracoes_site'),
    path('crm/blog/', views.crm_blog, name='crm_blog'),
    path('crm/equipe/', views.crm_equipe, name='crm_equipe'),
    path('crm/comissoes/', views.crm_comissoes, name='crm_comissoes'),
    
    # Stripe Billing
    path('billing/checkout/', stripe_views.create_checkout_session, name='stripe_checkout'),
    path('billing/portal/', stripe_views.stripe_customer_portal, name='stripe_portal'),
    path('billing/upgrade/', stripe_views.upgrade_plan, name='stripe_upgrade'),
    path('billing/downgrade/', stripe_views.downgrade_plan, name='stripe_downgrade'),
    path('billing/cancel/', stripe_views.cancel_plan, name='stripe_cancel'),
    path('billing/update-card/', stripe_views.update_card, name='stripe_update_card'),
    path('billing/faturamento/', stripe_views.faturamento_view, name='faturamento'),
    path('webhooks/stripe/', stripe_views.stripe_webhook, name='stripe_webhook'),
]