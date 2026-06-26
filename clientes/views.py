from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Client, Domain
from .forms import OnboardingStep1Form, OnboardingStep2Form, OnboardingStep3Form, OnboardingStep4Form
from django.db import connection

@login_required
def login_redirect_view(request):
    """
    Se o usuário já tem um tenant associado (em um sistema real verificaríamos 
    se ele tem acesso a um Client específico), redirecionamos para o CRM.
    Se não tem, redirecionamos para o Setup.
    """
    # Verificação super simples para o protótipo: se ele já passou pelo step4 no passado
    if request.session.get('onboarding_completo', False):
        return redirect('saas_crm')
    return redirect('saas_setup')

@login_required
def setup_onboarding(request, step=1):
    """
    Wizard Multi-Step de Onboarding.
    Guarda as informações na sessão e só provisiona o banco de dados no final.
    """
    if step not in [1, 2, 3, 4]:
        return redirect('saas_setup', step=1)
        
    # Inicializa sessão de onboarding se não existir
    if 'onboarding_data' not in request.session:
        request.session['onboarding_data'] = {}

    form = None
    template_name = f'clientes/setup_step{step}.html'

    if request.method == 'POST':
        if step == 1:
            form = OnboardingStep1Form(request.POST)
            if form.is_valid():
                request.session['onboarding_data'].update(form.cleaned_data)
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
                plano = form.cleaned_data['plano_escolhido']
                data = request.session['onboarding_data']
                
                # FASE 4: O BIG BANG (Criar o Tenant e o Banco de Dados)
                try:
                    # Garantimos que estamos no schema public
                    with connection.cursor() as cursor:
                        connection.set_schema_to_public()
                    
                    schema_name = data['subdominio'].lower().replace('-', '_')
                    
                    novo_tenant = Client(
                        schema_name=schema_name,
                        nome=data['nome_imobiliaria'],
                        tipo_documento=data.get('tipo_documento', 'CNPJ'),
                        cpf_cnpj=data['cpf_cnpj'],
                        telefone=data['telefone'],
                        
                        cep=data.get('cep', ''),
                        rua=data.get('rua', ''),
                        numero=data.get('numero', ''),
                        complemento=data.get('complemento', ''),
                        bairro=data.get('bairro', ''),
                        cidade=data.get('cidade', ''),
                        uf=data.get('uf', ''),
                        
                        cor_primaria=data['cor_primaria'],
                        texto_quem_somos=data.get('texto_quem_somos', ''),
                        portfolio_lancamento=data.get('portfolio_lancamento', True),
                        portfolio_revenda=data.get('portfolio_revenda', True),
                        portfolio_aluguel=data.get('portfolio_aluguel', False),
                        auto_create_schema=True
                    )
                    novo_tenant.save() # Isso demora uns 5 segundos pois roda o migrate_schemas interno!
                    
                    # Cria o domínio
                    domain_name = f"{data['subdominio']}.imob.dsprime.org"
                    domain = Domain(domain=domain_name, tenant=novo_tenant, is_primary=True)
                    domain.save()
                    
                    request.session['onboarding_completo'] = True
                    request.session['tenant_domain'] = domain_name
                    del request.session['onboarding_data'] # Limpa a sessão
                    
                    messages.success(request, f"Plataforma criada com sucesso! Seu domínio é {domain_name}")
                    return redirect('saas_crm')
                    
                except Exception as e:
                    messages.error(request, f"Erro ao criar plataforma: {str(e)}")
                    return redirect('saas_setup', step=4)

    else:
        # GET
        data = request.session.get('onboarding_data', {})
        if step == 1:
            form = OnboardingStep1Form(initial=data)
        elif step == 2:
            form = OnboardingStep2Form(initial=data)
        elif step == 3:
            form = OnboardingStep3Form(initial=data)
        elif step == 4:
            form = OnboardingStep4Form()

    return render(request, template_name, {'form': form, 'step': step})

@login_required
def crm_dashboard(request):
    """
    Página inicial do CRM (Mock).
    """
    tenant_domain = request.session.get('tenant_domain', None)
    return render(request, 'clientes/crm.html', {'tenant_domain': tenant_domain})
