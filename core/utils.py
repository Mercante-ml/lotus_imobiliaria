import xml.etree.ElementTree as ET
from core.models import Imovel
import re
from celery import shared_task
import requests
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.db import connection
from django.utils.text import slugify

def clean_text(text):
    if text:
        return text.strip()
    return ''

def format_bairro_name(bairro_name):
    if not bairro_name:
        return ''
    subs = {
        r'\b(?:str|st|st\.)\b': 'Setor',
        r'\b(?:cond|cond\.)\b': 'Condomínio',
        r'\b(?:res|res\.)\b': 'Residencial',
        r'\b(?:pq|pq\.)\b': 'Parque',
        r'\b(?:jd|jd\.)\b': 'Jardim',
        r'\b(?:vl|vl\.)\b': 'Vila',
        r'\b(?:av|av\.)\b': 'Avenida',
        r'\b(?:ch|ch\.)\b': 'Chácara',
        r'\b(?:faz|faz\.)\b': 'Fazenda',
        r'\b(?:lote|lot\.)\b': 'Loteamento',
    }
    name = bairro_name.strip()
    for padrao, substituto in subs.items():
        name = re.sub(padrao, substituto, name, flags=re.IGNORECASE)
    exceptions = ['de', 'do', 'da', 'dos', 'das', 'e']
    words = name.split()
    formatted_words = []
    for i, word in enumerate(words):
        if i > 0 and word.lower() in exceptions:
            formatted_words.append(word.lower())
        else:
            formatted_words.append(word.capitalize())
    return ' '.join(formatted_words)

def traduzir_tipo_imovel(tipo_ingles):
    if not tipo_ingles:
        return 'Outros'
    tipo = tipo_ingles.strip().lower()
    if '/' in tipo:
        tipo = tipo.split('/')[-1].strip()
    mapa = {
        'apartment': 'Apartamento',
        'building': 'Prédio/Edifício',
        'business': 'Ponto Comercial',
        'condo': 'Casa de Condomínio',
        'edificio comercial': 'Prédio Comercial',
        'edificio residencial': 'Prédio Residencial',
        'farm ranch': 'Chácara/Fazenda',
        'flat': 'Flat',
        'home': 'Casa',
        'hotel': 'Hotel',
        'industrial': 'Galpão/Industrial',
        'land lot': 'Lote/Terreno',
        'office': 'Sala Comercial',
        'penthouse': 'Cobertura',
        'sobrado': 'Sobrado',
        'studio': 'Studio',
        'village house': 'Casa de Vila'
    }
    return mapa.get(tipo, tipo_ingles.title())
from django.core.cache import cache
from django.db import connection

