from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
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
    destaques_lancamento = Imovel.objects.filter(finalidade='lancamento', em_destaque=True).order_by('-data_atualizacao')[:3]
    if not destaques_lancamento:
        destaques_lancamento = Imovel.objects.filter(finalidade='lancamento').order_by('-data_atualizacao')[:3]

    destaques_revenda = Imovel.objects.filter(finalidade='revenda', em_destaque=True).order_by('-data_atualizacao')[:3]
    if not destaques_revenda:
        destaques_revenda = Imovel.objects.filter(finalidade='revenda').order_by('-data_atualizacao')[:3]

    destaques_aluguel = Imovel.objects.filter(finalidade='aluguel', em_destaque=True).order_by('-data_atualizacao')[:3]
    if not destaques_aluguel:
        destaques_aluguel = Imovel.objects.filter(finalidade='aluguel').order_by('-data_atualizacao')[:3]
    
    bairros = Bairro.objects.all().order_by('nome')
    ultimos_posts = PostBlog.objects.all().order_by('-data_publicacao')[:3]
    context = {
        'tenant': request.tenant,
        'destaques_lancamento': destaques_lancamento,
        'destaques_revenda': destaques_revenda,
        'destaques_aluguel': destaques_aluguel,
        'bairros': bairros, 
        'ultimos_posts': ultimos_posts
    }
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
    if not request.tenant.exibir_equipe:
        from django.http import Http404
        raise Http404("Página não encontrada")
        
    corretores = Corretor.objects.filter(exibir_no_site=True)
    conteudo = {
        'titulo': request.tenant.titulo_equipe or 'Nossa Equipe', 
        'subtitulo': request.tenant.subtitulo_equipe or 'Especialistas dedicados a encontrar o imóvel ideal para você.'
    }
    return render(request, 'core/lista_corretores.html', {'corretores': corretores, 'conteudo': conteudo})

from django.core.mail import send_mail
from django.conf import settings

def contato(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            
            # Envia o e-mail para a imobiliária
            if hasattr(request, 'tenant') and getattr(request.tenant, 'empresa_email', None):
                subject = f"Novo Contato no Site: {lead.nome}"
                message = f"Olá, equipe {request.tenant.nome}!\n\nVocê recebeu um novo contato através do seu site.\n\nDados do Lead:\nNome: {lead.nome}\nEmail: {lead.email}\nTelefone: {lead.telefone}\n\nMensagem:\n{lead.mensagem}\n\nEste lead já está disponível no seu painel Kanban."
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [request.tenant.empresa_email],
                        fail_silently=True,
                    )
                except Exception as e:
                    pass
                    
            return redirect('core:contato_sucesso')
    else:
        form = LeadForm()
    return render(request, 'core/contato.html', {'form': form})

def contato_sucesso(request):
    return render(request, 'core/contato_sucesso.html')

def detalhe_imovel(request, imovel_id):
    imovel = get_object_or_404(Imovel.objects.prefetch_related('imagens_secundarias', 'caracteristicas'), id=imovel_id)
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        mensagem_txt = request.POST.get('mensagem', f'Tenho interesse no imóvel: {imovel.titulo}')
        
        # Cria o Lead no Kanban
        lead = Lead.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            mensagem=mensagem_txt,
            imovel=imovel,
            corretor=imovel.corretor, # Associa ao corretor do imóvel, se houver
            status='novo'
        )
        
        # Envia e-mail para a imobiliária
        if hasattr(request, 'tenant') and getattr(request.tenant, 'empresa_email', None):
            subject = f"Novo Lead (Imóvel): {lead.nome}"
            message = f"Olá, equipe {request.tenant.nome}!\n\nUm novo cliente demonstrou interesse no imóvel '{imovel.titulo}'.\n\nDados do Lead:\nNome: {lead.nome}\nEmail: {lead.email}\nTelefone: {lead.telefone}\n\nMensagem:\n{lead.mensagem}\n\nEste lead já está disponível no seu painel Kanban."
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.tenant.empresa_email], fail_silently=True)
            except Exception:
                pass
                
        messages.success(request, 'Sua mensagem foi enviada com sucesso! Um consultor entrará em contato em breve.', extra_tags='lead_success')
        return redirect('core:detalhe_imovel', imovel_id=imovel.id)
        
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

def termos_uso(request):
    if hasattr(request, 'tenant') and request.tenant.schema_name == 'public':
        return render(request, 'core/saas_termos_uso.html')
    return render(request, 'core/termos_uso.html')

def politica_privacidade(request):
    if hasattr(request, 'tenant') and request.tenant.schema_name == 'public':
        return render(request, 'core/saas_politica_privacidade.html')
    return render(request, 'core/politica_privacidade.html')

def custom_404(request, exception):
    return render(request, 'core/404.html', status=404)

