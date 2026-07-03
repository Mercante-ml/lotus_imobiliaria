import os

templates_dir = '/home/dsprime/projects/apps/lotus_imobiliaria/clientes/templates/clientes/'
os.makedirs(templates_dir, exist_ok=True)

def get_progress_bar(step):
    dots = ""
    for i in range(1, 9):
        if i < step:
            bg = "bg-[#C6A87C] text-white"
        elif i == step:
            bg = "bg-[#C6A87C] text-white ring-4 ring-[#C6A87C]/30"
        else:
            bg = "bg-gray-200 text-gray-500"
        dots += f'<div class="w-8 h-8 rounded-full {bg} flex items-center justify-center font-bold text-sm shrink-0">{i}</div>'
    
    width_pct = (step - 1) * (100 / 7)
    
    return f"""
        <div class="flex items-center justify-between mb-8 relative">
            <div class="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-gray-200 -z-10"></div>
            <div class="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-[#C6A87C] -z-10 transition-all duration-500" style="width: {width_pct}%;"></div>
            {dots}
        </div>
    """

def get_base(step, title, subtitle, content, js="", form_enctype=""):
    enctype = 'enctype="multipart/form-data"' if form_enctype else ''
    voltar_btn = '<a href="{% url ' + chr(39) + 'saas_setup' + chr(39) + ' ' + str(step-1) + ' %}" class="text-gray-500 hover:text-gray-900 font-medium px-4 py-2 transition">&larr; Voltar</a>' if step > 1 else '<div></div>'
    btn_text = 'Finalizar Setup' if step == 8 else 'Próximo Passo'
    onclick_attr = 'onclick="this.innerHTML=' + chr(39) + '<i class=' + chr(92) + chr(39) + 'fa-solid fa-circle-notch fa-spin' + chr(92) + chr(39) + '></i> Criando Plataforma...' + chr(39) + ';"' if step == 8 else ''    
    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Passo {step} - {title} - Setup</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/imask"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
        .font-serif {{ font-family: 'Playfair Display', serif !important; }}
    </style>
</head>
<body class="bg-gray-50 font-sans min-h-screen flex items-center justify-center py-12">
    
    <div class="w-full max-w-4xl mx-auto bg-white p-8 md:p-12 rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100">
        {get_progress_bar(step)}

        <h1 class="text-4xl font-serif text-gray-900 mb-2">{title}</h1>
        <p class="text-gray-500 mb-10 text-lg">{subtitle}</p>

        <form method="POST" action="{{% url 'saas_setup' {step} %}}" {enctype}>
            {{% csrf_token %}}
            
            <div class="space-y-6">
                {content}
            </div>

            <div class="mt-12 flex justify-between items-center pt-6 border-t border-gray-100">
                {voltar_btn}
                <button type="submit" id="btnSubmit" class="bg-gray-900 text-white px-8 py-4 rounded-xl font-bold hover:bg-[#C6A87C] transition shadow-lg flex items-center gap-2" {onclick_attr}>
                    {btn_text} <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>
        </form>
    </div>

    {js}