@shared_task(bind=True)
def process_xml_task(self, xml_file_path, tenant_schema, tenant_id):
    from core.models import Imovel, ImagemImovel
    from clientes.models import Client
    
    # Switch schema for this task
    connection.set_schema(tenant_schema)
    tenant = Client.objects.get(id=tenant_id)
    
    cache_key = f'sync_{tenant_schema}'
    cache.set(cache_key, {'status': 'reading_file', 'current': 0, 'total': 0}, timeout=3600)
    
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_string = f.read()
            
        root = ET.fromstring(xml_string)
        listings = root.findall('.//Listing')
        total = len(listings)
        
        # O cliente quer que a nova carga SUBSTITUA o estoque antigo
        # Limpa todos os imóveis deste tenant antes de processar os novos
        Imovel.objects.all().delete()
        
        cache.set(cache_key, {'status': 'processing', 'current': 0, 'total': total}, timeout=3600)
        
        count = 0
        
        for listing in listings:
            titulo_node = listing.find('.//Title')
            titulo = clean_text(titulo_node.text) if titulo_node is not None else 'Imóvel sem título'
            
            desc_node = listing.find('.//Description')
            descricao = clean_text(desc_node.text) if desc_node is not None else ''
            
            details = listing.find('.//Details')
            valor = None
            quartos = 0
            banheiros = 0
            area = None
            tipo_imovel_obj = None
            bairro_obj = None
            cidade_text = ''
            
            if details is not None:
                price_node = details.find('.//ListPrice')
                if price_node is not None and price_node.text:
                    try:
                        val = re.sub(r'[^\d.]', '', price_node.text.replace(',', '.'))
                        if val: valor = float(val)
                    except ValueError: pass
                
                bed_node = details.find('.//Bedrooms')
                if bed_node is not None and bed_node.text and bed_node.text.isdigit():
                    quartos = int(bed_node.text)
                    
                bath_node = details.find('.//Bathrooms')
                if bath_node is not None and bath_node.text and bath_node.text.isdigit():
                    banheiros = int(bath_node.text)
                    
                area_node = details.find('.//LivingArea')
                if area_node is not None and area_node.text:
                    try:
                        area = float(area_node.text)
                    except ValueError: pass
                    
                # Extrair Tipo do Imóvel
                from core.models import TipoImovel, Bairro
                tipo_node = details.find('.//PropertyType')
                if tipo_node is None:
                    tipo_node = details.find('.//PropertySubType') # fallback
                if tipo_node is not None and tipo_node.text:
                    tipo_ingles = clean_text(tipo_node.text)
                    tipo_nome = traduzir_tipo_imovel(tipo_ingles)
                    if tipo_nome:
                        tipo_slug = slugify(tipo_nome)
                        tipo_imovel_obj, _ = TipoImovel.objects.get_or_create(nome=tipo_nome[:100], defaults={'slug': tipo_slug[:100]})
                        
            # Extrair Bairro e Cidade
            location = listing.find('.//Location')
            if location is not None:
                bairro_node = location.find('.//Neighborhood')
                if bairro_node is not None and bairro_node.text:
                    bairro_nome_raw = clean_text(bairro_node.text)
                    bairro_nome = format_bairro_name(bairro_nome_raw)
                    if bairro_nome:
                        bairro_obj, _ = Bairro.objects.get_or_create(nome=bairro_nome[:80])
                        
                cidade_node = location.find('.//City')
                if cidade_node is not None and cidade_node.text:
                    cidade_text = clean_text(cidade_node.text).title()

            imovel = Imovel.objects.create(
                titulo=titulo[:250],
                descricao=descricao,
                valor=valor,
                quartos=quartos,
                banheiros=banheiros,
                area_util=area,
                tipo_imovel=tipo_imovel_obj,
                bairro=bairro_obj,
                cidade=cidade_text[:100]
            )
            
            # Baixar imagens
            media = listing.find('.//Media')
            if media is not None:
                items = media.findall('.//Item')
                for i, item in enumerate(items):
                    # Limita a 10 fotos por imóvel para não travar o servidor (MVP)
                    if i >= 10: break
                    
                    if item.text:
                        img_url = clean_text(item.text)
                        try:
                            response = requests.get(img_url, timeout=3)
                            if response.status_code == 200:
                                if i == 0:
                                    img_name = f"imovel_{imovel.id}_capa.jpg"
                                    imovel.imagem_principal.save(img_name, ContentFile(response.content), save=True)
                                else:
                                    img_name = f"imovel_{imovel.id}_sec_{i}.jpg"
                                    img_obj = ImagemImovel(imovel=imovel)
                                    img_obj.imagem.save(img_name, ContentFile(response.content), save=True)
                        except Exception as e:
                            print(f"Erro ao baixar imagem {img_url}: {e}")
            
            count += 1
            cache.set(cache_key, {'status': 'processing', 'current': count, 'total': total}, timeout=3600)
            
        cache.set(cache_key, {'status': 'done', 'current': count, 'total': total}, timeout=3600)
        
    except Exception as e:
        print(f"General XML processing error in task: {e}")
        cache.set(cache_key, {'status': 'error', 'error': str(e)}, timeout=3600)

def processar_xml_vivareal(xml_file_path, tenant):
    """
    Spawns a Celery background task to process the XML so the UI isn't blocked.
    """
    process_xml_task.delay(xml_file_path, tenant.schema_name, tenant.id)