def saas_landing(request):
    """Landing page para vender o próprio sistema como SaaS"""
    if request.method == 'POST':
        nome = request.POST.get('nome', '')
        email = request.POST.get('email', '')
        telefone = request.POST.get('telefone', '')
        mensagem = request.POST.get('mensagem', '')
        
        subject = f"Novo Contato (ImobGold SaaS): {nome}"
        body = f"Novo lead comercial captado na Landing Page do SaaS!\n\nNome: {nome}\nEmail: {email}\nTelefone: {telefone}\n\nMensagem:\n{mensagem}"
        
        try:
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                ['contato@dsprime.net'],
                fail_silently=True,
            )
        except Exception as e:
            pass
            
        messages.success(request, 'Sua mensagem foi enviada com sucesso! Um de nossos consultores entrará em contato.')
        return redirect('saas_landing')
        
    return render(request, 'core/saas_landing.html')

def lista_blog(request):
    if not request.tenant.exibir_blog:
        from django.http import Http404
        raise Http404("Página não encontrada")
    posts_list = PostBlog.objects.all().order_by('-data_publicacao')
    paginator = Paginator(posts_list, 9) # 9 posts por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'core/blog.html', {'page_obj': page_obj})

def detalhe_post(request, post_id):
    if not request.tenant.exibir_blog:
        from django.http import Http404
        raise Http404("Página não encontrada")
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
def api_leads(request):
    import json
    import datetime
    from django.http import JsonResponse
    from .models import Lead, Corretor
    
    corretor_logado = Corretor.objects.filter(email=request.user.email).first()
    is_owner = request.user.is_superuser or (corretor_logado and corretor_logado.cargo == 'Diretor')
    is_manager = corretor_logado and corretor_logado.cargo == 'Gerente'
    
    leads = Lead.objects.all().order_by('-data_criacao')
    
    if not is_owner:
        if is_manager:
            # Gerente vê seus próprios leads e os da sua equipe
            equipe_ids = Corretor.objects.filter(gerente_responsavel=corretor_logado).values_list('id', flat=True)
            ids_permitidos = list(equipe_ids) + [corretor_logado.id]
            leads = leads.filter(corretor_id__in=ids_permitidos)
        elif corretor_logado:
            # Corretor normal vê apenas seus leads
            leads = leads.filter(corretor_id=corretor_logado.id)
        else:
            # Usuário não é corretor, não é owner, nem gerente (não deve ver nada)
            leads = leads.none()
    leads_data = []
    
    for l in leads:
        leads_data.append({
            'id': l.id,
            'name': l.nome,
            'phone': l.telefone,
            'email': l.email,
            'status': l.status,
            'timestamp': l.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'temperatura': 'morno',
            'idle_days': (datetime.date.today() - l.data_criacao.date()).days,
            'property_title': l.imovel.titulo if l.imovel else 'Lead Genérico',
            'property_url': f"/imovel/{l.imovel.id}/" if l.imovel else "#",
            'observacoes': l.mensagem,
            'corretor_id': l.corretor.id if l.corretor else None,
            'corretor_name': l.corretor.nome if l.corretor else 'Não Atribuído',
        })
        
    return JsonResponse({'leads': leads_data})

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
@login_required
def api_leads_update(request):
    import json
    import datetime
    from django.http import JsonResponse
    from .models import Lead, Corretor
    if request.method == 'POST':
        data = json.loads(request.body)
        lead_id = data.get('lead_id') or data.get('id')
        status = data.get('status')
        observacoes = data.get('observacoes')
        
        if lead_id and status:
            lead = Lead.objects.filter(id=lead_id).first()
            if lead:
                lead.status = status
                if observacoes and observacoes.strip() != '':
                    # Identificar o autor da nota
                    corretor = Corretor.objects.filter(email=request.user.email).first()
                    nome_autor = corretor.nome if corretor else (request.user.first_name or request.user.username)
                    
                    data_str = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
                    entry = f"[{data_str} - {nome_autor}]: {observacoes}"
                    if lead.mensagem:
                        lead.mensagem += '\n' + entry
                    else:
                        lead.mensagem = entry
                        
                if status == 'fechado' and 'valor_venda' in data:
                    try:
                        valor_venda = float(data.get('valor_venda', 0))
                        lead.valor_venda = valor_venda
                        
                        imobiliaria = request.tenant
                        
                        # Comissão total recebida pela Imobiliária
                        comissao_total = (valor_venda * float(imobiliaria.comissao_padrao)) / 100
                        lead.comissao_total = comissao_total
                        
                        # Distribuição
                        comissao_distribuida = 0.0
                        
                        if lead.corretor:
                            vendedor = lead.corretor
                            
                            # 1. Comissão Direta (todos ganham quando vendem)
                            lead.comissao_gerada = (valor_venda * float(vendedor.comissao_venda_direta)) / 100
                            comissao_distribuida += lead.comissao_gerada
                            
                            # Se o próprio vendedor for Diretor, ele acumula gerente e diretor
                            if vendedor.cargo == 'Diretor':
                                lead.comissao_gerente = (valor_venda * float(vendedor.comissao_equipe)) / 100
                                lead.comissao_diretor = (valor_venda * float(vendedor.comissao_equipe)) / 100
                                comissao_distribuida += lead.comissao_gerente + lead.comissao_diretor
                                
                            # Se o próprio vendedor for Gerente, ele acumula gerente
                            elif vendedor.cargo == 'Gerente':
                                lead.comissao_gerente = (valor_venda * float(vendedor.comissao_equipe)) / 100
                                comissao_distribuida += lead.comissao_gerente
                                
                                # E paga o Diretor acima dele (se houver)
                                if vendedor.gerente_responsavel and vendedor.gerente_responsavel.cargo == 'Diretor':
                                    lead.comissao_diretor = (valor_venda * float(vendedor.gerente_responsavel.comissao_equipe)) / 100
                                    comissao_distribuida += lead.comissao_diretor
                                    
                            # Se o vendedor for Corretor
                            else:
                                if vendedor.gerente_responsavel:
                                    superior = vendedor.gerente_responsavel
                                    
                                    if superior.cargo == 'Diretor':
                                        # Diretor gerenciando o corretor diretamente ganha como Gerente e Diretor
                                        lead.comissao_gerente = (valor_venda * float(superior.comissao_equipe)) / 100
                                        lead.comissao_diretor = (valor_venda * float(superior.comissao_equipe)) / 100
                                        comissao_distribuida += lead.comissao_gerente + lead.comissao_diretor
                                    else: # superior é Gerente
                                        lead.comissao_gerente = (valor_venda * float(superior.comissao_equipe)) / 100
                                        comissao_distribuida += lead.comissao_gerente
                                        
                                        # Verifica se o Gerente tem Diretor acima
                                        if superior.gerente_responsavel and superior.gerente_responsavel.cargo == 'Diretor':
                                            diretor = superior.gerente_responsavel
                                            lead.comissao_diretor = (valor_venda * float(diretor.comissao_equipe)) / 100
                                            comissao_distribuida += lead.comissao_diretor
                                        else:
                                            # Se não tem na cadeia, pega o primeiro Diretor da imobiliária (Dono)
                                            diretor_geral = Corretor.objects.filter(cargo='Diretor').first()
                                            if diretor_geral:
                                                lead.comissao_diretor = (valor_venda * float(diretor_geral.comissao_equipe)) / 100
                                                comissao_distribuida += lead.comissao_diretor
                                else:
                                    # Corretor sem gerente. Paga pro primeiro Diretor como Gerente e Diretor?
                                    # Ou apenas como Diretor? Vamos pagar Gerente e Diretor pro Dono
                                    diretor_geral = Corretor.objects.filter(cargo='Diretor').first()
                                    if diretor_geral:
                                        lead.comissao_gerente = (valor_venda * float(diretor_geral.comissao_equipe)) / 100
                                        lead.comissao_diretor = (valor_venda * float(diretor_geral.comissao_equipe)) / 100
                                        comissao_distribuida += lead.comissao_gerente + lead.comissao_diretor
                                        
                        # 4. Receita Líquida da Casa
                        lead.comissao_imobiliaria = lead.comissao_total - comissao_distribuida
                    except ValueError:
                        pass
                elif status in ['lixeira', 'arquivado']:
                    pass # Resetting could go here if needed, but not strictly required
                        
                lead.save()
                return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@csrf_exempt
