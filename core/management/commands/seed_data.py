from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Imovel

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with test data'

    def handle(self, *args, **options):
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_user(username='testuser', email='test@example.com', password='password')
        if not Imovel.objects.filter(titulo='Imóvel Teste').exists():
            Imovel.objects.create(titulo='Imóvel Teste', valor=100000.00)
        self.stdout.write(self.style.SUCCESS('Successfully seeded the database.'))
