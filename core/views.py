from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Imovel, Bairro, Corretor, ConteudoPagina, 
    TipoImovel, Caracteristica, ImagemImovel
)
from .forms import LeadForm
from django.db.models import Q, Max, Min
import re
import urllib.parse
import html

# --- FUNÇÃO ATUALIZADA ---
def index(request):
    destaques = Imovel.objects.filter(
        finalidade='lancamento', 
        em_destaque=True
    ).order_by('-data_atualizacao')[:3]
    
    # NOVO: Buscar todos os bairros para o dropdown da home
    bairros = Bairro.objects.all().order_by('nome')
    
    context = {
        'destaques': destaques,
        'bairros': bairros # NOVO: Adicionar bairros ao contexto
    }
    return render(request, 'core/index.html', context)

def sobre(request):
    return render(request, 'core/sobre.html')

def lista_imoveis(request):
    
    # Salva a URL da busca atual na sessão para o botão "voltar"
    request.session['last_search_url'] = request.get_full_path()

    imoveis = Imovel.objects.filter(valor__isnull=False).order_by('-data_atualizacao')
    
    bairros = Bairro.objects.all().order_by('nome')
    tipos_imovel = TipoImovel.objects.all().order_by('nome')
    caracteristicas = Caracteristica.objects.all().order_by('nome')
    
    filtros_aplicados = request.GET.copy()
    
    # --- Aplicação dos Filtros ---
    
    finalidade = filtros_aplicados.get('finalidade', 'lancamento')
    if finalidade:
        imoveis = imoveis.filter(finalidade=finalidade)

    categoria = filtros_aplicados.get('categoria')
    if categoria:
        imoveis = imoveis.filter(categoria=categoria)

    # NOVO FILTRO (name="query" do seu form)
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
    enviado = False
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
    """
    Mostra a página de detalhe de um único imóvel.
    """
    imovel = get_object_or_404(Imovel.objects.prefetch_related('imagens_secundarias', 'caracteristicas'), id=imovel_id)
    
    similares = Imovel.objects.filter(
        bairro=imovel.bairro, 
        categoria=imovel.categoria
    ).exclude(id=imovel_id)[:3] 
    
    # Gera o link do WhatsApp
    imovel_url = request.build_absolute_uri()
    mensagem = f"Olá, eu vi o imóvel '{imovel.titulo}' no site ({imovel_url}) e gostaria de mais informações."
    whatsapp_url = f"https://wa.me/5562983188400?text={urllib.parse.quote(mensagem)}"

    # Recupera a URL da última busca para o botão "voltar"
    last_search_url = request.session.get('last_search_url', '/imoveis/')

    # Decodifica o HTML da descrição para renderizar as tags <br>
    imovel.descricao = html.unescape(imovel.descricao)

    context = {
        'imovel': imovel,
        'similares': similares,
        'whatsapp_url': whatsapp_url,
        'last_search_url': last_search_url,
    }
    return render(request, 'core/detalhe_imovel.html', context)