@login_required
def api_leads_update_corretor(request):
    import json
    from django.http import JsonResponse
    if request.method == 'POST':
        data = json.loads(request.body)
        lead_id = data.get('lead_id') or data.get('id')
        corretor_id = data.get('corretor_id')
        if lead_id:
            lead = Lead.objects.filter(id=lead_id).first()
            if lead:
                lead.corretor_id = corretor_id if corretor_id else None
                lead.save()
                return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def crm_gaveta(request):
    """ CRM Gaveta & Arquivo Morto """
    corretor_logado = Corretor.objects.filter(email=request.user.email).first()
    is_owner = request.user.is_superuser or (corretor_logado and corretor_logado.cargo == 'Diretor')
    is_manager = corretor_logado and corretor_logado.cargo == 'Gerente'
    
    leads = Lead.objects.all().order_by('-data_criacao')
    
    if not is_owner:
        if is_manager:
            equipe_ids = Corretor.objects.filter(gerente_responsavel=corretor_logado).values_list('id', flat=True)
            ids_permitidos = list(equipe_ids) + [corretor_logado.id]
            leads = leads.filter(corretor_id__in=ids_permitidos)
        elif corretor_logado:
            leads = leads.filter(corretor_id=corretor_logado.id)
        else:
            leads = leads.none()
            
    if is_owner or is_manager:
        leads = leads.filter(status__in=['standby', 'arquivado', 'lixeira'])
    else:
        leads = leads.filter(status='standby')
        
    # Calcular dias restantes na lixeira
    import datetime
    from django.utils import timezone
    now = timezone.now()
    for lead in leads:
        if lead.status == 'lixeira':
            # fallback to data_criacao
            base_date = lead.data_criacao
            dias_na_lixeira = (now - base_date).days
            lead.dias_para_excluir = max(0, 40 - dias_na_lixeira)
            
    return render(request, 'core/crm/gaveta.html', {
        'is_owner': is_owner,
        'is_gerente': is_manager,
        'leads': leads
    })


