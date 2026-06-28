from django import forms

class OnboardingStep1Form(forms.Form):
    nome_imobiliaria = forms.CharField(label='Nome da Imobiliária', max_length=100)
    tipo_documento = forms.ChoiceField(label='Tipo de Documento', choices=[('CPF', 'CPF'), ('CNPJ', 'CNPJ')], widget=forms.RadioSelect)
    cpf_cnpj = forms.CharField(label='CPF ou CNPJ', max_length=20)
    telefone = forms.CharField(label='Telefone', max_length=20)
    
    cep = forms.CharField(label='CEP', max_length=10)
    rua = forms.CharField(label='Rua', max_length=150)
    numero = forms.CharField(label='Número', max_length=20)
    complemento = forms.CharField(label='Complemento', max_length=100, required=False)
    bairro = forms.CharField(label='Bairro', max_length=100)
    cidade = forms.CharField(label='Cidade', max_length=100)
    uf = forms.CharField(label='UF', max_length=2)

CORES_CHOICES = [
    ('#C6A87C', 'Dourado Premium'),
    ('#1B2A59', 'Azul Marinho'),
    ('#1a1a1a', 'Grafite / Preto'),
    ('#164e63', 'Verde Esmeralda'),
    ('#7f1d1d', 'Vinho / Bordeaux')
]

class OnboardingStep2Form(forms.Form):
    subdominio = forms.SlugField(label='Subdomínio (URL)', max_length=50)
    cor_primaria = forms.ChoiceField(choices=CORES_CHOICES, label='Cor Principal do Site')
    portfolio_lancamento = forms.BooleanField(label='Lançamentos', required=False, initial=True)
    portfolio_revenda = forms.BooleanField(label='Revenda', required=False, initial=True)
    portfolio_aluguel = forms.BooleanField(label='Aluguel', required=False, initial=False)

class OnboardingStep3Form(forms.Form):
    texto_quem_somos = forms.CharField(
        label='Quem Somos', 
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'Conte a história da sua imobiliária...'}),
        required=False
    )

class OnboardingStep4Form(forms.Form):
    # XML VivaReal/Zap upload
    arquivo_xml = forms.FileField(
        label='Importar Estoque (XML VivaReal/Zap)',
        required=False,
        help_text='Faça upload do seu XML padrão Grupo ZAP para importar seus imóveis automaticamente.'
    )

class OnboardingStep5Form(forms.Form):
    # Formulário vazio apenas para submissão do plano escolhido
    plano_escolhido = forms.CharField(widget=forms.HiddenInput(), initial='boutique')
