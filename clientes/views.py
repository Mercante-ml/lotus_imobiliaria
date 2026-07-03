from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Client, Domain
from .forms import (
    OnboardingStep1Form, OnboardingStep2Form, OnboardingStep3Form, 
    OnboardingStep4Form, OnboardingStep5Form, OnboardingStep6Form, 
    OnboardingStep7Form, OnboardingStep8Form
)
from django.db import connection

@login_required
def login_redirect_view(request):
    """
    Se o usuário já tem um tenant associado (em um sistema real verificaríamos 
    se ele tem acesso a um Client específico), redirecionamos para o CRM.
    Se não tem, redirecionamos para o Setup.
    """
    if request.user.is_superuser:
        if connection.schema_name != 'public':
            return redirect('core:crm_kanban')
        return redirect('/admin/')
        
    # Se estivermos no schema de um tenant (imobiliária), joga pro CRM ou para Minha Conta
    if connection.schema_name != 'public':
        is_broker = request.user.is_superuser
        if not is_broker:
            from core.models import Corretor
            is_broker = Corretor.objects.filter(user=request.user).exists()
            
        if is_broker:
            return redirect('core:crm_kanban')
        else:
            return redirect('core:minha_conta')
        
    # Se estivermos no public, checamos a sessão para o onboarding
    if request.session.get('onboarding_completo', False):
        domain_name = request.session.get('tenant_domain')
        if domain_name:
            return redirect(f'https://{domain_name}/crm/')
    
    return redirect('saas_setup')

