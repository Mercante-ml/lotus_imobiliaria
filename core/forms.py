from django import forms
from .models import Lead

# --- NOVAS IMPORTAÇÕES ---
from django.contrib.auth import get_user_model
from .models import Profile
from allauth.account.forms import SignupForm # Importa o form base do allauth
# -------------------------

User = get_user_model()


# --- 1. SEU FORMULÁRIO DE CONTATO (LeadForm) ---
class LeadForm(forms.ModelForm):
    
    class Meta:
        model = Lead
        fields = ['nome', 'email', 'telefone', 'mensagem']
        
        # Widgets com o estilo Tailwind (que já estavam corretos)
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'w-full p-3 text-sm text-graphite bg-white border border-gray-400 rounded-lg focus:outline-none focus:border-ouro focus:ring-2 focus:ring-ouro/50',
                'placeholder': 'O seu nome completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full p-3 text-sm text-graphite bg-white border border-gray-400 rounded-lg focus:outline-none focus:border-ouro focus:ring-2 focus:ring-ouro/50',
                'placeholder': 'O seu melhor email'
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'w-full p-3 text-sm text-graphite bg-white border border-gray-400 rounded-lg focus:outline-none focus:border-ouro focus:ring-2 focus:ring-ouro/50',
                'placeholder': '(Opcional) O seu número de WhatsApp'
            }),
            'mensagem': forms.Textarea(attrs={
                'class': 'w-full p-3 text-sm text-graphite bg-white border border-gray-400 rounded-lg focus:outline-none focus:border-ouro focus:ring-2 focus:ring-ouro/50',
                'rows': 4,
                'placeholder': 'Escreva a sua mensagem...'
            }),
        }

# --- 2. FORMULÁRIOS "MINHA CONTA" ---

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('telefone',)


# --- 3. NOVO FORMULÁRIO DE CADASTRO (Signup) ---
class CustomSignupForm(SignupForm):
    # Adicionamos os campos que queremos
    first_name = forms.CharField(max_length=30, label='Nome')
    last_name = forms.CharField(max_length=150, label='Sobrenome')

    def save(self, request):
        # Chama o 'save' original do allauth
        user = super(CustomSignupForm, self).save(request)
        
        # Pega os dados dos nossos novos campos e salva no User
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        
        return user