# core/management/commands/importar_xml_teste.py

import requests
import re
import logging
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
# Importe todos os modelos necessários
from core.models import Imovel, ImagemImovel, Bairro, TipoImovel, Caracteristica
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# --- Funções de Limpeza de Dados ---

def get_text(element, tag, default=''):
    """ Pega o texto de um sub-elemento, tratando se for None. """
    try:
        node = element.find(tag)
        if node is not None and node.text:
            return node.text.strip()
        return default
    except AttributeError:
        return default

def get_decimal(element, tag, default=None):
    """ Pega um valor decimal, tratando erros. """
    try:
        text = get_text(element, tag)
        if text:
            cleaned_text = re.sub(r'[^\d,\.]', '', text)
            cleaned_text = cleaned_text.replace(',', '.')
            if cleaned_text:
                return Decimal(cleaned_text)
        return default
    except (InvalidOperation, TypeError, AttributeError):
        return default

def get_int(element, tag, default=None):
    """ Pega um valor inteiro, tratando erros. """
    try:
        text = get_text(element, tag)
        if text:
            cleaned_text = re.sub(r'[^\d]', '', text)
            if cleaned_text:
                return int(cleaned_text)
        return default
    except (ValueError, TypeError, AttributeError):
        return default

def clean_description(text):
    """ Limpa o texto da descrição para remover branding (ex: Urbs). """
    if not text:
        return ""
    text = re.sub(r'urbs', 'Lotus', text, flags=re.IGNORECASE)
    return text

# --- Fim das Funções de Limpeza ---


