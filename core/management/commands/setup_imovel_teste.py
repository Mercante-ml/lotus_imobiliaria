from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
import requests
from core.models import Imovel, ImagemImovel, Bairro, TipoImovel

class Command(BaseCommand):
    help = 'Cria um imóvel de teste com galeria de imagens para verificação visual.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Iniciando criação de dados de teste para o imóvel..."))

        # Garante que um bairro e tipo de imóvel existam
        bairro, _ = Bairro.objects.get_or_create(nome="Setor de Testes")
        tipo, _ = TipoImovel.objects.get_or_create(nome="Apartamento de Teste")

        # Cria ou atualiza o imóvel com ID 1
        imovel_teste, created = Imovel.objects.update_or_create(
            id=1,
            defaults={
                'titulo': 'Imóvel de Teste para Lightbox',
                'descricao': '<p>Esta é uma descrição de teste. O lightbox deve funcionar ao clicar nas imagens.</p>',
                'valor': 950000.00,
                'quartos': 3,
                'suites': 1,
                'vagas': 2,
                'area_util': 120.00,
                'bairro': bairro,
                'tipo_imovel': tipo,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Imóvel de teste (ID: {imovel_teste.id}) criado."))
        else:
            self.stdout.write(self.style.WARNING(f"Imóvel de teste (ID: {imovel_teste.id}) atualizado."))
            # Limpa imagens antigas para evitar duplicatas
            imovel_teste.imagens_secundarias.all().delete()
            imovel_teste.imagem_principal = None
            imovel_teste.save()


        # URLs de imagens de placeholder
        image_urls = [
            'https://placehold.co/800x600/CCCCCC/FFFFFF/png',
            'https://placehold.co/800x600/AAAAAA/FFFFFF/png',
            'https://placehold.co/800x600/888888/FFFFFF/png',
            'https://placehold.co/800x600/666666/FFFFFF/png',
        ]

        try:
            # Baixa a primeira imagem como principal
            response = requests.get(image_urls[0], stream=True)
            if response.status_code == 200:
                imovel_teste.imagem_principal.save('principal.png', ContentFile(response.content), save=True)
                self.stdout.write(self.style.SUCCESS("Imagem principal baixada e salva."))

            # Baixa as outras como secundárias
            for i, url in enumerate(image_urls[1:]):
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    imagem_secundaria = ImagemImovel(imovel=imovel_teste)
                    imagem_secundaria.imagem.save(f'secundaria_{i+1}.png', ContentFile(response.content), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Imagem secundária {i+1} baixada e salva."))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Erro ao baixar imagens: {e}"))
            self.stdout.write(self.style.WARNING("O teste visual pode falhar se as imagens não puderem ser baixadas."))

        self.stdout.write(self.style.SUCCESS("Dados de teste criados com sucesso."))
