# core/management/commands/importar_xml_teste.py

import requests
import re
import logging
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from core.models import Imovel, ImagemImovel, Bairro, TipoImovel, Caracteristica
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# --- Funções de Limpeza de Dados ---

def get_text(element, tag, default=''):
    """ Pega o texto de um sub-elemento, tratando se for None. """
    try:
        text = element.find(tag).text
        return text.strip() if text else default
    except AttributeError:
        return default

def get_decimal(element, tag, default=None):
    """ Pega um valor decimal, tratando erros. """
    try:
        text = get_text(element, tag)
        if text:
            # Remove qualquer coisa que não seja dígito ou ponto/vírgula
            cleaned_text = re.sub(r'[^\d,\.]', '', text)
            # Substitui vírgula por ponto
            cleaned_text = cleaned_text.replace(',', '.')
            return Decimal(cleaned_text)
        return default
    except (InvalidOperation, TypeError, AttributeError):
        return default

def get_int(element, tag, default=None):
    """ Pega um valor inteiro, tratando erros. """
    try:
        text = get_text(element, tag)
        if text:
            # Pega apenas os dígitos
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
    # Adicione outras substituições se necessário
    return text

# --- Fim das Funções de Limpeza ---


class Command(BaseCommand):
    help = 'Importa dados de imóveis do imoveis.xml (teste) para o modelo evoluído.'

    def add_arguments(self, parser):
        # O ficheiro XML que você enviou
        parser.add_argument('xml_file', type=str, help='Caminho para o ficheiro imoveis.xml', default='imoveis.xml', nargs='?')

    def handle(self, *args, **kwargs):
        xml_file_path = kwargs['xml_file']
        self.stdout.write(self.style.SUCCESS(f'Iniciando importação de {xml_file_path}...'))

        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            count = 0

            for listing in root.findall('.//Listing'):
                listing_id = get_text(listing, 'ListingID')
                if not listing_id:
                    continue

                self.stdout.write(self.style.NOTICE(f'Processando Imóvel ID: {listing_id}'))

                # --- Mapeamento do XML para o nosso Models.py Evoluído ---
                
                # 1. Dados Simples (Texto, Números)
                titulo = clean_description(get_text(listing, 'Title', 'Título não informado'))
                descricao = clean_description(get_text(listing.find('Details'), 'Description', ''))
                
                # 2. Dados de Preço e Medidas
                valor = get_decimal(listing.find('Details'), 'ListPrice')
                area_util = get_decimal(listing.find('Details'), 'LivingArea')
                quartos = get_int(listing.find('Details'), 'Bedrooms')
                suites = get_int(listing.find('Details'), 'Suites')
                banheiros = get_int(listing.find('Details'), 'Bathrooms')
                vagas = get_int(listing.find('Details'), 'Garage')
                
                # 3. Mapeamento de 'Finalidade' (Lançamento/Revenda)
                # Assumindo que 'PREMIUM' no XML significa Lançamento (ajuste esta regra se necessário)
                publication_type = get_text(listing, 'PublicationType')
                finalidade = 'lancamento' if publication_type == 'PREMIUM' else 'revenda'

                # 4. Mapeamento de ForeignKeys (Bairro, TipoImovel)
                bairro_nome = get_text(listing.find('Location'), 'Neighborhood')
                bairro, _ = Bairro.objects.get_or_create(nome=bairro_nome) if bairro_nome else (None, False)

                tipo_nome = get_text(listing.find('Details'), 'PropertyType')
                tipo_imovel, _ = TipoImovel.objects.get_or_create(nome=tipo_nome, defaults={'slug': slugify(tipo_nome)}) if tipo_nome else (None, False)

                # --- Criação ou Atualização do Imóvel ---
                imovel, created = Imovel.objects.update_or_create(
                    titulo=titulo, # Usando título como chave (ou mude para um ID único se tiver)
                    defaults={
                        'descricao': descricao,
                        'valor': valor,
                        'area_util': area_util,
                        'quartos': quartos,
                        'suites': suites,
                        'banheiros': banheiros,
                        'vagas': vagas,
                        'finalidade': finalidade,
                        'bairro': bairro,
                        'tipo_imovel': tipo_imovel,
                        'em_destaque': (finalidade == 'lancamento') # Vamos marcar lançamentos como destaque por padrão
                    }
                )

                # 5. Mapeamento de Many-to-Many (Características)
                imovel.caracteristicas.clear()
                features_text = get_text(listing.find('Details'), 'Features')
                if features_text:
                    features_list = features_text.split(';')
                    for feat_nome in features_list:
                        if feat_nome.strip():
                            caracteristica, _ = Caracteristica.objects.get_or_create(nome=feat_nome.strip())
                            imovel.caracteristicas.add(caracteristica)

                # 6. O "HACK" DAS IMAGENS (Download e Salvamento Local)
                media = listing.find('Media')
                if media is not None:
                    # Limpa imagens antigas
                    ImagemImovel.objects.filter(imovel=imovel).delete()
                    
                    # Imagem Principal
                    primary_item = media.find('Item[@primary="true"]')
                    if primary_item is not None:
                        image_url = primary_item.text.strip() if primary_item.text else None
                        if image_url:
                            try:
                                response = requests.get(image_url)
                                if response.status_code == 200:
                                    file_name = image_url.split('/')[-1]
                                    imovel.imagem_principal.save(file_name, ContentFile(response.content), save=True)
                                    self.stdout.write(f'  > Imagem principal descarregada: {file_name}')
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'  > Falha ao descarregar imagem principal: {e}'))

                    # Imagens Secundárias (Galeria)
                    for item in media.findall('Item[@medium="image"]'):
                        if item.get('primary') == 'true':
                            continue # Já processámos a principal
                        
                        image_url = item.text.strip() if item.text else None
                        if image_url:
                            try:
                                response = requests.get(image_url)
                                if response.status_code == 200:
                                    file_name = image_url.split('/')[-1]
                                    img_obj = ImagemImovel(imovel=imovel)
                                    img_obj.imagem.save(file_name, ContentFile(response.content), save=True)
                                    self.stdout.write(f'  > Imagem da galeria descarregada: {file_name}')
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'  > Falha ao descarregar imagem da galeria: {e}'))

                count += 1
                
            self.stdout.write(self.style.SUCCESS(f'Importação concluída. {count} imóveis processados.'))

        except ET.ParseError as e:
            self.stdout.write(self.style.ERROR(f'Erro ao fazer o parse do XML: {e}'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Erro: Ficheiro não encontrado em "{xml_file_path}". Tem a certeza que ele está no sítio certo?'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocorreu um erro inesperado: {e}'))
            logger.exception('Erro inesperado na importação de XML:')