@login_required
def crm_kanban(request):
    """ CRM Kanban View for the Tenant """
    # Força a troca de senha padrão no primeiro acesso
    if request.user.is_authenticated and request.user.check_password('imob123!'):
        from django.contrib import messages
        messages.warning(request, "Por favor, altere a senha padrão de acesso por motivos de segurança.")
        return redirect('account_change_password')
        
    corretor_logado = Corretor.objects.filter(email=request.user.email).first()
    is_owner = request.user.is_superuser or (corretor_logado and corretor_logado.cargo == 'Diretor')
    is_manager = corretor_logado and corretor_logado.cargo == 'Gerente'
    
    leads = Lead.objects.all().order_by('-data_criacao')
    corretores = Corretor.objects.all()
    
    if not is_owner:
        if is_manager:
            equipe_ids = Corretor.objects.filter(gerente_responsavel=corretor_logado).values_list('id', flat=True)
            ids_permitidos = list(equipe_ids) + [corretor_logado.id]
            leads = leads.filter(corretor_id__in=ids_permitidos)
            corretores = Corretor.objects.filter(id__in=ids_permitidos)
        elif corretor_logado:
            leads = leads.filter(corretor_id=corretor_logado.id)
            corretores = Corretor.objects.filter(id=corretor_logado.id)
        else:
            leads = leads.none()
            corretores = Corretor.objects.none()
    
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
        
    from django.db.models import Sum
    import datetime
    
    # Filtro de Mês/Ano para as comissões
    meses_opcoes = []
    meses_extenso = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    hoje = datetime.date.today()
    
    # Gera os últimos 6 meses até o mes atual
    for i in range(6):
        d = (hoje.replace(day=1) - datetime.timedelta(days=i*30)).replace(day=1)
        meses_opcoes.append(f"{meses_extenso[d.month - 1]} {d.year}")
        
    mes_filtro = request.GET.get('mes', f"{meses_extenso[hoje.month - 1]} {hoje.year}")
    
    try:
        nome_mes, ano_str = mes_filtro.split()
        mes_idx = meses_extenso.index(nome_mes) + 1
        ano_idx = int(ano_str)
        # Considera fechados E arquivados (que tiveram venda > 0)
        from django.db.models import Q
        leads_fechados = leads.filter(
            Q(status='fechado') | Q(status='arquivado', valor_venda__gt=0),
            data_criacao__year=ano_idx, 
            data_criacao__month=mes_idx
        )
    except:
        from django.db.models import Q
        leads_fechados = leads.filter(Q(status='fechado') | Q(status='arquivado', valor_venda__gt=0))
        
    total_vendido = leads_fechados.aggregate(Sum('valor_venda'))['valor_venda__sum'] or 0
    
    comissao_imobiliaria = leads_fechados.aggregate(Sum('comissao_imobiliaria'))['comissao_imobiliaria__sum'] or 0
    c_gerada = leads_fechados.aggregate(Sum('comissao_gerada'))['comissao_gerada__sum'] or 0
    c_gerente = leads_fechados.aggregate(Sum('comissao_gerente'))['comissao_gerente__sum'] or 0
    c_diretor = leads_fechados.aggregate(Sum('comissao_diretor'))['comissao_diretor__sum'] or 0
    comissao_distribuida = c_gerada + c_gerente + c_diretor
    
    context = {
        'leads': leads,
        'corretores': corretores,
        'is_owner': is_owner,
        'is_gerente': is_manager,
        'is_diamond': tenant.plano_ativo == 'corporate',
        'total_vendido': total_vendido,
        'minha_comissao': comissao_imobiliaria, # para o dono, a comissao dele é a liquida da casa
        'comissao_distribuida': comissao_distribuida,
        'c_gerada': c_gerada,
        'c_gerente': c_gerente,
        'c_diretor': c_diretor,
        'dias_restantes': dias_restantes,
        'gb_used': round(tenant.get_gb_used(), 2),
        'gb_limit': tenant.get_gb_limit(),
        'gb_perc': tenant.get_gb_percentage(),
        'total_imoveis': total_imoveis,
        'imoveis_lancamento': imoveis_lancamento,
        'imoveis_revenda': imoveis_revenda,
        'data_ultima_carga': data_ultima_carga,
        'mes_filtro': mes_filtro,
        'meses_opcoes': meses_opcoes,
    }
    return render(request, 'core/crm/kanban.html', context)

