from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Imovel, Bairro, Corretor, ConteudoPagina, 
    TipoImovel, Caracteristica, ImagemImovel, Cliente
)
from .forms import LeadForm
from django.db.models import Q, Max, Min
import re
import html
<<<<<<< HEAD
from urllib.parse import quote
=======
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
>>>>>>> ccc3a18a88ff6b2aa19ec88d8c4e0d186a48fc02

def index(request):
    destaques = Imovel.objects.filter(
        finalidade='lancamento', 
        em_destaque=True
    ).order_by('-data_atualizacao')[:3]
    bairros = Bairro.objects.all().order_by('nome')
    context = {
        'destaques': destaques,
        'bairros': bairros
    }
    return render(request, 'core/index.html', context)

def sobre(request):
    try:
        # Usamos o manager .objects do proxy model para garantir o get_or_create
        conteudo, created = ConteudoPagina.objects.get_or_create(
            chave='pagina_sobre',
            defaults={
                'titulo': 'Página Sobre',
                'subtitulo': 'Conteúdo padrão inicial.',
                'corpo': '<p>Este é o conteúdo padrão. Edite no painel de administração.</p>'
            }
        )
    except Exception:
        # Fallback em caso de erro no banco
        conteudo = {
            'titulo': 'Página Sobre',
            'subtitulo': 'Erro ao carregar o conteúdo.',
            'corpo': '<p>Ocorreu um erro ao buscar os dados. Tente novamente mais tarde.</p>'
        }
    return render(request, 'core/sobre.html', {'conteudo': conteudo})

def lista_imoveis(request):
    # Salva a URL da busca na sessão para o botão "Voltar"
    # Apenas salva se for uma página de resultados, não a partir de um imóvel
    if 'imoveis' in request.path:
        request.session['last_search_url'] = request.get_full_path()
    
    imoveis = Imovel.objects.filter(valor__isnull=False).order_by('-data_atualizacao')
    bairros = Bairro.objects.all().order_by('nome')
    tipos_imovel = TipoImovel.objects.all().order_by('nome')
    caracteristicas = Caracteristica.objects.all().order_by('nome')
    filtros_aplicados = request.GET.copy()
    
    finalidade = filtros_aplicados.get('finalidade', 'lancamento')
    if finalidade:
        imoveis = imoveis.filter(finalidade=finalidade)

    categoria = filtros_aplicados.get('categoria')
    if categoria:
        imoveis = imoveis.filter(categoria=categoria)

    query = filtros_aplicados.get('query')
    if query:
        imoveis = imoveis.filter(titulo__icontains=query)

    bairro_id = filtros_aplicados.get('bairro')
    if bairro_id:
        imoveis = imoveis.filter(bairro_id=bairro_id)

    tipos_slugs = filtros_aplicados.getlist('tipo_imovel')
    if tipos_slugs:
        imoveis = imoveis.filter(tipo_imovel__slug__in=tipos_slugs)

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

    features = filtros_aplicados.getlist('features')
    if features:
        for f in features:
            imoveis = imoveis.filter(caracteristicas__nome=f)

    context = {
        'imoveis': imoveis.distinct(), 
        'bairros': bairros,
        'tipos_imovel': tipos_imovel,
        'caracteristicas': caracteristicas,
        'filtros_aplicados': filtros_aplicados,
    }
    return render(request, 'core/lista_imoveis.html', context)

def lista_corretores(request):
    corretores = Corretor.objects.all()
    try:
        conteudo = ConteudoPagina.objects.get(chave='pagina_corretores')
    except ConteudoPagina.DoesNotExist:
        conteudo = {
            'titulo': 'A Nossa Equipa', 
            'subtitulo': 'Especialistas dedicados a encontrar o imóvel que reflete a sua essência.'
        }
    return render(request, 'core/lista_corretores.html', {
        'corretores': corretores, 
        'conteudo': conteudo
    })

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
    
    # Corrige o HTML escapado na descrição
    imovel.descricao = html.unescape(imovel.descricao)

    similares = Imovel.objects.filter(
        bairro=imovel.bairro,
        categoria=imovel.categoria
    ).exclude(id=imovel_id)[:3]

    # Lógica para o botão WhatsApp
    numero_whatsapp = "+5562983188400"
    url_imovel = request.build_absolute_uri()
    mensagem_whatsapp = f"Olá! Tenho interesse neste imóvel: {imovel.titulo}. Pode me dar mais detalhes? Link: {url_imovel}"
    link_whatsapp = f"httpsa//wa.me/{numero_whatsapp}?text={quote(mensagem_whatsapp)}"
    
    # Lógica para o botão "Voltar"
    last_search_url = request.session.get('last_search_url', None)

    context = {
        'imovel': imovel,
        'similares': similares,
        'link_whatsapp': link_whatsapp,
        'last_search_url': last_search_url,
    }
    return render(request, 'core/detalhe_imovel.html', context)
<<<<<<< HEAD
=======

@login_required
def lista_favoritos(request):
    cliente = get_object_or_404(Cliente, user=request.user)
    imoveis = cliente.imoveis_favoritos.all()
    context = {
        'imoveis': imoveis,
    }
    return render(request, 'core/lista_favoritos.html', context)

@login_required
def adicionar_favorito(request, imovel_id):
    imovel = get_object_or_404(Imovel, id=imovel_id)
    cliente, created = Cliente.objects.get_or_create(user=request.user)
    imovel.favoritos.add(cliente)
    return redirect(request.META.get('HTTP_REFERER', 'core:lista_imoveis'))

@login_required
def remover_favorito(request, imovel_id):
    imovel = get_object_or_404(Imovel, id=imovel_id)
    cliente = get_object_or_404(Cliente, user=request.user)
    imovel.favoritos.remove(cliente)
    return redirect(request.META.get('HTTP_REFERER', 'core:lista_imoveis'))

def comparar_imoveis(request):
    imoveis_ids = request.session.get('comparar_imoveis', [])
    imoveis = Imovel.objects.filter(id__in=imoveis_ids)
    context = {
        'imoveis': imoveis,
    }
    return render(request, 'core/comparar_imoveis.html', context)

def update_comparison(request):
    if request.method == 'POST':
        imovel_id = request.POST.get('imovel_id')
        action = request.POST.get('action')

        imoveis_ids = request.session.get('comparar_imoveis', [])

        if action == 'add':
            if imovel_id not in imoveis_ids and len(imoveis_ids) < 3:
                imoveis_ids.append(imovel_id)
        elif action == 'remove':
            if imovel_id in imoveis_ids:
                imoveis_ids.remove(imovel_id)

        request.session['comparar_imoveis'] = imoveis_ids
        return JsonResponse({'status': 'ok', 'count': len(imoveis_ids)})

    return JsonResponse({'status': 'error'}, status=400)
>>>>>>> ccc3a18a88ff6b2aa19ec88d8c4e0d186a48fc02
