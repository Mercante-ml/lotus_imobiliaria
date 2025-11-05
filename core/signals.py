from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from django.contrib.auth.models import User
from .models import Cliente
from allauth.socialaccount.models import SocialAccount

@receiver(user_logged_in)
def create_cliente_profile(sender, request, user, **kwargs):
    cliente, created = Cliente.objects.get_or_create(user=user)
    if created:
        try:
            social_account = SocialAccount.objects.get(user=user)
            if social_account.provider == 'google':
                user.first_name = social_account.extra_data.get('given_name')
                user.last_name = social_account.extra_data.get('family_name')
                cliente.foto_url = social_account.extra_data.get('picture')
            elif social_account.provider == 'facebook':
                user.first_name = social_account.extra_data.get('first_name')
                user.last_name = social_account.extra_data.get('last_name')
                cliente.foto_url = social_account.extra_data.get('picture', {}).get('data', {}).get('url')
            user.save()
            cliente.save()
        except SocialAccount.DoesNotExist:
            pass