class Command(BaseCommand):
    help = 'Importa dados de imóveis do imoveis.xml (teste) para o modelo evoluído.'

    def add_arguments(self, parser):
        parser.add_argument('xml_file', type=str, help='Caminho para o ficheiro imoveis.xml', default='imoveis.xml', nargs='?')
        
        parser.add_argument(
            '--limit',
            type=int,
            help='Limita a importação ao N primeiro imóveis (para testes rápidos).',
            default=None
        )
        
        # --- NOVO: Adiciona a opção --offset ---
        parser.add_argument(
            '--offset',
            type=int,
            help='Pula os N primeiros imóveis (para importar em lotes).',
            default=0 # Padrão é 0 (não pular nenhum)
        )
        
        # --- NOVO: Adiciona a opção --force-finalidade ---
        parser.add_argument(
            '--force-finalidade',
            type=str,
            choices=['lancamento', 'revenda'],
            help='Força a finalidade (lancamento ou revenda) para todos os imóveis importados.',
            default=None
        )

    def handle(self, *args, **kwargs):
        xml_file_path = kwargs['xml_file']
        
        # --- Pega nos novos valores ---
        limit = kwargs.get('limit') 
        offset = kwargs.get('offset', 0)
        force_finalidade = kwargs.get('force_finalidade')
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando importação de {xml_file_path}...'))
        
        if limit: self.stdout.write(self.style.WARNING(f'--- MODO DE TESTE: Limitado a {limit} imóveis ---'))
        if offset: self.stdout.write(self.style.WARNING(f'--- MODO DE TESTE: Pulando os primeiros {offset} imóveis ---'))
        if force_finalidade: self.stdout.write(self.style.WARNING(f'--- MODO DE TESTE: Forçando finalidade = "{force_finalidade}" ---'))

        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            count_processed = 0 # Quantos imóveis nós importámos
            count_skipped = 0   # Quantos imóveis nós pulámos (offset)

            for listing in root.findall('.//Listing'):
                
                # --- LÓGICA DO OFFSET ---
                if count_skipped < offset:
                    count_skipped += 1
                    continue # Pula este imóvel

                # --- LÓGICA DO LIMIT ---
                if limit is not None and count_processed >= limit:
                    self.stdout.write(self.style.WARNING(f'\nLimite de {limit} imóveis atingido. Parando a importação.'))
                    break # Sai do loop 'for'
                
                listing_id = get_text(listing, 'ListingID')
                if not listing_id:
                    continue

                self.stdout.write(self.style.NOTICE(f'Processando Imóvel ID: {listing_id} (Imóvel {count_skipped + 1} do XML)'))

                # --- Mapeamento do XML ---
                
                details = listing.find('Details')
                location = listing.find('Location')
                
                # 1. Dados Simples
                titulo = clean_description(get_text(listing, 'Title', f'Imóvel Cód. {listing_id}'))
                descricao = clean_description(get_text(details, 'Description', ''))
                
                # 2. Dados de Preço e Medidas
                valor = get_decimal(details, 'ListPrice')
                taxa_condominio = get_decimal(details, 'PropertyAdministrationFee')
                iptu = get_decimal(details, 'Iptu')
                area_util = get_decimal(details, 'LivingArea')
                quartos = get_int(details, 'Bedrooms')
                suites = get_int(details, 'Suites')
                banheiros = get_int(details, 'Bathrooms')
                vagas = get_int(details, 'Garage')
                andar = get_int(details, 'UnitFloor')
                
                # 3. Mapeamento de 'Finalidade' - LÓGICA ATUALIZADA
                
                # Lógica Padrão (Baseada no Título)
                titulo_lower = titulo.lower()
                if 'lançamento' in titulo_lower or 'breve' in titulo_lower:
                    finalidade_default = 'lancamento'
                else:
                    finalidade_default = 'revenda'
                
                # Override (se o comando --force-finalidade foi usado)
                finalidade = force_finalidade if force_finalidade else finalidade_default
                em_destaque_default = (finalidade == 'lancamento') # Marca lançamentos como destaque

                # 4. Mapeamento de 'Categoria' (Residencial/Comercial)
                usage_type = get_text(details, 'UsageType')
                categoria = 'comercial' if usage_type and 'commercial' in usage_type.lower() else 'residencial'

                # 5. Mapeamento de ForeignKeys (Bairro)
                bairro_nome = get_text(location, 'Neighborhood')
                bairro, _ = Bairro.objects.get_or_create(nome=bairro_nome) if bairro_nome else (None, False)

                # 6. Mapeamento de 'TipoImovel'
                property_type_raw = get_text(details, 'PropertyType')
                tipo_nome = property_type_raw
                if '/' in property_type_raw:
                    partes = property_type_raw.split('/')
                    tipo_nome = partes[-1].strip()

                tipo_imovel, _ = TipoImovel.objects.get_or_create(nome=tipo_nome, defaults={'slug': slugify(tipo_nome)}) if tipo_nome and tipo_nome.strip() else (None, False)
                
                # --- Criação ou Atualização do Imóvel ---
                imovel, created = Imovel.objects.update_or_create(
                    titulo=titulo, # Assumindo título como chave única para testes
                    defaults={
                        'descricao': descricao,
                        'valor': valor,
                        'taxa_condominio': taxa_condominio,
                        'iptu': iptu,
                        'area_util': area_util,
                        'quartos': quartos,
                        'suites': suites,
                        'banheiros': banheiros,
                        'vagas': vagas,
                        'andar': andar,
                        'finalidade': finalidade, # Salva a finalidade (forçada ou não)
                        'categoria': categoria, 
                        'bairro': bairro,
                        'tipo_imovel': tipo_imovel,
                        'em_destaque': em_destaque_default # Salva o destaque
                    }
                )

                # 7. Mapeamento de Many-to-Many (Características)
                imovel.caracteristicas.clear()
                features_text = get_text(details, 'Features')
                if features_text:
                    features_list = features_text.split(';')
                    for feat_nome in features_list:
                        if feat_nome.strip():
                            caracteristica, _ = Caracteristica.objects.get_or_create(nome=feat_nome.strip())
                            imovel.caracteristicas.add(caracteristica)

                # 8. O "HACK" DAS IMAGENS (Download e Salvamento Local)
                media = listing.find('Media')
                if media is not None:
                    if not created:
                        ImagemImovel.objects.filter(imovel=imovel).delete()
                        if imovel.imagem_principal:
                            imovel.imagem_principal.delete(save=False)
                    
                    # Imagem Principal
                    primary_item = media.find('Item[@primary="true"]')
                    if primary_item is not None:
                        image_url = primary_item.text.strip() if primary_item.text else None
                        if image_url:
                            try:
                                response = requests.get(image_url, timeout=10)
                                if response.status_code == 200:
                                    file_name = image_url.split('/')[-1]
                                    imovel.imagem_principal.save(file_name, ContentFile(response.content), save=True)
                                    self.stdout.write(f'  > Imagem principal descarregada: {file_name}')
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'  > Falha ao descarregar imagem principal: {e}'))

                    # Imagens Secundárias (Galeria)
                    for item in media.findall('Item[@medium="image"]'):
                        if item.get('primary') == 'true': continue
                        image_url = item.text.strip() if item.text else None
                        if image_url:
                            try:
                                response = requests.get(image_url, timeout=10)
                                if response.status_code == 200:
                                    file_name = image_url.split('/')[-1]
                                    img_obj = ImagemImovel(imovel=imovel)
                                    img_obj.imagem.save(file_name, ContentFile(response.content), save=True)
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'  > Falha ao descarregar imagem da galeria: {e}'))

                count_processed += 1
                
            self.stdout.write(self.style.SUCCESS(f'\nImportação concluída. {count_processed} imóveis processados. ({count_skipped} imóveis pulados).'))

        except ET.ParseError as e:
            self.stdout.write(self.style.ERROR(f'Erro ao fazer o parse do XML: {e}'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Erro: Ficheiro não encontrado em "{xml_file_path}". Tem a certeza que ele está no sítio certo (raiz do projeto)?'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocorreu um erro inesperado: {e}'))
            logger.exception('Erro inesperado na importação de XML:')



