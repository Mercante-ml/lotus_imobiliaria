
from django.core.management.base import BaseCommand
from core.models import ConteudoPagina

class Command(BaseCommand):
    help = 'Creates or updates the sobre page content for Playwright tests with body content.'

    def handle(self, *args, **options):
        custom_title = "Página Sobre Dinâmica"
        custom_subtitle = "Este conteúdo é 100% editável pelo admin."
        custom_body = """
            <h2>Nossa Nova Missão</h2>
            <p><strong>Missão:</strong> Entregar código que funciona na primeira tentativa.</p>
            <blockquote>Isto é um teste.</blockquote>
        """

        obj, created = ConteudoPagina.objects.update_or_create(
            chave='pagina_sobre',
            defaults={
                'titulo': custom_title,
                'subtitulo': custom_subtitle,
                'corpo': custom_body
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created test content for sobre page.'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated test content for sobre page.'))