@login_required
def crm_relatorios(request):
    from core.models import Lead, Corretor
    from django.db.models import Sum, Count, Q
    from django.db.models.functions import TruncMonth
    import datetime
    
    tenant = request.tenant
    corretor_logado = Corretor.objects.filter(email=request.user.email).first()
    is_owner = request.user.is_superuser or (corretor_logado and corretor_logado.cargo == 'Diretor')
    is_manager = corretor_logado and corretor_logado.cargo == 'Gerente'
    
    if not is_owner and not is_manager:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Apenas gestores e proprietários têm acesso a relatórios gerenciais.")

    # Base de Leads Fechados
    leads_fechados = Lead.objects.filter(Q(status='fechado') | Q(status='arquivado', valor_venda__gt=0)).order_by('data_criacao')
    
    # Se não for dono, gerente vê apenas a sua equipe
    if not is_owner and is_manager:
        equipe_ids = Corretor.objects.filter(gerente_responsavel=corretor_logado).values_list('id', flat=True)
        ids_permitidos = list(equipe_ids) + [corretor_logado.id]
        leads_fechados = leads_fechados.filter(corretor_id__in=ids_permitidos)

    # Filtro de Ano e Mês
    ano_selecionado = request.GET.get('ano')
    mes_selecionado = request.GET.get('mes')
    
    if ano_selecionado:
        leads_fechados = leads_fechados.filter(data_criacao__year=ano_selecionado)
    if mes_selecionado:
        leads_fechados = leads_fechados.filter(data_criacao__month=mes_selecionado)

    vgv_total = sum(l.valor_venda for l in leads_fechados)
    receita_casa = sum(l.comissao_imobiliaria for l in leads_fechados)
    total_vendas = leads_fechados.count()
    
    vendas_por_mes = leads_fechados.annotate(
        month=TruncMonth('data_criacao')
    ).values('month').annotate(
        total_vgv=Sum('valor_venda'),
        count=Count('id')
    ).order_by('month')
    
    labels_meses = []
    dados_vgv_meses = []
    for v in vendas_por_mes:
        mes_str = v['month'].strftime("%b/%Y") if v['month'] else "N/A"
        labels_meses.append(mes_str)
        dados_vgv_meses.append(float(v['total_vgv'] or 0))

    ranking_corretores_dict = {}
    for lead in leads_fechados:
        corretor_nome = lead.corretor.nome if lead.corretor else "Lead da Casa (Sem Corretor)"
        if corretor_nome not in ranking_corretores_dict:
            ranking_corretores_dict[corretor_nome] = {'vendas': 0, 'vgv': 0}
        ranking_corretores_dict[corretor_nome]['vendas'] += 1
        ranking_corretores_dict[corretor_nome]['vgv'] += float(lead.valor_venda)
        
    ranking_corretores = sorted([
        {'nome': k, 'vendas': v['vendas'], 'vgv': v['vgv']} for k, v in ranking_corretores_dict.items()
    ], key=lambda x: x['vgv'], reverse=True)

    ranking_equipes_dict = {}
    for lead in leads_fechados:
        gerente_nome = "Venda Direta / Sem Equipe"
        if lead.corretor and lead.corretor.gerente_responsavel:
            gerente_nome = lead.corretor.gerente_responsavel.nome
            
        if gerente_nome not in ranking_equipes_dict:
            ranking_equipes_dict[gerente_nome] = {'vendas': 0, 'vgv': 0}
        ranking_equipes_dict[gerente_nome]['vendas'] += 1
        ranking_equipes_dict[gerente_nome]['vgv'] += float(lead.valor_venda)

    ranking_equipes = sorted([
        {'nome': k, 'vendas': v['vendas'], 'vgv': v['vgv']} for k, v in ranking_equipes_dict.items()
    ], key=lambda x: x['vgv'], reverse=True)

    context = {
        'tenant': tenant,
        'vgv_total': vgv_total,
        'receita_casa': receita_casa,
        'total_vendas': total_vendas,
        'labels_meses': labels_meses,
        'dados_vgv_meses': dados_vgv_meses,
        'ranking_corretores': ranking_corretores,
        'ranking_equipes': ranking_equipes,
        'ano_selecionado': ano_selecionado,
        'mes_selecionado': mes_selecionado,
    }
    return render(request, 'core/crm/relatorios.html', context)

@login_required
def assinatura(request):
    tenant = request.tenant
    
    # Busca os price IDs do env
    from django.conf import settings
    import stripe
    import time
    from datetime import datetime
    
    if request.GET.get('checkout') == 'success':
        try:
            # Fallback local sync se o webhook falhar
            if not tenant.stripe_customer_id:
                customers = stripe.Customer.list(email=request.user.email, limit=1)
                if customers.data:
                    tenant.stripe_customer_id = customers.data[0].id
                    tenant.save()
            
            if tenant.stripe_customer_id:
                subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='active')
                total_gb_extra = 0
                
                PRICE_10GB = getattr(settings, 'STRIPE_PRICE_10GB', '')
                PRICE_50GB = getattr(settings, 'STRIPE_PRICE_50GB', '')
                PRICE_CORPORATE = getattr(settings, 'STRIPE_PRICE_CORPORATE', '')
                PRICE_BOUTIQUE = getattr(settings, 'STRIPE_PRICE_BOUTIQUE', '')
                
                for sub in subs.auto_paging_iter():
                    if hasattr(sub, 'items') and hasattr(sub.items, 'data'):
                        for item in sub.items.data:
                            pid = item.price.id
                            qty = item.quantity
                            if pid == PRICE_10GB:
                                total_gb_extra += (10 * qty)
                            elif pid == PRICE_50GB:
                                total_gb_extra += (50 * qty)
                            elif pid == PRICE_CORPORATE:
                                tenant.plano_ativo = 'corporate'
                            elif pid == PRICE_BOUTIQUE:
                                tenant.plano_ativo = 'boutique'
                
                tenant.gb_extra = total_gb_extra
                tenant.status_assinatura = 'active'
                tenant.save()
        except Exception as e:
            print(f"Erro no fallback sync do stripe: {str(e)}")

    
    prices = {
        'boutique': getattr(settings, 'STRIPE_PRICE_BOUTIQUE', ''),
        'corporate': getattr(settings, 'STRIPE_PRICE_CORPORATE', ''),
        '10gb': getattr(settings, 'STRIPE_PRICE_10GB', ''),
        '50gb': getattr(settings, 'STRIPE_PRICE_50GB', '')
    }
    
    is_trialing = False
    trial_days_left = 0
    
    if tenant.stripe_customer_id:
        try:
            subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='trialing', limit=1)
            for sub in subs.auto_paging_iter():
                is_trialing = True
                trial_end = getattr(sub, 'trial_end', None)
                if trial_end:
                    now = int(time.time())
                    diff = trial_end - now
                    trial_days_left = max(0, int(diff / 86400))
                break
        except Exception:
            pass
    
    context = {
        'tenant': tenant,
        'gb_used': round(tenant.get_gb_used(), 2),
        'gb_limit': tenant.get_gb_limit(),
        'gb_perc': tenant.get_gb_percentage(),
        'prices': prices,
        'is_corporate': tenant.plano_ativo == 'corporate',
        'is_trialing': is_trialing,
        'trial_days_left': trial_days_left,
    }
    
    setup_intent_id = request.GET.get('setup_intent')
    if setup_intent_id and request.GET.get('cartao') == 'atualizado':
        try:
            intent = stripe.SetupIntent.retrieve(setup_intent_id)
            if intent.payment_method:
                # Set it as the default payment method for the customer
                stripe.Customer.modify(
                    tenant.stripe_customer_id,
                    invoice_settings={'default_payment_method': intent.payment_method}
                )
                
                # Optionally, update all active subscriptions to use this payment method
                subs = stripe.Subscription.list(customer=tenant.stripe_customer_id, status='active')
                for sub in subs.auto_paging_iter():
                    stripe.Subscription.modify(
                        sub.id,
                        default_payment_method=intent.payment_method
                    )
        except Exception as e:
            print(f"Erro ao setar cartão padrão: {e}")
            
        from django.contrib import messages
        messages.success(request, 'Cartão de crédito atualizado com sucesso!')
        
    return render(request, 'core/crm/assinatura.html', context)

