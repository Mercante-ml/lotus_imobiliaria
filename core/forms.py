from django import forms
from .models import Lead

class LeadForm(forms.ModelForm):
    
    class Meta:
        model = Lead
        fields = ['nome', 'email', 'telefone', 'mensagem']
        
        # Aqui está a "evolução":
        # Adicionamos as classes de estilo do Tailwind diretamente aqui.
        # Isto corrige o problema dos "campos em branco" no contato.html.
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