</body>
</html>
"""

# STEP 1
content1 = """
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="md:col-span-2">
            <label class="block text-sm font-bold text-gray-700 mb-2">Nome da Imobiliária / Empresa</label>
            <input type="text" name="nome_imobiliaria" value="{{ form.nome_imobiliaria.value|default:'' }}" required class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] focus:border-[#C6A87C] outline-none transition text-lg bg-gray-50 focus:bg-white" placeholder="Ex: Lotus Imobiliária">
        </div>
        
        <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Subdomínio Desejado</label>
            <div class="flex rounded-xl overflow-hidden border border-gray-300 focus-within:ring-2 focus-within:ring-[#C6A87C] transition">
                <input type="text" name="subdominio" value="{{ form.subdominio.value|default:'' }}" required class="w-full px-5 py-4 outline-none text-right bg-gray-50 focus:bg-white" placeholder="suaempresa">
                <span class="px-5 py-4 bg-gray-100 text-gray-500 border-l border-gray-300 font-medium">.imobgold.com</span>
            </div>
        </div>
        
        <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Cor Principal da Marca</label>
            <select name="cor_primaria" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white cursor-pointer">
                {% for val, name in form.cor_primaria.field.choices %}
                <option value="{{ val }}" {% if form.cor_primaria.value == val %}selected{% endif %}>{{ name }}</option>
                {% endfor %}
            </select>
        </div>
        
        <div class="md:col-span-2 p-6 border-2 border-dashed border-gray-200 rounded-2xl bg-gray-50 text-center hover:bg-gray-100 transition cursor-pointer relative mt-4">
            <input type="file" name="logo" accept="image/*" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer">
            <i class="fa-solid fa-cloud-arrow-up text-4xl text-gray-400 mb-3"></i>
            <h3 class="text-lg font-bold text-gray-700">Logo da sua Empresa</h3>
            <p class="text-sm text-gray-500 mt-1">Clique ou arraste sua logo (PNG transparente recomendado)</p>
        </div>
        
        <div class="md:col-span-2 pt-6 border-t border-gray-100 mt-2">
            <label class="block text-sm font-bold text-gray-700 mb-4">Quais tipos de imóveis você trabalha?</label>
            <div class="flex gap-6">
                <label class="flex items-center gap-3 cursor-pointer p-4 border border-gray-200 rounded-xl hover:border-[#C6A87C] transition flex-1 text-center justify-center">
                    <input type="checkbox" name="portfolio_lancamento" {% if form.portfolio_lancamento.value or form.portfolio_lancamento.value is None %}checked{% endif %} class="w-5 h-5 text-[#C6A87C] rounded border-gray-300 focus:ring-[#C6A87C]">
                    <span class="font-bold text-gray-700">Lançamentos</span>
                </label>
                <label class="flex items-center gap-3 cursor-pointer p-4 border border-gray-200 rounded-xl hover:border-[#C6A87C] transition flex-1 text-center justify-center">
                    <input type="checkbox" name="portfolio_revenda" {% if form.portfolio_revenda.value or form.portfolio_revenda.value is None %}checked{% endif %} class="w-5 h-5 text-[#C6A87C] rounded border-gray-300 focus:ring-[#C6A87C]">
                    <span class="font-bold text-gray-700">Revenda</span>
                </label>
                <label class="flex items-center gap-3 cursor-pointer p-4 border border-gray-200 rounded-xl hover:border-[#C6A87C] transition flex-1 text-center justify-center">
                    <input type="checkbox" name="portfolio_aluguel" {% if form.portfolio_aluguel.value %}checked{% endif %} class="w-5 h-5 text-[#C6A87C] rounded border-gray-300 focus:ring-[#C6A87C]">
                    <span class="font-bold text-gray-700">Aluguel</span>
                </label>
            </div>
        </div>
    </div>
"""
with open(os.path.join(templates_dir, 'setup_step1.html'), 'w') as f:
    f.write(get_base(1, "Identidade Visual", "Vamos configurar a cara do seu novo site e sistema.", content1, "", True))


# STEP 2
content2 = """
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
            <div class="flex justify-between items-center mb-2">
                <label class="block text-sm font-bold text-gray-700">Documento</label>
                <div class="flex items-center gap-3 text-sm">
                    <label class="flex items-center gap-1 cursor-pointer font-medium text-gray-600">
                        <input type="radio" name="tipo_documento" value="CNPJ" id="radio-cnpj" onchange="toggleDocMask()" {% if form.tipo_documento.value == 'CNPJ' or form.tipo_documento.value is None %}checked{% endif %} class="text-[#C6A87C] focus:ring-[#C6A87C]"> CNPJ
                    </label>
                    <label class="flex items-center gap-1 cursor-pointer font-medium text-gray-600">
                        <input type="radio" name="tipo_documento" value="CPF" id="radio-cpf" onchange="toggleDocMask()" {% if form.tipo_documento.value == 'CPF' %}checked{% endif %} class="text-[#C6A87C] focus:ring-[#C6A87C]"> CPF
                    </label>
                </div>
            </div>
            <input type="text" name="cpf_cnpj" id="input-doc" value="{{ form.cpf_cnpj.value|default:'' }}" required placeholder="00.000.000/0001-00"
                   class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
        </div>
        
        <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Telefone / WhatsApp Principal</label>
            <input type="text" name="telefone" id="input-telefone" value="{{ form.telefone.value|default:'' }}" required placeholder="(00) 00000-0000"
                   class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
        </div>
        
        <div class="md:col-span-2">
            <label class="block text-sm font-bold text-gray-700 mb-2">E-mail Público (Para clientes entrarem em contato)</label>
            <input type="email" name="empresa_email" value="{{ form.empresa_email.value|default:'' }}" placeholder="contato@suaempresa.com.br"
                   class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
        </div>
        
        <!-- Endereço -->
        <div class="md:col-span-2 pt-6 border-t border-gray-100 mt-2">
            <h3 class="text-xl font-bold text-gray-900 mb-6">Endereço da Sede</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="md:col-span-1">
                    <label class="block text-sm font-bold text-gray-700 mb-2">CEP</label>
                    <input type="text" name="cep" id="input-cep" value="{{ form.cep.value|default:'' }}" placeholder="00000-000" onblur="buscarCep(this.value)"
                           class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
                <div class="md:col-span-2">
                    <label class="block text-sm font-bold text-gray-700 mb-2">Rua / Logradouro</label>
                    <input type="text" name="rua" id="input-rua" value="{{ form.rua.value|default:'' }}"
                           class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-100">
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="md:col-span-1">
                    <label class="block text-sm font-bold text-gray-700 mb-2">Número</label>
                    <input type="text" name="numero" value="{{ form.numero.value|default:'' }}"
                           class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
                <div class="md:col-span-2">
                    <label class="block text-sm font-bold text-gray-700 mb-2">Complemento (Opcional)</label>
                    <input type="text" name="complemento" value="{{ form.complemento.value|default:'' }}" placeholder="Ex: Sala 402"
                           class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div class="md:col-span-2">
                    <label class="block text-sm font-bold text-gray-700 mb-2">Bairro</label>
                    <input type="text" name="bairro" id="input-bairro" value="{{ form.bairro.value|default:'' }}"
                           class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-100">
                </div>
                <div class="md:col-span-1">
                    <label class="block text-sm font-bold text-gray-700 mb-2">Cidade</label>
                    <input type="text" name="cidade" id="input-cidade" value="{{ form.cidade.value|default:'' }}"
                           class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-100">
                </div>
                <div class="md:col-span-1">
                    <label class="block text-sm font-bold text-gray-700 mb-2">UF</label>
                    <input type="text" name="uf" id="input-uf" value="{{ form.uf.value|default:'' }}" maxlength="2"
                           class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-100 uppercase">
                </div>
            </div>
        </div>
    </div>
"""
js2 = r"""
<script>
    IMask(document.getElementById('input-telefone'), { mask: '(00) 00000-0000' });
    IMask(document.getElementById('input-cep'), { mask: '00000-000' });
    var docMask;
    
    function initMask() {
        var input = document.getElementById('input-doc');
        if (docMask) docMask.destroy();
        if (document.getElementById('radio-cnpj').checked) {
            docMask = IMask(input, { mask: '00.000.000/0000-00' }); 
            input.placeholder = '00.000.000/0001-00';
        } else {
            docMask = IMask(input, { mask: '000.000.000-00' }); 
            input.placeholder = '000.000.000-00';
        }
    }
    
    function toggleDocMask() {
        document.getElementById('input-doc').value = ''; 
        initMask();
    }
    
    initMask();

    function buscarCep(cepVal) {
        let cepLimpo = cepVal.replace(/\D/g, '');
        if (cepLimpo.length === 8) {
            fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`).then(res => res.json()).then(data => {
                if (!data.erro) {
                    document.getElementById('input-rua').value = data.logradouro;
                    document.getElementById('input-bairro').value = data.bairro;
                    document.getElementById('input-cidade').value = data.localidade;
                    document.getElementById('input-uf').value = data.uf;
                }
            });
        }
    }
</script>
"""
with open(os.path.join(templates_dir, 'setup_step2.html'), 'w') as f:
    f.write(get_base(2, "Contato e Endereço", "Informações públicas e de faturamento da empresa.", content2, js2))

# STEP 3
content3 = """
    <div class="space-y-6">
        <div class="bg-blue-50 border border-blue-100 p-5 rounded-2xl flex gap-4 text-blue-800">
            <i class="fa-solid fa-circle-info text-2xl"></i>
            <p class="text-sm">Estes são os textos que aparecerão no <strong>topo do seu site</strong>, a primeira coisa que o cliente lerá.</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="md:col-span-2">
                <label class="block text-sm font-bold text-gray-700 mb-2">Tagline (Texto pequeno no topo)</label>
                <input type="text" name="home_hero_tag" value="{{ form.home_hero_tag.value|default:'O Padrão de Viver' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
            </div>
            
            <div class="md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Título Principal (Texto normal)</label>
                    <input type="text" name="home_hero_titulo" value="{{ form.home_hero_titulo.value|default:'O Seu Espaço de' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Destaque (Aparece Dourado)</label>
                    <input type="text" name="home_hero_destaque" value="{{ form.home_hero_destaque.value|default:'Renascimento.' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
            </div>
            
            <div class="md:col-span-2">
                <label class="block text-sm font-bold text-gray-700 mb-2">Subtítulo Principal (Texto de apoio descritivo)</label>
                <textarea name="home_hero_subtitulo" rows="2" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">{{ form.home_hero_subtitulo.value|default:'Curadoria especializada para transformar a complexidade do mercado na simplicidade do extraordinário.' }}</textarea>
            </div>
        </div>
        
        <div class="pt-8 border-t border-gray-100 mt-4">
            <h3 class="text-xl font-bold text-gray-900 mb-6">Sessão Manifesto</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Título do Manifesto (Normal)</label>
                    <input type="text" name="home_manifesto_titulo" value="{{ form.home_manifesto_titulo.value|default:'Não vendemos imóveis.' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Destaque do Manifesto (Dourado)</label>
                    <input type="text" name="home_manifesto_destaque" value="{{ form.home_manifesto_destaque.value|default:'Apresentamos novos começos.' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
                <div class="md:col-span-2">
                    <label class="block text-sm font-bold text-gray-700 mb-2">Texto do Manifesto</label>
                    <textarea name="home_manifesto_texto" rows="3" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">{{ form.home_manifesto_texto.value|default:'Nascemos com o propósito de elevar a experiência de encontrar o seu lar. Trabalhamos apenas com uma seleção criteriosa de propriedades que oferecem design imponente, conforto absoluto e exclusividade.' }}</textarea>
                </div>
            </div>
        </div>
    </div>
"""
with open(os.path.join(templates_dir, 'setup_step3.html'), 'w') as f:
    f.write(get_base(3, "Textos da Página Inicial", "Cause a melhor primeira impressão com chamadas matadoras.", content3))

# STEP 4
content4 = """
    <div class="space-y-6">
        <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Título da Página (Hero)</label>
            <input type="text" name="sobre_titulo" value="{{ form.sobre_titulo.value|default:'A Nossa História' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
        </div>
        
        <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Subtítulo da Página</label>
            <input type="text" name="sobre_subtitulo" value="{{ form.sobre_subtitulo.value|default:'Descubra o propósito que nos move e a curadoria que nos define.' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
        </div>
        
        <div>
            <label class="block text-sm font-bold text-gray-700 mb-2">Frase de Impacto / Citação</label>
            <textarea name="sobre_citacao" rows="2" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">{{ form.sobre_citacao.value|default:'Tal como a flor de lótus, florescemos onde poucos imaginam: entregando beleza e valor em toda a jornada dos nossos clientes.' }}</textarea>
        </div>
        
        <div class="pt-6 border-t border-gray-100">
            <label class="block text-sm font-bold text-gray-700 mb-2">Texto Completo: Quem Somos</label>
            <textarea name="texto_quem_somos" rows="6" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">{{ form.texto_quem_somos.value|default:'Inspirados pela flor de lótus, símbolo milenar de pureza, resiliência e renascimento, trazemos renovação e integridade a cada negociação imobiliária.' }}</textarea>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-2">Nossa Missão</label>
                <textarea name="sobre_missao" rows="4" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">{{ form.sobre_missao.value|default:'Proporcionar experiências imobiliárias únicas, que transcendam a simples transação. Construímos relações sólidas baseadas em confiança, clareza e um atendimento de excelência que reflete a mesma qualidade e sofisticação dos imóveis que representamos.' }}</textarea>
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-2">Nossa Visão</label>
                <textarea name="sobre_visao" rows="4" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">{{ form.sobre_visao.value|default:'Ser a principal referência em curadoria e atendimento personalizado no mercado imobiliário de médio e alto padrão. Aspiramos ser a primeira e única escolha para clientes exigentes que procuram não apenas um endereço, mas um verdadeiro refúgio.' }}</textarea>
            </div>
        </div>
    </div>
"""
with open(os.path.join(templates_dir, 'setup_step4.html'), 'w') as f:
    f.write(get_base(4, "Página Sobre Nós", "Conte a história, missão e visão da sua imobiliária.", content4))

# STEP 5 - Equipe
content5 = """
    <div class="space-y-6">
        <div class="flex items-center gap-4 bg-gray-50 p-6 rounded-2xl border border-gray-200">
            <label class="relative inline-flex items-center cursor-pointer shrink-0">
                <input type="checkbox" name="exibir_equipe" id="toggle_equipe" onchange="toggleContent()" {% if form.exibir_equipe.value or form.exibir_equipe.value is None %}checked{% endif %} class="sr-only peer">
                <div class="w-14 h-7 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-[#C6A87C]"></div>
            </label>
            <div>
                <h4 class="font-bold text-gray-900 text-lg">Exibir seção "Nossa Equipe" no Site</h4>
                <p class="text-sm text-gray-500">Mostre seus corretores na página inicial para gerar proximidade. Você poderá cadastrar a equipe posteriormente no painel do CRM.</p>
            </div>
        </div>
        
        <div id="equipe_content" class="space-y-8 transition-all duration-300">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Título da Seção</label>
                    <input type="text" name="titulo_equipe" value="{{ form.titulo_equipe.value|default:'Nossa Equipe' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-2">Subtítulo Descritivo</label>
                    <input type="text" name="subtitulo_equipe" value="{{ form.subtitulo_equipe.value|default:'Especialistas dedicados a encontrar o imóvel ideal para você.' }}" class="w-full px-5 py-4 rounded-xl border border-gray-300 focus:ring-2 focus:ring-[#C6A87C] outline-none transition bg-gray-50 focus:bg-white">
                </div>
            </div>
            <input type="hidden" name="acao_equipe" value="pular">
        </div>
    </div>
"""
js5 = """
<script>
    function toggleContent() {
        var isChecked = document.getElementById('toggle_equipe').checked;
        var content = document.getElementById('equipe_content');
        if(isChecked) { content.classList.remove('opacity-50', 'pointer-events-none'); }
        else { content.classList.add('opacity-50', 'pointer-events-none'); }
    }
    
    toggleContent();
</script>
"""
with open(os.path.join(templates_dir, 'setup_step5.html'), 'w') as f:
    f.write(get_base(5, "Nossa Equipe", "Apresente seus corretores para gerar mais confiança.", content5, js5, False))

# STEP 6 - Blog
content6 = """
    <div class="space-y-6">
        <div class="flex items-center gap-4 bg-gray-50 p-6 rounded-2xl border border-gray-200">
            <label class="relative inline-flex items-center cursor-pointer shrink-0">
                <input type="checkbox" name="exibir_blog" id="toggle_blog" onchange="toggleContent()" {% if form.exibir_blog.value or form.exibir_blog.value is None %}checked{% endif %} class="sr-only peer">
                <div class="w-14 h-7 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-[#C6A87C]"></div>
            </label>
            <div>
                <h4 class="font-bold text-gray-900 text-lg">Ativar Módulo de Blog / Notícias</h4>
                <p class="text-sm text-gray-500">Módulo incrível para publicar artigos em PDF, links e vídeos do YouTube. Você poderá gerenciá-los pelo painel CRM.</p>
            </div>
        </div>
        <input type="hidden" name="acao_blog" value="pular">
    </div>
"""
js6 = """
<script>
    function toggleContent() {
        var isChecked = document.getElementById('toggle_blog').checked;
        var content = document.getElementById('blog_content');
        if(content) {
            if(isChecked) { content.classList.remove('opacity-50', 'pointer-events-none'); }
            else { content.classList.add('opacity-50', 'pointer-events-none'); }
        }
    }
    
    toggleContent();
</script>
"""
with open(os.path.join(templates_dir, 'setup_step6.html'), 'w') as f:
    f.write(get_base(6, "Central de Blog", "Atraia visitantes com artigos e materiais ricos.", content6, js6, False))

# STEP 7 - Imóveis
content7 = """
    <div class="space-y-6">
        <h4 class="font-bold text-xl text-gray-900 mb-6 text-center">Como deseja adicionar seus imóveis para inaugurar o site?</h4>
        <input type="hidden" name="acao_imoveis" id="acao_imoveis" value="pular">
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div onclick="selectAcao('upload')" id="card_upload" class="acao-card p-8 border-2 border-gray-200 rounded-3xl cursor-pointer hover:border-[#C6A87C] transition flex flex-col items-center text-center bg-white">
                <i class="fa-solid fa-file-code text-4xl text-gray-400 mb-4"></i>
                <h5 class="font-bold text-lg text-gray-800 mb-2">Importar XML Zap</h5>
                <p class="text-sm text-gray-500 leading-relaxed">Transferir em massa seu estoque de outro sistema via XML Padrão Zap/VivaReal.</p>
            </div>
            
            <div onclick="selectAcao('manual')" id="card_manual" class="acao-card p-8 border-2 border-gray-200 rounded-3xl cursor-pointer hover:border-[#C6A87C] transition flex flex-col items-center text-center bg-white">
                <i class="fa-solid fa-house-medical text-4xl text-gray-400 mb-4"></i>
                <h5 class="font-bold text-lg text-gray-800 mb-2">Cadastrar Manual</h5>
                <p class="text-sm text-gray-500 leading-relaxed">Gosto de fazer o cadastro perfeito, com calma, direto no painel CRM.</p>
            </div>
            
            <div onclick="selectAcao('pular')" id="card_pular" class="acao-card p-8 border-2 border-[#C6A87C] bg-[#C6A87C]/5 rounded-3xl cursor-pointer transition flex flex-col items-center text-center shadow-lg shadow-[#C6A87C]/10">
                <i class="fa-solid fa-forward text-4xl text-[#C6A87C] mb-4"></i>
                <h5 class="font-bold text-lg text-[#C6A87C] mb-2">Pular Etapa</h5>
                <p class="text-sm text-[#C6A87C]/70 font-medium leading-relaxed">Deixar site temporariamente vazio por enquanto.</p>
            </div>
        </div>
        
        <div id="upload_box" class="hidden mt-8 p-8 bg-gray-50 rounded-3xl border border-gray-200 shadow-inner">
            <label class="block text-base font-bold text-gray-800 mb-4 flex items-center justify-center gap-3">
                <i class="fa-solid fa-cloud-arrow-up text-[#C6A87C] text-2xl"></i> Envie seu arquivo XML
            </label>
            <input type="file" name="arquivo_xml" accept=".xml" class="w-full px-5 py-4 rounded-xl border border-gray-300 bg-white focus:ring-2 focus:ring-[#C6A87C] outline-none">
            <p class="text-sm text-gray-500 mt-4 text-center">Os imóveis começarão a ser importados automaticamente em segundo plano após você finalizar a próxima etapa de Setup.</p>
        </div>
    </div>
"""
js7 = """
<script>
    function selectAcao(acao) {
        document.getElementById('acao_imoveis').value = acao;
        document.querySelectorAll('.acao-card').forEach(el => {
            el.classList.remove('border-[#C6A87C]', 'bg-[#C6A87C]/5', 'shadow-lg', 'shadow-[#C6A87C]/10');
            el.querySelector('i').classList.remove('text-[#C6A87C]');
            el.querySelector('h5').classList.remove('text-[#C6A87C]');
            el.querySelector('p').classList.remove('text-[#C6A87C]/70', 'font-medium');
            
            el.classList.add('border-gray-200', 'bg-white');
            el.querySelector('i').classList.add('text-gray-400');
            el.querySelector('h5').classList.add('text-gray-800');
            el.querySelector('p').classList.add('text-gray-500');
        });
        
        let activeCard = document.getElementById('card_' + acao);
        activeCard.classList.add('border-[#C6A87C]', 'bg-[#C6A87C]/5', 'shadow-lg', 'shadow-[#C6A87C]/10');
        activeCard.classList.remove('border-gray-200', 'bg-white');
        activeCard.querySelector('i').classList.add('text-[#C6A87C]');
        activeCard.querySelector('i').classList.remove('text-gray-400');
        activeCard.querySelector('h5').classList.add('text-[#C6A87C]');
        activeCard.querySelector('h5').classList.remove('text-gray-800');
        activeCard.querySelector('p').classList.remove('text-gray-500');
        activeCard.querySelector('p').classList.add('text-[#C6A87C]/70', 'font-medium');
        
        if(acao === 'upload') {
            document.getElementById('upload_box').classList.remove('hidden');
        } else {
            document.getElementById('upload_box').classList.add('hidden');
        }
    }
</script>
"""
with open(os.path.join(templates_dir, 'setup_step7.html'), 'w') as f:
    f.write(get_base(7, "Seus Imóveis", "O coração do seu negócio. Vamos trazer o seu estoque.", content7, js7, True))

# STEP 8 - Plano
content8 = """
    <div class="space-y-10">
        
        <input type="hidden" name="plano_escolhido" id="plano_escolhido" value="corporate">
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <!-- Plano Boutique -->
            <div onclick="selectPlan('boutique')" id="plan_boutique" class="relative border-2 border-gray-200 rounded-3xl p-8 cursor-pointer hover:border-[#C6A87C] transition group bg-white">
                <div class="absolute top-6 right-6 text-gray-300 group-hover:text-[#C6A87C] transition" id="check_boutique">
                    <i class="fa-regular fa-circle text-2xl"></i>
                </div>
                <h3 class="text-3xl font-serif font-bold text-gray-900 mb-2">Boutique</h3>
                <p class="text-gray-500 text-sm mb-8 h-10 pr-8">Perfeito para corretores independentes e curadoria seleta.</p>
                <div class="mb-8">
                    <span class="text-5xl font-bold text-gray-900">R$ 299</span><span class="text-gray-500 font-medium">/mês</span>
                </div>
                
                <ul class="space-y-4 text-sm text-gray-600 font-medium">
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> Até 3 Corretores</li>
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> 5GB de Armazenamento</li>
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> CRM Premium</li>
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> Site Alta Conversão</li>
                </ul>
            </div>
            
            <!-- Plano Corporate -->
            <div onclick="selectPlan('corporate')" id="plan_corporate" class="relative border-2 border-[#C6A87C] bg-[#C6A87C]/5 shadow-2xl shadow-[#C6A87C]/10 rounded-3xl p-8 cursor-pointer transition group">
                <div class="absolute -top-4 left-1/2 -translate-x-1/2 bg-[#C6A87C] text-white px-6 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest shadow-md">
                    Mais Popular
                </div>
                <div class="absolute top-6 right-6 text-[#C6A87C]" id="check_corporate">
                    <i class="fa-solid fa-circle-check text-2xl"></i>
                </div>
                
                <h3 class="text-3xl font-serif font-bold text-[#C6A87C] mb-2">Corporate</h3>
                <p class="text-gray-600 text-sm mb-8 h-10 pr-8">Para grandes operações, integrações de portal e alto volume.</p>
                <div class="mb-8">
                    <span class="text-5xl font-bold text-gray-900">R$ 599</span><span class="text-gray-500 font-medium">/mês</span>
                </div>
                
                <ul class="space-y-4 text-sm text-gray-800 font-bold">
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> Corretores Ilimitados</li>
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> 10GB de Armazenamento</li>
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> Importação de XML ZAP</li>
                    <li class="flex items-center gap-3"><i class="fa-solid fa-check text-[#C6A87C] text-lg"></i> Gestão de Comissões</li>
                </ul>
            </div>
        </div>
        
        <div class="bg-blue-50 p-6 rounded-2xl border border-blue-100 text-sm text-blue-800 flex items-start gap-4">
            <i class="fa-solid fa-shield-halved text-2xl text-blue-400 mt-1"></i>
            <div>
                <strong class="block mb-1 text-blue-900 text-base">Criação da Infraestrutura Segura</strong>
                Ao clicar em "Finalizar Setup", nossos servidores configurarão instantaneamente o seu Banco de Dados isolado, Roteamento Cloudflare e Painel CRM. 
                Isso pode demorar de 10 a 20 segundos. Por favor, <strong>não feche nem atualize a página</strong>.
            </div>
        </div>
    </div>
"""
js8 = """
<script>
    function selectPlan(plan) {
        document.getElementById('plano_escolhido').value = plan;
        
        const b = document.getElementById('plan_boutique');
        const c = document.getElementById('plan_corporate');
        const checkB = document.getElementById('check_boutique');
        const checkC = document.getElementById('check_corporate');
        
        if(plan === 'boutique') {
            b.classList.add('border-[#C6A87C]', 'bg-[#C6A87C]/5', 'shadow-2xl', 'shadow-[#C6A87C]/10');
            b.classList.remove('border-gray-200', 'bg-white');
            b.querySelector('h3').classList.add('text-[#C6A87C]');
            b.querySelector('h3').classList.remove('text-gray-900');
            checkB.innerHTML = '<i class="fa-solid fa-circle-check text-2xl"></i>';
            checkB.classList.add('text-[#C6A87C]');
            checkB.classList.remove('text-gray-300');
            
            c.classList.remove('border-[#C6A87C]', 'bg-[#C6A87C]/5', 'shadow-2xl', 'shadow-[#C6A87C]/10');
            c.classList.add('border-gray-200', 'bg-white');
            c.querySelector('h3').classList.remove('text-[#C6A87C]');
            c.querySelector('h3').classList.add('text-gray-900');
            checkC.innerHTML = '<i class="fa-regular fa-circle text-2xl"></i>';
            checkC.classList.remove('text-[#C6A87C]');
            checkC.classList.add('text-gray-300');
        } else {
            c.classList.add('border-[#C6A87C]', 'bg-[#C6A87C]/5', 'shadow-2xl', 'shadow-[#C6A87C]/10');
            c.classList.remove('border-gray-200', 'bg-white');
            c.querySelector('h3').classList.add('text-[#C6A87C]');
            c.querySelector('h3').classList.remove('text-gray-900');
            checkC.innerHTML = '<i class="fa-solid fa-circle-check text-2xl"></i>';
            checkC.classList.add('text-[#C6A87C]');
            checkC.classList.remove('text-gray-300');
            
            b.classList.remove('border-[#C6A87C]', 'bg-[#C6A87C]/5', 'shadow-2xl', 'shadow-[#C6A87C]/10');
            b.classList.add('border-gray-200', 'bg-white');
            b.querySelector('h3').classList.remove('text-[#C6A87C]');
            b.querySelector('h3').classList.add('text-gray-900');
            checkB.innerHTML = '<i class="fa-regular fa-circle text-2xl"></i>';
            checkB.classList.remove('text-[#C6A87C]');
            checkB.classList.add('text-gray-300');
        }
    }
</script>
"""
with open(os.path.join(templates_dir, 'setup_step8.html'), 'w') as f:
    f.write(get_base(8, "Escolha seu Plano", "O último passo antes de dominar o mercado imobiliário.", content8, js8))

print("Templates generated successfully!")