@login_required
def crm_imoveis(request):
    """ View to manage the property stock (Estoque) in the CRM """
    from django.db.models import Q
    from core.models import Bairro
    
    query = Imovel.objects.all().order_by('-data_cadastro')
    
    # Filters
    busca = request.GET.get('busca', '')
    if busca:
        query = query.filter(Q(titulo__icontains=busca) | Q(codigo__icontains=busca) if hasattr(Imovel, 'codigo') else Q(titulo__icontains=busca))
        
    finalidade = request.GET.get('finalidade', '')
    if finalidade:
        query = query.filter(finalidade=finalidade)
        
    bairro_id = request.GET.get('bairro', '')
    if bairro_id:
        query = query.filter(bairro_id=bairro_id)
        
    destaque = request.GET.get('destaque', '')
    if destaque == '1':
        query = query.filter(em_destaque=True)
        
    # Actions (Delete or Toggle Destaque)
    if request.method == 'POST':
        acao = request.POST.get('acao')
        imovel_id = request.POST.get('imovel_id')
        try:
            imovel = Imovel.objects.get(id=imovel_id)
            if acao == 'excluir':
                imovel.delete()
                messages.success(request, 'Imóvel excluído com sucesso!')
            elif acao == 'toggle_destaque':
                imovel.em_destaque = not imovel.em_destaque
                imovel.save()
                messages.success(request, f'Destaque {"ativado" if imovel.em_destaque else "removido"} com sucesso!')
            return redirect(request.get_full_path())
        except Imovel.DoesNotExist:
            messages.error(request, 'Imóvel não encontrado.')
            
    # Pagination? Let's just limit to 100 or use standard pagination.
    from django.core.paginator import Paginator
    paginator = Paginator(query, 30)
    page_number = request.GET.get('page')
    imoveis = paginator.get_page(page_number)
    
    bairros = Bairro.objects.all().order_by('nome')
    
    return render(request, 'core/crm/imoveis_estoque.html', {
        'imoveis': imoveis,
        'bairros': bairros,
        'busca': busca,
        'finalidade': finalidade,
        'bairro_id': bairro_id,
        'destaque': destaque
    })

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
@user_passes_test(lambda u: u.is_staff)
@login_required
def crm_clientes(request):
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'editar_telefone':
            profile_id = request.POST.get('profile_id')
            novo_telefone = request.POST.get('telefone')
            try:
                profile = Profile.objects.get(id=profile_id)
                profile.telefone = novo_telefone
                profile.save()
                messages.success(request, 'Telefone atualizado com sucesso!')
            except Profile.DoesNotExist:
                messages.error(request, 'Cliente não encontrado.')
                
        elif acao == 'novo_cliente':
            nome = request.POST.get('nome')
            email = request.POST.get('email')
            telefone = request.POST.get('telefone')
            
            # Criar um Lead manualmente (vai pro Kanban)
            Lead.objects.create(
                nome=nome,
                email=email,
                telefone=telefone,
                status='novo',
                mensagem='Cliente cadastrado manualmente via CRM.'
            )
            messages.success(request, 'Cliente cadastrado com sucesso! Ele já está disponível no seu Kanban.')
            
        return redirect('core:crm_clientes')

    # Todos os Profiles (cadastrados) do Tenant
    clientes = Profile.objects.select_related('user').all().order_by('-id')
    return render(request, 'core/crm/clientes.html', {'clientes': clientes})

