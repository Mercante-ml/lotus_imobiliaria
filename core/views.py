from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import LeadForm, UserUpdateForm, ProfileUpdateForm
from .models import (
    Imovel, Bairro, Corretor, ConteudoPagina, 
    TipoImovel, Caracteristica, ImagemImovel, Profile, PostBlog, AlertaBusca, Lead
)
from django.db.models import Q, F
import re
import urllib.parse
import html

# --- (views index, sobre - sem mudança) ---
def index(request):
    destaques = Imovel.objects.filter(finalidade='lancamento', em_destaque=True).order_by('-data_atualizacao')[:3]
    bairros = Bairro.objects.all().order_by('nome')
    ultimos_posts = PostBlog.objects.all().order_by('-data_publicacao')[:3]
    context = {'destaques': destaques, 'bairros': bairros, 'ultimos_posts': ultimos_posts}
    return render(request, 'core/index.html', context)

def sobre(request):
    try:
        conteudo = ConteudoPagina.objects.get(chave='pagina_sobre')
    except ConteudoPagina.DoesNotExist:
        conteudo = {'titulo': 'Sobre a Lotus Imobiliária', 'subtitulo': 'O seu espaço de renascimento. Clareza e elegância na busca pelo extraordinário.'}
    return render(request, 'core/sobre.html', {'conteudo': conteudo})


# --- VIEW LISTA_IMOVEIS (CORRIGIDA) ---
def lista_imoveis(request):
    # Trava: Se a importação estiver rodando ou a base estiver zerada, mostra tela de manutenção
    status_importacao = ConteudoPagina.objects.filter(chave='status_importacao').first()
    is_rodando = status_importacao and status_importacao.titulo == 'rodando'
    
    if is_rodando or not Imovel.objects.exists():
        progresso = status_importacao.subtitulo if status_importacao else "Iniciando..."
        return render(request, 'core/manutencao.html', {'progresso': progresso})

    request.session['last_search_url'] = request.get_full_path()
    imoveis = Imovel.objects.filter(valor__isnull=False).order_by('-data_atualizacao')
    tipos_imovel = TipoImovel.objects.all().order_by('nome')
    caracteristicas = Caracteristica.objects.all().order_by('nome')
    
    filtros_aplicados = request.GET.copy()
    page_number = filtros_aplicados.pop('page', [1])[0]
    
    # --- Aplicação dos Filtros ---
    finalidade = filtros_aplicados.get('finalidade', 'lancamento')
    if finalidade: imoveis = imoveis.filter(finalidade=finalidade)
    
    categoria = filtros_aplicados.get('categoria')
    if categoria: imoveis = imoveis.filter(categoria=categoria)
    
    query = filtros_aplicados.get('query')
    if query: imoveis = imoveis.filter(titulo__icontains=query)
    
    estado = filtros_aplicados.get('estado')
    if estado: imoveis = imoveis.filter(estado=estado)
    
    cidade = filtros_aplicados.get('cidade')
    if cidade:
        imoveis = imoveis.filter(cidade__iexact=cidade)
    
    tipos_slugs = filtros_aplicados.getlist('tipo_imovel')
    if tipos_slugs: imoveis = imoveis.filter(tipo_imovel__slug__in=tipos_slugs)
    
    # Mostrar TODOS os bairros (não apenas os filtrados) para a barra não sumir
    bairros = Bairro.objects.all().order_by('nome')

    bairro_ids = filtros_aplicados.getlist('bairro')
    if bairro_ids: imoveis = imoveis.filter(bairro_id__in=bairro_ids)
    
    valor_min = filtros_aplicados.get('valor_min')
    valor_max = filtros_aplicados.get('valor_max')
    condominio_min = filtros_aplicados.get('condominio_min')
    condominio_max = filtros_aplicados.get('condominio_max')
    iptu_min = filtros_aplicados.get('iptu_min')
    iptu_max = filtros_aplicados.get('iptu_max')
    
    if valor_min: imoveis = imoveis.filter(valor__gte=valor_min)
    if valor_max: imoveis = imoveis.filter(valor__lte=valor_max)
    if condominio_min: imoveis = imoveis.filter(taxa_condominio__gte=condominio_min)
    if condominio_max: imoveis = imoveis.filter(taxa_condominio__lte=condominio_max)
    if iptu_min: imoveis = imoveis.filter(iptu__gte=iptu_min)
    if iptu_max: imoveis = imoveis.filter(iptu__lte=iptu_max)
    
    quartos = filtros_aplicados.get('quartos')
    vagas = filtros_aplicados.get('vagas')
    banheiros = filtros_aplicados.get('banheiros')
    
    if quartos:
        num = re.sub(r'\D', '', quartos)
        imoveis = imoveis.filter(quartos__gte=num)
    if vagas:
        num = re.sub(r'\D', '', vagas)
        imoveis = imoveis.filter(vagas__gte=num)
    if banheiros:
        num = re.sub(r'\D', '', banheiros)
        imoveis = imoveis.filter(banheiros__gte=num)
        
    ordenacao = filtros_aplicados.get('ordenacao', 'relevancia')
    if ordenacao == 'valor_asc':
        imoveis = imoveis.order_by(F('valor').asc(nulls_last=True))
    elif ordenacao == 'valor_desc':
        imoveis = imoveis.order_by(F('valor').desc(nulls_last=True))
    elif ordenacao == 'area_desc':
        imoveis = imoveis.order_by(F('area_util').desc(nulls_last=True))
    elif ordenacao == 'area_asc':
        imoveis = imoveis.order_by(F('area_util').asc(nulls_last=True))
    else:
        imoveis = imoveis.order_by('-em_destaque', '-data_atualizacao')
        
    imoveis_list = imoveis.distinct()
    paginator = Paginator(imoveis_list, 12) 
    page_obj = paginator.get_page(page_number)
    filtros_aplicados_query = filtros_aplicados.urlencode()
    
    elided_page_range = paginator.get_elided_page_range(number=page_obj.number, on_each_side=2, on_ends=1)
    bairros_selecionados_objs = Bairro.objects.filter(id__in=bairro_ids) if bairro_ids else []

    context = {
        'page_obj': page_obj, 'filtros_aplicados_query': filtros_aplicados_query, 
        'bairros': bairros, 'tipos_imovel': tipos_imovel, 
        'elided_page_range': elided_page_range,
        'bairros_selecionados_objs': bairros_selecionados_objs,
        'caracteristicas': caracteristicas, 'filtros_aplicados': filtros_aplicados,
    }
    return render(request, 'core/lista_imoveis.html', context)


