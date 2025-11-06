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
    TipoImovel, Caracteristica, ImagemImovel, Profile
)
from django.db.models import Q
import re
import urllib.parse
import html

# --- (views index, sobre - sem mudança) ---
def index(request):
    destaques = Imovel.objects.filter(finalidade='lancamento', em_destaque=True).order_by('-data_atualizacao')[:3]
    bairros = Bairro.objects.all().order_by('nome')
    context = {'destaques': destaques, 'bairros': bairros}
    return render(request, 'core/index.html', context)

def sobre(request):
    try:
        conteudo = ConteudoPagina.objects.get(chave='pagina_sobre')
    except ConteudoPagina.DoesNotExist:
        conteudo = {'titulo': 'Sobre a Lotus Imobiliária', 'subtitulo': 'O seu espaço de renascimento. Clareza e elegância na busca pelo extraordinário.'}
    return render(request, 'core/sobre.html', {'conteudo': conteudo})


# --- VIEW LISTA_IMOVEIS (CORRIGIDA) ---
def lista_imoveis(request):
    request.session['last_search_url'] = request.get_full_path()
    imoveis = Imovel.objects.filter(valor__isnull=False).order_by('-data_atualizacao')
    bairros = Bairro.objects.all().order_by('nome')
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
    
    bairro_id = filtros_aplicados.get('bairro')
    if bairro_id: imoveis = imoveis.filter(bairro_id=bairro_id)
    
    tipos_slugs = filtros_aplicados.getlist('tipo_imovel')
    if tipos_slugs: imoveis = imoveis.filter(tipo_imovel__slug__in=tipos_slugs)
    
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
        
    imoveis_list = imoveis.distinct()
    paginator = Paginator(imoveis_list, 12) 
    page_obj = paginator.get_page(page_number)
    filtros_aplicados_query = filtros_aplicados.urlencode()
    
    context = {
        'page_obj': page_obj, 'filtros_aplicados_query': filtros_aplicados_query, 
        'bairros': bairros, 'tipos_imovel': tipos_imovel, 
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
    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'core/minha_conta.html', context)

def favoritos(request):
    imoveis_favoritos = []
    if request.user.is_authenticated:
        imoveis_favoritos = request.user.profile.favoritos.all().order_by('-data_atualizacao')
    else:
        ids_str = request.GET.get('ids', '')
        if ids_str:
            try:
                ids_list = [int(id) for id in ids_str.split(',')]
                imoveis_favoritos = Imovel.objects.filter(id__in=ids_list)
                imoveis_dict = {imovel.id: imovel for imovel in imoveis_favoritos}
                imoveis_favoritos = [imoveis_dict[id] for id in ids_list if id in imoveis_dict]
            except ValueError:
                pass
    last_search_url = request.session.get('last_search_url', '/imoveis/')
    context = {'imoveis': imoveis_favoritos, 'last_search_url': last_search_url}
    return render(request, 'core/favoritos.html', context)

@login_required
@require_POST
def toggle_favorito(request):
    try:
        data = json.loads(request.body)
        imovel_id = data.get('id')
        action = data.get('action')

        if not imovel_id or action not in ['add', 'remove']:
            return JsonResponse({'status': 'error', 'message': 'Dados inválidos'}, status=400)

        imovel = get_object_or_404(Imovel, id=imovel_id)
        profile = request.user.profile

        if action == 'add':
            profile.favoritos.add(imovel)
        else:
            profile.favoritos.remove(imovel)

        return JsonResponse({'status': 'success', 'total': profile.favoritos.count()})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def sync_favoritos(request):
    try:
        data = json.loads(request.body)
        local_ids = set(map(str, data.get('ids', [])))

        profile = request.user.profile
        server_imoveis = profile.favoritos.all()
        server_ids = set(map(str, server_imoveis.values_list('id', flat=True)))

        combined_ids = local_ids.union(server_ids)

        imoveis_to_add = Imovel.objects.filter(id__in=combined_ids)
        profile.favoritos.set(imoveis_to_add)

        updated_server_ids = list(profile.favoritos.values_list('id', flat=True))

        return JsonResponse({'status': 'success', 'server_favorites': updated_server_ids})
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid request: {e}'}, status=400)
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