@login_required
def setup_onboarding(request, step=1):
    """
    Wizard Multi-Step de Onboarding.
    Guarda as informações na sessão e só provisiona o banco de dados no final.
    """
    if step not in range(1, 9):
        return redirect('saas_setup', step=1)
        
    # Inicializa sessão de onboarding se não existir
    if 'onboarding_data' not in request.session:
        request.session['onboarding_data'] = {}

    form = None
    template_name = f'clientes/setup_step{step}.html'

    if request.method == 'POST':
        if step == 1:
            form = OnboardingStep1Form(request.POST, request.FILES)
            if form.is_valid():
                cd = form.cleaned_data.copy()
                if 'logo' in request.FILES:
                    from django.core.files.storage import default_storage
                    logo_file = request.FILES['logo']
                    file_path = default_storage.save(f'tmp_logo/{logo_file.name}', logo_file)
                    request.session['onboarding_data']['logo_path'] = file_path
                if 'logo' in cd:
                    del cd['logo']
                request.session['onboarding_data'].update(cd)
                request.session.modified = True
                return redirect('saas_setup', step=2)
        
        elif step == 2:
            form = OnboardingStep2Form(request.POST)
            if form.is_valid():
                request.session['onboarding_data'].update(form.cleaned_data)
                request.session.modified = True
                return redirect('saas_setup', step=3)
                
        elif step == 3:
            form = OnboardingStep3Form(request.POST)
            if form.is_valid():
                request.session['onboarding_data'].update(form.cleaned_data)
                request.session.modified = True
                return redirect('saas_setup', step=4)
                
        elif step == 4:
            form = OnboardingStep4Form(request.POST)
            if form.is_valid():
                request.session['onboarding_data'].update(form.cleaned_data)
                request.session.modified = True
                return redirect('saas_setup', step=5)
                
        elif step == 5:
            form = OnboardingStep5Form(request.POST, request.FILES)
            if form.is_valid():
                # Handling equipe action (upload/manual/pular)
                if 'arquivo_equipe' in request.FILES and form.cleaned_data.get('acao_equipe') == 'upload':
                    from django.core.files.storage import default_storage
                    arq = request.FILES['arquivo_equipe']
                    file_path = default_storage.save(f'tmp_equipe/{arq.name}', arq)
                    request.session['onboarding_data']['equipe_file_path'] = file_path
                
                cd = form.cleaned_data.copy()
                if 'arquivo_equipe' in cd:
                    del cd['arquivo_equipe']
                request.session['onboarding_data'].update(cd)
                request.session.modified = True
                return redirect('saas_setup', step=6)
                
        elif step == 6:
            form = OnboardingStep6Form(request.POST, request.FILES)
            if form.is_valid():
                if 'arquivo_blog' in request.FILES and form.cleaned_data.get('acao_blog') == 'upload':
                    from django.core.files.storage import default_storage
                    arq = request.FILES['arquivo_blog']
                    file_path = default_storage.save(f'tmp_blog/{arq.name}', arq)
                    request.session['onboarding_data']['blog_file_path'] = file_path
                
                cd = form.cleaned_data.copy()
                if 'arquivo_blog' in cd:
                    del cd['arquivo_blog']
                request.session['onboarding_data'].update(cd)
                request.session.modified = True
                return redirect('saas_setup', step=7)
                
        elif step == 7:
            form = OnboardingStep7Form(request.POST, request.FILES)
            if form.is_valid():
                if 'arquivo_xml' in request.FILES and form.cleaned_data.get('acao_imoveis') == 'upload':
                    from django.core.files.storage import default_storage
                    xml_file = request.FILES['arquivo_xml']
                    file_path = default_storage.save(f'tmp_xml/{xml_file.name}', xml_file)
                    request.session['onboarding_data']['xml_file_path'] = file_path
                
                cd = form.cleaned_data.copy()
                if 'arquivo_xml' in cd:
                    del cd['arquivo_xml']
                request.session['onboarding_data'].update(cd)
                request.session.modified = True
                return redirect('saas_setup', step=8)
                
        elif step == 8:
            form = OnboardingStep8Form(request.POST)
            if form.is_valid():
                plano = form.cleaned_data['plano_escolhido']
                data = request.session['onboarding_data']
                
                # FASE FINAL: Criar o Tenant e o Banco de Dados
                try:
                    with connection.cursor() as cursor:
                        connection.set_schema_to_public()
                    
                    schema_name = data['subdominio'].lower().replace('-', '_')
                    
                    novo_tenant = Client(
                        schema_name=schema_name,
                        nome=data['nome_imobiliaria'],
                        tipo_documento=data.get('tipo_documento', 'CNPJ'),
                        cpf_cnpj=data.get('cpf_cnpj', ''),
                        telefone=data.get('telefone', ''),
                        empresa_email=data.get('empresa_email', ''),
                        
                        cep=data.get('cep', ''),
                        rua=data.get('rua', ''),
                        numero=data.get('numero', ''),
                        complemento=data.get('complemento', ''),
                        bairro=data.get('bairro', ''),
                        cidade=data.get('cidade', ''),
                        uf=data.get('uf', ''),
                        
                        cor_primaria=data['cor_primaria'],
                        
                        # Home Texts
                        home_hero_bg_preset=data.get('home_hero_bg_preset', 'preset_1'),
                        home_hero_tag=data.get('home_hero_tag', ''),
                        home_hero_titulo=data.get('home_hero_titulo', ''),
                        home_hero_destaque=data.get('home_hero_destaque', ''),
                        home_hero_subtitulo=data.get('home_hero_subtitulo', ''),
                        home_manifesto_titulo=data.get('home_manifesto_titulo', ''),
                        home_manifesto_destaque=data.get('home_manifesto_destaque', ''),
                        home_manifesto_texto=data.get('home_manifesto_texto', ''),
                        
                        # Sobre Texts
                        sobre_titulo=data.get('sobre_titulo', ''),
                        sobre_subtitulo=data.get('sobre_subtitulo', ''),
                        sobre_citacao=data.get('sobre_citacao', ''),
                        texto_quem_somos=data.get('texto_quem_somos', ''),
                        sobre_missao=data.get('sobre_missao', ''),
                        sobre_visao=data.get('sobre_visao', ''),
                        
                        # Visibility
                        exibir_equipe=data.get('exibir_equipe', True),
                        titulo_equipe=data.get('titulo_equipe', 'Nossa Equipe'),
                        subtitulo_equipe=data.get('subtitulo_equipe', ''),
                        exibir_blog=data.get('exibir_blog', True),
                        
                        portfolio_lancamento=data.get('portfolio_lancamento', True),
                        portfolio_revenda=data.get('portfolio_revenda', True),
                        portfolio_aluguel=data.get('portfolio_aluguel', False)
                    )
                    novo_tenant.save()
                    
                    # Salva logo
                    logo_path = data.get('logo_path')
                    if logo_path:
                        import os
                        from django.core.files.storage import default_storage
                        from django.core.files import File
                        try:
                            full_path = default_storage.path(logo_path)
                            with open(full_path, 'rb') as f:
                                novo_tenant.logo.save(os.path.basename(logo_path), File(f), save=True)
                        except Exception as e:
                            print(f"Erro ao salvar logo: {e}")
                    
                    # Cria o domínio
                    from django.conf import settings
                    base_domain = settings.ROOT_DOMAIN if settings.ROOT_DOMAIN.startswith('.') else f'.{settings.ROOT_DOMAIN}'
                    domain_name = f"{data['subdominio'].lower()}{base_domain}"
                    domain = Domain(domain=domain_name, tenant=novo_tenant, is_primary=True)
                    domain.save()
                    
                    from django_tenants.utils import tenant_context
                    from core.models import Corretor
                    with tenant_context(novo_tenant):
                        Corretor.objects.create(
                            user=request.user,
                            nome=request.user.first_name or request.user.username or data['nome_imobiliaria'],
                            email=request.user.email,
                            telefone=data.get('telefone', ''),
                            cargo='Diretor',
                            exibir_no_site=True,
                            comissao_venda_direta=100.0,
                            comissao_equipe=0.0
                        )
                    
                    # Cloudflare Tunnel
                    from clientes.cloudflare import CloudflareTunnelManager
                    try:
                        cf_manager = CloudflareTunnelManager()
                        cf_manager.add_route(domain_name)
                    except Exception as e:
                        print(f"Aviso CF: {e}")
                    
                    # Importação XML
                    xml_file_path = data.get('xml_file_path')
                    if xml_file_path:
                        try:
                            from core.utils import processar_xml_vivareal
                            from django.core.files.storage import default_storage
                            full_path = default_storage.path(xml_file_path)
                            processar_xml_vivareal(full_path, tenant=novo_tenant)
                        except Exception as e:
                            print(f"Erro ao processar XML: {e}")
                            
                    # IMPORTANTE: Aqui poderíamos ter chamadas para importar CSV de corretores e blog posts
                    # se acao_equipe == 'upload' e tiver equipe_file_path
                    # se acao_blog == 'upload' e tiver blog_file_path
                    
                    request.session['onboarding_completo'] = True
                    request.session['tenant_domain'] = domain_name
                    del request.session['onboarding_data']
                    
                    messages.success(request, f"Plataforma criada com sucesso! Redirecionando para o seu CRM...")
                    return redirect(f'https://{domain_name}/crm/')
                    
                except Exception as e:
                    messages.error(request, f"Erro ao criar plataforma: {str(e)}")
                    return redirect('saas_setup', step=8)

    else:
        # GET
        data = request.session.get('onboarding_data', {})
        if step == 1: form = OnboardingStep1Form(initial=data)
        elif step == 2: form = OnboardingStep2Form(initial=data)
        elif step == 3: form = OnboardingStep3Form(initial=data)
        elif step == 4: form = OnboardingStep4Form(initial=data)
        elif step == 5: form = OnboardingStep5Form(initial=data)
        elif step == 6: form = OnboardingStep6Form(initial=data)
        elif step == 7: form = OnboardingStep7Form(initial=data)
        elif step == 8: form = OnboardingStep8Form(initial=data)

    return render(request, template_name, {'form': form, 'step': step})

@login_required
def crm_dashboard(request):
    """
    Página inicial do CRM (Mock).
    """
    tenant_domain = request.session.get('tenant_domain', None)
    return render(request, 'clientes/crm.html', {'tenant_domain': tenant_domain})