@login_required
@user_passes_test(lambda u: u.is_staff)
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

@login_required
def configuracoes_site(request):
    if request.method == 'POST':
        tenant = request.tenant
        tenant.nome = request.POST.get('nome', tenant.nome)
        
        if 'logo' in request.FILES:
            tenant.logo = request.FILES['logo']
            
        tenant.exibir_equipe = request.POST.get('exibir_equipe') == 'on'
        tenant.titulo_equipe = request.POST.get('titulo_equipe', '')
        tenant.subtitulo_equipe = request.POST.get('subtitulo_equipe', '')
        tenant.exibir_blog = request.POST.get('exibir_blog') == 'on'
        tenant.texto_quem_somos = request.POST.get('texto_quem_somos', '')
        tenant.sobre_titulo = request.POST.get('sobre_titulo', '')
        tenant.sobre_subtitulo = request.POST.get('sobre_subtitulo', '')
        tenant.sobre_citacao = request.POST.get('sobre_citacao', '')
        tenant.sobre_missao = request.POST.get('sobre_missao', '')
        tenant.sobre_visao = request.POST.get('sobre_visao', '')
        
        tenant.home_hero_tag = request.POST.get('home_hero_tag', '')
        tenant.home_hero_titulo = request.POST.get('home_hero_titulo', '')
        tenant.home_hero_destaque = request.POST.get('home_hero_destaque', '')
        tenant.home_hero_subtitulo = request.POST.get('home_hero_subtitulo', '')
        
        tenant.home_hero_bg_preset = request.POST.get('home_hero_bg_preset', 'preset_1')
        if 'home_hero_bg_custom' in request.FILES:
            tenant.home_hero_bg_custom = request.FILES['home_hero_bg_custom']
            tenant.home_hero_bg_preset = 'custom'
        
        tenant.home_manifesto_titulo = request.POST.get('home_manifesto_titulo', '')
        tenant.home_manifesto_destaque = request.POST.get('home_manifesto_destaque', '')
        tenant.home_manifesto_texto = request.POST.get('home_manifesto_texto', '')
        
        tenant.telefone = request.POST.get('telefone', '')
        tenant.empresa_email = request.POST.get('empresa_email', '')
        
        tenant.cep = request.POST.get('cep', '')
        tenant.rua = request.POST.get('rua', '')
        tenant.numero = request.POST.get('numero', '')
        tenant.complemento = request.POST.get('complemento', '')
        tenant.bairro = request.POST.get('bairro', '')
        tenant.cidade = request.POST.get('cidade', '')
        tenant.uf = request.POST.get('uf', '')
        
        tenant.tipo_documento = request.POST.get('tipo_documento', 'CNPJ')
        tenant.cpf_cnpj = request.POST.get('cpf_cnpj', '')
        
        tenant.empresa_creci = request.POST.get('empresa_creci', '')
        tenant.empresa_instagram = request.POST.get('empresa_instagram', '')
        tenant.empresa_facebook = request.POST.get('empresa_facebook', '')
        
        tenant.save()
        messages.success(request, 'Configurações salvas com sucesso!')
        
        active_tab = request.POST.get('active_tab', '')
        from django.urls import reverse
        url = reverse('core:configuracoes_site')
        if active_tab:
            return redirect(f"{url}#{active_tab}")
        return redirect('core:configuracoes_site')
    return render(request, 'core/crm/configuracoes_site.html')

