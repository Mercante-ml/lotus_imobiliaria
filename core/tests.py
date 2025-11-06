from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Imovel, Profile

User = get_user_model()

class CoreViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.imovel = Imovel.objects.create(titulo='Imóvel Teste')

    def test_toggle_favorito_add(self):
        self.client.login(email='test@example.com', password='password')
        response = self.client.post(
            reverse('core:toggle_favorito'),
            {'id': self.imovel.id, 'action': 'add'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.profile.favoritos.filter(id=self.imovel.id).exists())

    def test_toggle_favorito_remove(self):
        self.user.profile.favoritos.add(self.imovel)
        self.client.login(email='test@example.com', password='password')
        response = self.client.post(
            reverse('core:toggle_favorito'),
            {'id': self.imovel.id, 'action': 'remove'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.profile.favoritos.filter(id=self.imovel.id).exists())

    def test_favoritos_view_authenticated(self):
        self.user.profile.favoritos.add(self.imovel)
        self.client.login(email='test@example.com', password='password')
        response = self.client.get(reverse('core:favoritos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.imovel.titulo)

    def test_favoritos_view_unauthenticated(self):
        response = self.client.get(reverse('core:favoritos'))
        self.assertEqual(response.status_code, 200)

    def test_password_change(self):
        self.client.login(email='test@example.com', password='password')
        response = self.client.post(reverse('account_change_password'), {
            'oldpassword': 'password',
            'password1': 'a_much_stronger_password',
            'password2': 'a_much_stronger_password',
        })
        self.assertEqual(response.status_code, 302, "Password change should redirect.")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('a_much_stronger_password'))
