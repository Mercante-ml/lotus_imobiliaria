from django import forms

CORES_CHOICES = [
    ('#C6A87C', 'Dourado Premium'),
    ('#1B2A59', 'Azul Marinho'),
    ('#1a1a1a', 'Grafite / Preto'),
    ('#164e63', 'Verde Esmeralda'),
    ('#7f1d1d', 'Vinho / Bordeaux')
]

# Passo 1: Identidade Visual
class OnboardingStep1Form(forms.Form):
    nome_imobiliaria = forms.CharField(label='Nome da Imobiliária', max_length=100)
    subdominio = forms.SlugField(label='Subdomínio (URL)', max_length=50)
    cor_primaria = forms.ChoiceField(choices=CORES_CHOICES, label='Cor Principal do Site')
    logo = forms.ImageField(label='Logo da Imobiliária', required=False, help_text='Envie a logo da sua imobiliária (PNG ou SVG transparente recomendado).')
    portfolio_lancamento = forms.BooleanField(label='Lançamentos', required=False, initial=True)
    portfolio_revenda = forms.BooleanField(label='Revenda', required=False, initial=True)
    portfolio_aluguel = forms.BooleanField(label='Aluguel', required=False, initial=False)

# Passo 2: Contatos e Endereço
class OnboardingStep2Form(forms.Form):
    tipo_documento = forms.ChoiceField(label='Tipo de Documento', choices=[('CPF', 'CPF'), ('CNPJ', 'CNPJ')], widget=forms.RadioSelect)
    cpf_cnpj = forms.CharField(label='CPF ou CNPJ', max_length=20)
    telefone = forms.CharField(label='Telefone', max_length=20)
    empresa_email = forms.EmailField(label='E-mail Público', required=False)
    
    cep = forms.CharField(label='CEP', max_length=10, required=False)
    rua = forms.CharField(label='Rua', max_length=150, required=False)
    numero = forms.CharField(label='Número', max_length=20, required=False)
    complemento = forms.CharField(label='Complemento', max_length=100, required=False)
    bairro = forms.CharField(label='Bairro', max_length=100, required=False)
    cidade = forms.CharField(label='Cidade', max_length=100, required=False)
    uf = forms.CharField(label='UF', max_length=2, required=False)

# Passo 3: Página Inicial
class OnboardingStep3Form(forms.Form):
    home_hero_bg_preset = forms.CharField(label='Fundo Hero', max_length=20, required=False, initial="preset_1")
    home_hero_tag = forms.CharField(label='Tagline', max_length=50, required=False, initial="O Padrão de Viver")
    home_hero_titulo = forms.CharField(label='Título Principal', max_length=150, required=False, initial="O Seu Espaço de")
    home_hero_destaque = forms.CharField(label='Destaque (Dourado)', max_length=150, required=False, initial="Renascimento.")
    home_hero_subtitulo = forms.CharField(label='Subtítulo Principal', widget=forms.Textarea(attrs={'rows': 2}), required=False, initial="Curadoria especializada para transformar a complexidade do mercado na simplicidade do extraordinário.")
    
    home_manifesto_titulo = forms.CharField(label='Título do Manifesto', max_length=150, required=False, initial="Não vendemos imóveis.")
    home_manifesto_destaque = models_destaque = forms.CharField(label='Destaque do Manifesto', max_length=150, required=False, initial="Apresentamos novos começos.")
    home_manifesto_texto = forms.CharField(label='Texto do Manifesto', widget=forms.Textarea(attrs={'rows': 3}), required=False, initial="Nascemos com o propósito de elevar a experiência de encontrar o seu lar...")

# Passo 4: Sobre
class OnboardingStep4Form(forms.Form):
    sobre_titulo = forms.CharField(label='Título da Página (Hero)', max_length=150, required=False, initial="A Nossa História")
    sobre_subtitulo = forms.CharField(label='Subtítulo da Página', max_length=250, required=False, initial="Descubra o propósito que nos move e a curadoria que nos define.")
    sobre_citacao = forms.CharField(label='Citação / Frase de Impacto', widget=forms.Textarea(attrs={'rows': 2}), required=False, initial="Tal como a flor de lótus, florescemos onde poucos imaginam...")
    texto_quem_somos = forms.CharField(label='Quem Somos', widget=forms.Textarea(attrs={'rows': 4}), required=False)
    sobre_missao = forms.CharField(label='Nossa Missão', widget=forms.Textarea(attrs={'rows': 3}), required=False)
    sobre_visao = forms.CharField(label='Nossa Visão', widget=forms.Textarea(attrs={'rows': 3}), required=False)

# Passo 5: Equipe (Upload, Manual ou Pular)
class OnboardingStep5Form(forms.Form):
    exibir_equipe = forms.BooleanField(label='Exibir seção "Nossa Equipe" no site', required=False, initial=True)
    titulo_equipe = forms.CharField(label='Título da Seção Equipe', max_length=150, initial='Nossa Equipe', required=False)
    subtitulo_equipe = forms.CharField(label='Subtítulo da Seção Equipe', max_length=250, initial='Especialistas dedicados a encontrar o imóvel ideal para você.', required=False)
    
    acao_equipe = forms.ChoiceField(choices=[('upload', 'Upload Planilha'), ('manual', 'Cadastrar Manualmente'), ('pular', 'Pular')], initial='pular', widget=forms.HiddenInput())
    arquivo_equipe = forms.FileField(label='Importar Corretores (CSV)', required=False)

# Passo 6: Blog (Upload, Manual ou Pular)
class OnboardingStep6Form(forms.Form):
    exibir_blog = forms.BooleanField(label='Exibir seção "Blog/Notícias" no site', required=False, initial=True)
    
    acao_blog = forms.ChoiceField(choices=[('upload', 'Upload Planilha'), ('manual', 'Cadastrar Manualmente'), ('pular', 'Pular')], initial='pular', widget=forms.HiddenInput())
    arquivo_blog = forms.FileField(label='Importar Posts (CSV)', required=False)

# Passo 7: Imóveis (Upload, Manual ou Pular)
class OnboardingStep7Form(forms.Form):
    acao_imoveis = forms.ChoiceField(choices=[('upload', 'Upload XML'), ('manual', 'Cadastrar Manualmente'), ('pular', 'Pular')], initial='pular', widget=forms.HiddenInput())
    arquivo_xml = forms.FileField(
        label='Importar Estoque (XML VivaReal/Zap)',
        required=False,
        help_text='Faça upload do seu XML padrão Grupo ZAP para importar seus imóveis automaticamente.'
    )

# Passo 8: Escolha do Plano
class OnboardingStep8Form(forms.Form):
    # Formulário vazio apenas para submissão do plano escolhido
    plano_escolhido = forms.CharField(widget=forms.HiddenInput(), initial='boutique')