@login_required
def crm_blog(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            PostBlog.objects.create(
                titulo=request.POST.get('titulo', ''),
                resumo=request.POST.get('resumo', ''),
                tipo_conteudo=request.POST.get('tipo_conteudo', 'link'),
                link_url=request.POST.get('link_url', ''),
                embed_code=request.POST.get('embed_code', ''),
                imagem_card=request.FILES.get('imagem_card'),
                arquivo=request.FILES.get('arquivo')
            )
            messages.success(request, 'Artigo publicado com sucesso!')
        elif action == 'edit':
            post_id = request.POST.get('post_id')
            post = PostBlog.objects.filter(id=post_id).first()
            if post:
                post.titulo = request.POST.get('titulo', post.titulo)
                post.resumo = request.POST.get('resumo', post.resumo)
                post.tipo_conteudo = request.POST.get('tipo_conteudo', post.tipo_conteudo)
                post.link_url = request.POST.get('link_url', post.link_url)
                post.embed_code = request.POST.get('embed_code', post.embed_code)
                if 'imagem_card' in request.FILES:
                    post.imagem_card = request.FILES['imagem_card']
                if 'arquivo' in request.FILES:
                    post.arquivo = request.FILES['arquivo']
                post.save()
                messages.success(request, 'Artigo atualizado com sucesso!')
        elif action == 'delete':
            post_id = request.POST.get('post_id')
            PostBlog.objects.filter(id=post_id).delete()
            messages.success(request, 'Artigo excluído com sucesso!')
        return redirect('core:crm_blog')
    
    posts = PostBlog.objects.all().order_by('-data_publicacao')
    return render(request, 'core/crm/blog_lista.html', {'posts': posts})

@login_required
def crm_equipe(request):
    tenant = request.tenant
    is_owner = True # For now, assume logged in user in CRM is owner
    is_gerente = False
    
    if tenant.plano_ativo != 'corporate' and not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("A funcionalidade Gestão de Equipe (Multi-Corretores) é exclusiva do Plano Diamond. Faça o upgrade para utilizar.")
        
    if request.method == 'POST':
        corretor_id = request.POST.get('corretor_id')
        nome = request.POST.get('nome')
        whatsapp = request.POST.get('whatsapp')
        email = request.POST.get('email')
        
        bio = request.POST.get('bio', '')
        foto = request.FILES.get('foto')
        
        role = request.POST.get('role', 'Corretor')
        gerente_id = request.POST.get('gerente_id')
        gerente = None
        if gerente_id:
            gerente = Corretor.objects.filter(id=gerente_id).first()
        
        if nome and email:
            if role == 'Diretor':
                comissao_venda_direta = tenant.taxa_corretor + tenant.taxa_gerente + tenant.taxa_diretor
                comissao_equipe = tenant.taxa_diretor
            elif role == 'Gerente':
                comissao_venda_direta = tenant.taxa_corretor + tenant.taxa_gerente
                comissao_equipe = tenant.taxa_gerente
            else:
                comissao_venda_direta = tenant.taxa_corretor
                comissao_equipe = 0.0
                
            from django.contrib.auth.models import User
            from django_tenants.utils import schema_context
            
            # Handle user creation in public schema
            user = None
            with schema_context('public'):
                user = User.objects.filter(email=email).first()
                if not user:
                    username = email.split('@')[0]
                    base_username = username
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{base_username}{counter}"
                        counter += 1
                    user = User.objects.create_user(username=username, email=email, password='imob123!')
                
            if corretor_id:
                from django.shortcuts import get_object_or_404
                corretor = get_object_or_404(Corretor, id=corretor_id)
                corretor.nome = nome
                corretor.telefone = whatsapp
                corretor.email = email
                corretor.bio = bio
                if foto:
                    corretor.foto = foto
                corretor.cargo = role
                corretor.gerente_responsavel = gerente
                corretor.comissao_venda_direta = comissao_venda_direta
                corretor.comissao_equipe = comissao_equipe
                corretor.user = user
                corretor.save()
            else:
                Corretor.objects.create(
                    nome=nome, 
                    telefone=whatsapp,
                    email=email,
                    bio=bio,
                    foto=foto,
                    cargo=role,
                    gerente_responsavel=gerente,
                    comissao_venda_direta=comissao_venda_direta if is_owner else 1.50,
                    comissao_equipe=comissao_equipe if is_owner else 0.30,
                    user=user
                )
            return redirect('core:crm_equipe')
            
    corretores = Corretor.objects.all()
        
    organograma_diretores = Corretor.objects.filter(cargo='Diretor')
    
    organograma_gerentes = []
    gerentes = Corretor.objects.filter(cargo='Gerente')
    for g in gerentes:
        corretores_g = Corretor.objects.filter(gerente_responsavel=g, cargo='Corretor')
        organograma_gerentes.append({'obj': g, 'corretores': corretores_g})
        
    organograma_soltos = Corretor.objects.filter(gerente_responsavel__isnull=True, cargo='Corretor')

    return render(request, 'core/crm/equipe.html', {
        'imobiliaria': tenant, 
        'corretores': corretores,
        'organograma_diretores': organograma_diretores,
        'organograma_gerentes': organograma_gerentes,
        'organograma_soltos': organograma_soltos,
        'is_owner': is_owner,
        'is_gerente': is_gerente
    })

@login_required
def crm_comissoes(request):
    tenant = request.tenant
    is_owner = True
    
    if not is_owner:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Apenas donos ou diretores podem acessar as comissões globais.")
        
    if request.method == 'POST':
        try:
            tenant.comissao_padrao = float(request.POST.get('comissao_padrao', 5.0))
            tenant.taxa_corretor = float(request.POST.get('taxa_corretor', 1.5))
            tenant.taxa_gerente = float(request.POST.get('taxa_gerente', 0.3))
            tenant.taxa_diretor = float(request.POST.get('taxa_diretor', 0.2))
            tenant.save()
            
            Corretor.objects.filter(cargo='Corretor').update(
                comissao_venda_direta=tenant.taxa_corretor,
                comissao_equipe=0.0
            )
            Corretor.objects.filter(cargo='Gerente').update(
                comissao_venda_direta=(tenant.taxa_corretor + tenant.taxa_gerente),
                comissao_equipe=tenant.taxa_gerente
            )
            Corretor.objects.filter(cargo='Diretor').update(
                comissao_venda_direta=(tenant.taxa_corretor + tenant.taxa_gerente + tenant.taxa_diretor),
                comissao_equipe=tenant.taxa_diretor
            )
            from django.contrib import messages
            messages.success(request, "Comissões atualizadas para toda a equipe com sucesso!")
        except ValueError:
            from django.contrib import messages
            messages.error(request, "Valores inválidos.")
            
        return redirect('core:crm_comissoes')

    return render(request, 'core/crm/comissoes.html', {
        'imobiliaria': tenant,
        'is_owner': True,
    })
