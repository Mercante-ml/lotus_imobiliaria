views_code = """
@login_required
def crm_equipe(request):
    tenant = request.tenant
    is_owner = True # For now, assume logged in user in CRM is owner
    is_gerente = False
    
    if tenant.plano_ativo != 'corporate' and not request.user.is_superuser:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("A funcionalidade Gestão de Equipe (Multi-Corretores) é exclusiva do Plano Diamond. Faça o upgrade para utilizar.")
        
    if request.method == 'POST':
        corretor_id = request.POST.get('corretor_id')
        nome = request.POST.get('nome')
        whatsapp = request.POST.get('whatsapp')
        email = request.POST.get('email')
        
        role = request.POST.get('role', 'corretor')
        gerente_id = request.POST.get('gerente_id')
        gerente = None
        if gerente_id:
            gerente = Corretor.objects.filter(id=gerente_id).first()
        
        if nome and email:
            if role == 'diretor':
                comissao_venda_direta = tenant.taxa_corretor + tenant.taxa_gerente + tenant.taxa_diretor
                comissao_equipe = tenant.taxa_diretor
            elif role == 'gerente':
                comissao_venda_direta = tenant.taxa_corretor + tenant.taxa_gerente
                comissao_equipe = tenant.taxa_gerente
            else:
                comissao_venda_direta = tenant.taxa_corretor
                comissao_equipe = 0.0
                
            if corretor_id:
                from django.shortcuts import get_object_or_404
                corretor = get_object_or_404(Corretor, id=corretor_id)
                corretor.nome = nome
                corretor.telefone = whatsapp
                corretor.email = email
                corretor.cargo = role
                corretor.gerente_responsavel = gerente
                corretor.comissao_venda_direta = comissao_venda_direta
                corretor.comissao_equipe = comissao_equipe
                corretor.save()
            else:
                Corretor.objects.create(
                    nome=nome, 
                    telefone=whatsapp,
                    email=email,
                    cargo=role,
                    gerente_responsavel=gerente,
                    comissao_venda_direta=comissao_venda_direta if is_owner else 1.50,
                    comissao_equipe=comissao_equipe if is_owner else 0.30
                )
            return redirect('core:crm_equipe')
            
    corretores = Corretor.objects.all()
        
    organograma_diretores = Corretor.objects.filter(cargo='diretor')
    
    organograma_gerentes = []
    gerentes = Corretor.objects.filter(cargo='gerente')
    for g in gerentes:
        corretores_g = Corretor.objects.filter(gerente_responsavel=g, cargo='corretor')
        organograma_gerentes.append({'obj': g, 'corretores': corretores_g})
        
    organograma_soltos = Corretor.objects.filter(gerente_responsavel__isnull=True, cargo='corretor')

    return render(request, 'core/crm/equipe.html', {
        'imobiliaria': tenant, 
        'corretores': corretores,
        'organograma_diretores': organograma_diretores,
        'organograma_gerentes': organograma_gerentes,
        'organograma_soltos': organograma_soltos,
        'is_owner': is_owner,
        'is_gerente': is_gerente
    })

@login_required
def crm_comissoes(request):
    tenant = request.tenant
    is_owner = True
    
    if not is_owner:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Apenas donos ou diretores podem acessar as comissões globais.")
        
    if request.method == 'POST':
        try:
            tenant.comissao_padrao = float(request.POST.get('comissao_padrao', 5.0))
            tenant.taxa_corretor = float(request.POST.get('taxa_corretor', 1.5))
            tenant.taxa_gerente = float(request.POST.get('taxa_gerente', 0.3))
            tenant.taxa_diretor = float(request.POST.get('taxa_diretor', 0.2))
            tenant.save()
            
            Corretor.objects.filter(cargo='corretor').update(
                comissao_venda_direta=tenant.taxa_corretor,
                comissao_equipe=0.0
            )
            Corretor.objects.filter(cargo='gerente').update(
                comissao_venda_direta=(tenant.taxa_corretor + tenant.taxa_gerente),
                comissao_equipe=tenant.taxa_gerente
            )
            Corretor.objects.filter(cargo='diretor').update(
                comissao_venda_direta=(tenant.taxa_corretor + tenant.taxa_gerente + tenant.taxa_diretor),
                comissao_equipe=tenant.taxa_diretor
            )
            from django.contrib import messages
            messages.success(request, "Comissões atualizadas para toda a equipe com sucesso!")
        except ValueError:
            from django.contrib import messages
            messages.error(request, "Valores inválidos.")
            
        return redirect('core:crm_comissoes')

    return render(request, 'core/crm/comissoes.html', {
        'imobiliaria': tenant,
        'is_owner': True,
    })
"""
with open("/home/dsprime/projects/apps/lotus_imobiliaria/core/views.py", "a") as f:
    f.write(views_code)
