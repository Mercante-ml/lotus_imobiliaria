import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lotus_imobiliaria.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

try:
    print("Enviando email...")
    send_mail(
        "Teste de Envio ImobGold",
        "Este é um email de teste para verificar se o SMTP está funcionando sem cair em spam/erros.",
        settings.DEFAULT_FROM_EMAIL,
        ['contato.dsprime@gmail.com'],
        fail_silently=False,
    )
    print("Sucesso!")
except Exception as e:
    print(f"Erro: {e}")