# --- (outras views: lista_corretores, contato, etc. sem mudança) ---
def lista_corretores(request):
    corretores = Corretor.objects.all()
    try:
        conteudo = ConteudoPagina.objects.get(chave='pagina_corretores')
    except ConteudoPagina.DoesNotExist:
        conteudo = {'titulo': 'A Nossa Equipa', 'subtitulo': 'Especialistas dedicados a encontrar o imóvel que reflete a sua essences.'}
    return render(request, 'core/lista_corretores.html', {'corretores': corretores, 'conteudo': conteudo})

def contato(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:contato_sucesso')
    else:
        form = LeadForm()
    return render(request, 'core/contato.html', {'form': form})

def contato_sucesso(request):
    return render(request, 'core/contato_sucesso.html')

def detalhe_imovel(request, imovel_id):
    imovel = get_object_or_404(Imovel.objects.prefetch_related('imagens_secundarias', 'caracteristicas'), id=imovel_id)
    similares = Imovel.objects.filter(bairro=imovel.bairro, categoria=imovel.categoria).exclude(id=imovel_id)[:3] 
    imovel_url = request.build_absolute_uri()
    mensagem = f"Olá, eu vi o imóvel '{imovel.titulo}' no site ({imovel_url}) e gostaria de mais informações."
    whatsapp_url = f"https://wa.me/5562983188400?text={urllib.parse.quote(mensagem)}"
    last_search_url = request.session.get('last_search_url', '/imoveis/')
    imovel.descricao = html.unescape(imovel.descricao)
    context = {'imovel': imovel, 'similares': similares, 'whatsapp_url': whatsapp_url, 'last_search_url': last_search_url,}
    return render(request, 'core/detalhe_imovel.html', context)

@login_required
def minha_conta(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!', extra_tags='profile_update')
            return redirect('core:minha_conta')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    # Busca os alertas ativos do usuário
    alertas = request.user.alertas.filter(ativo=True).order_by('-data_criacao')
    
    context = {'user_form': user_form, 'profile_form': profile_form, 'alertas': alertas}
    return render(request, 'core/minha_conta.html', context)

@login_required
def favoritos(request):
    imoveis_favoritos = request.user.profile.favoritos.all().order_by('-data_atualizacao')
    last_search_url = request.session.get('last_search_url', '/imoveis/')
    context = {'imoveis': imoveis_favoritos, 'last_search_url': last_search_url}
    return render(request, 'core/favoritos.html', context)

@login_required
@require_POST
def sync_favoritos(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not isinstance(ids, list):
            return JsonResponse({'status': 'error', 'message': 'IDs inválidos'}, status=400)
        ids_int = [int(id_str) for id_str in ids]
        imoveis = Imovel.objects.filter(id__in=ids_int)
        request.user.profile.favoritos.add(*imoveis)
        return JsonResponse({'status': 'success', 'total': request.user.profile.favoritos.count()})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# --- 1. NOVA VIEW ADICIONADA AQUI ---
# Esta view vai "interceptar" a página de "sucesso" do allauth
@login_required
def custom_password_change_done(request):
    # 1. Adiciona a mensagem de sucesso (com uma nova tag)
    messages.success(request, 'Sua senha foi alterada com sucesso!', extra_tags='password_update')
    
    # 2. Redireciona o usuário de volta para a página "Minha Conta"
    return redirect('core:minha_conta')

def comparar(request):
    return render(request, 'core/comparar.html')

def politica_privacidade(request):
    return render(request, 'core/politica_privacidade.html')

def custom_404(request, exception):
    return render(request, 'core/404.html', status=404)

def saas_landing(request):
    """Landing page para vender o próprio sistema como SaaS"""
    return render(request, 'core/saas_landing.html')

def termos_uso(request):
    return render(request, 'core/termos_uso.html')

def lista_blog(request):
    posts_list = PostBlog.objects.all().order_by('-data_publicacao')
    paginator = Paginator(posts_list, 9) # 9 posts por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/blog.html', {'page_obj': page_obj})

def detalhe_post(request, post_id):
    post = get_object_or_404(PostBlog, id=post_id)
    return render(request, 'core/blog_detalhe.html', {'post': post})

@login_required
@require_POST
def salvar_alerta(request):
    try:
        data = json.loads(request.body)
        query_string = data.get('query_string', '')
        resumo_busca = data.get('resumo_busca', 'Busca Personalizada')
        
        nome = request.user.first_name or request.user.username
        email = request.user.email
            
        alerta = AlertaBusca.objects.create(
            user=request.user,
            nome=nome,
            email=email,
            query_string=query_string,
            resumo_busca=resumo_busca
        )
        return JsonResponse({'status': 'success', 'message': 'Alerta salvo com sucesso!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def excluir_alerta(request, alerta_id):
    alerta = get_object_or_404(AlertaBusca, id=alerta_id, user=request.user)
    alerta.delete()
    messages.success(request, 'Alerta removido com sucesso!', extra_tags='profile_update')
    return redirect('core:minha_conta')
@login_required
def crm_kanban(request):
    """ CRM Kanban View for the Tenant """
    leads = Lead.objects.all().order_by('-data_criacao')
    corretores = Corretor.objects.all()
    
    # Trial Logic (14 days)
    import datetime
    tenant = request.tenant
    hoje = datetime.date.today()
    dias_usados = (hoje - tenant.criado_em).days
    dias_restantes = max(0, 14 - dias_usados)
    
    # Se já tem assinatura ativa no Stripe, não mostra banner de trial
    if tenant.status_assinatura == 'active':
        dias_restantes = -1 # Para esconder o banner
        
    from core.models import Imovel
    
    total_imoveis = Imovel.objects.count()
    imoveis_lancamento = Imovel.objects.filter(finalidade='lancamento').count()
    imoveis_revenda = Imovel.objects.filter(finalidade='revenda').count()
    
    # Busca a data do imóvel mais recente como "Data da Última Carga"
    ultimo_imovel = Imovel.objects.order_by('-data_atualizacao').first()
    data_ultima_carga = ultimo_imovel.data_atualizacao if ultimo_imovel else None
        
    context = {
        'leads': leads,
        'corretores': corretores,
        'is_owner': True,
        'is_diamond': tenant.plano_ativo == 'corporate',
        'total_vendido': 0,
        'minha_comissao': 0,
        'dias_restantes': dias_restantes,
        'gb_used': round(tenant.get_gb_used(), 2),
        'gb_limit': tenant.get_gb_limit(),
        'gb_perc': tenant.get_gb_percentage(),
        'total_imoveis': total_imoveis,
        'imoveis_lancamento': imoveis_lancamento,
        'imoveis_revenda': imoveis_revenda,
        'data_ultima_carga': data_ultima_carga,
    }
    return render(request, 'core/crm/kanban.html', context)

@login_required
def assinatura(request):
    tenant = request.tenant
    
    # Busca os price IDs do env
    from django.conf import settings
    prices = {
        'corporate': getattr(settings, 'STRIPE_PRICE_CORPORATE', ''),
        '10gb': getattr(settings, 'STRIPE_PRICE_10GB', ''),
        '50gb': getattr(settings, 'STRIPE_PRICE_50GB', '')
    }
    
    context = {
        'tenant': tenant,
        'gb_used': round(tenant.get_gb_used(), 2),
        'gb_limit': tenant.get_gb_limit(),
        'gb_perc': tenant.get_gb_percentage(),
        'prices': prices,
        'is_corporate': tenant.plano_ativo == 'corporate',
    }
    return render(request, 'core/crm/assinatura.html', context)

@login_required
def imovel_criar(request):
    """ View manual para cadastrar um novo imóvel (com todos os campos) """
    if request.method == 'POST':
        try:
            from core.models import Bairro, TipoImovel
            
            titulo = request.POST.get('titulo')
            descricao = request.POST.get('descricao', '')
            finalidade = request.POST.get('finalidade', 'revenda')
            categoria = request.POST.get('categoria', 'residencial')
            
            valor = request.POST.get('valor') or None
            taxa_condominio = request.POST.get('taxa_condominio') or None
            iptu = request.POST.get('iptu') or None
            
            quartos = request.POST.get('quartos') or None
            suites = request.POST.get('suites') or None
            banheiros = request.POST.get('banheiros') or None
            vagas = request.POST.get('vagas') or None
            area_util = request.POST.get('area_util') or None
            andar = request.POST.get('andar') or None
            
            endereco = request.POST.get('endereco', '')
            cidade = request.POST.get('cidade', '')
            estado = request.POST.get('estado', '')
            
            # Tratamento de Bairro
            bairro_nome = request.POST.get('bairro', '').strip()
            bairro_obj = None
            if bairro_nome:
                bairro_obj, _ = Bairro.objects.get_or_create(nome=bairro_nome)
                
            # Tratamento de Tipo de Imóvel
            tipo_nome = request.POST.get('tipo_imovel', '').strip()
            tipo_obj = None
            if tipo_nome:
                tipo_obj, _ = TipoImovel.objects.get_or_create(nome=tipo_nome)
            
            imovel = Imovel.objects.create(
                titulo=titulo,
                descricao=descricao,
                finalidade=finalidade,
                categoria=categoria,
                tipo_imovel=tipo_obj,
                valor=valor,
                taxa_condominio=taxa_condominio,
                iptu=iptu,
                quartos=quartos,
                suites=suites,
                banheiros=banheiros,
                vagas=vagas,
                area_util=area_util,
                andar=andar,
                bairro=bairro_obj,
                endereco=endereco,
                cidade=cidade,
                estado=estado
            )
            if 'imagem_principal' in request.FILES:
                imovel.imagem_principal = request.FILES['imagem_principal']
                imovel.save()
                
            # Processa fotos da galeria (múltiplas fotos)
            if 'galeria' in request.FILES:
                from core.models import ImagemImovel
                fotos = request.FILES.getlist('galeria')
                # Limita a 10 fotos extras para segurança/performance
                for foto in fotos[:10]:
                    ImagemImovel.objects.create(imovel=imovel, imagem=foto)
                
            messages.success(request, 'Imóvel cadastrado com sucesso!')
            return redirect('core:crm_kanban')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar imóvel: {str(e)}')
            
    return render(request, 'core/crm/imovel_form.html')

@login_required
def importar_xml(request):
    """ View manual para importar XML direto do CRM """
    if request.method == 'POST':
        if 'arquivo_xml' in request.FILES:
            try:
                xml_file = request.FILES['arquivo_xml']
                
                from django.core.files.storage import default_storage
                import os
                file_path = default_storage.save(f'tmp_xml/{xml_file.name}', xml_file)
                full_path = default_storage.path(file_path)
                
                from core.utils import processar_xml_vivareal
                processar_xml_vivareal(full_path, tenant=request.tenant)
                
                messages.success(request, 'Processamento de XML iniciado em segundo plano!')
                return redirect('core:crm_kanban')
            except Exception as e:
                messages.error(request, f'Erro ao processar XML: {str(e)}')
                return render(request, 'core/crm/importar_xml.html', status=400)
    
    return render(request, 'core/crm/importar_xml.html')

from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.cache import never_cache

@login_required
@never_cache
def api_import_status(request):
    """ Retorna o progresso atual do processamento de XML em background """
    tenant_schema = request.tenant.schema_name
    cache_key = f'sync_{tenant_schema}'
    
    data = cache.get(cache_key)
    print(f"DEBUG api_import_status: tenant={tenant_schema}, cache_data={data}")
    if not data:
        return JsonResponse({'status': 'idle'})
        
    # Quando concluído, adicionamos estatísticas reais do banco
    if data.get('status') == 'done':
        from core.models import Imovel, ImagemImovel
        total_imoveis = Imovel.objects.count()
        print(f"DEBUG api_import_status: Imovel.objects.count() = {total_imoveis}")
        if total_imoveis == 0 and data.get('total'):
            total_imoveis = data.get('total')
            print(f"DEBUG api_import_status: using data.get('total') = {total_imoveis}")
            
        total_fotos = ImagemImovel.objects.count() + total_imoveis # principal + galeria
        
        # Se total_fotos for 0 mas tivermos imoveis importados, fazer uma estimativa base
        if total_fotos == total_imoveis and total_imoveis > 0:
            total_fotos = total_imoveis * 5 # Estimativa de 5 fotos por imóvel importado
            
        # Estimativa de armazenamento: ~500KB por foto (em GB)
        gb_used = (total_fotos * 0.5) / 1024
        
        # Lógica real que puxa o gb_limit real do Tenant/Assinatura
        tenant = request.tenant
        gb_limit = 5.0 if tenant.plano_ativo == 'boutique' else 10.0
        gb_limit += tenant.gb_extra
        
        data['stats'] = {
            'total_imoveis': total_imoveis,
            'gb_used': round(gb_used, 2),
            'gb_limit': float(gb_limit)
        }
        print(f"DEBUG api_import_status: returning stats = {data['stats']}")
        
    return JsonResponse(data)

@login_required
def api_import_clear(request):
    """ Limpa o status de importação do cache (para esconder o banner) """
    tenant_schema = request.tenant.schema_name
    cache_key = f'sync_{tenant_schema}'
    cache.delete(cache_key)
    return JsonResponse({'status': 'ok'})

@login_required
def crm_marketing(request):
    """ Exibe o cartão de visita digital e QR Code para a imobiliária """
    tenant = request.tenant
    
    # Monta a URL pública (ajuste conforme seu schema de tenant: ex. imob.dsprime.org)
    # Supondo que a imobiliária acesse pela raiz '/' ou '/imoveis/' do domínio dela
    # Aqui vamos usar o domínio configurado no tenant ou montar via requisição
    dominios = tenant.domains.all()
    if dominios.exists():
        domain_str = dominios.first().domain
        protocol = 'https' if request.is_secure() else 'http'
        public_url = f"{protocol}://{domain_str}/imoveis/"
    else:
        public_url = request.build_absolute_uri('/imoveis/')
        
    context = {
        'public_url': public_url
    }
    return render(request, 'core/crm/marketing.html', context)
