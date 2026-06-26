import re
from core.models import Bairro
from core.management.commands.importar_xml_teste import format_bairro_name

for b in list(Bairro.objects.all()):
    novo_nome = format_bairro_name(b.nome)
    if b.nome == novo_nome:
        continue
    
    existente = Bairro.objects.filter(nome=novo_nome).exclude(id=b.id).first()
    if existente:
        # Move properties
        for imovel in b.imovel_set.all():
            imovel.bairro = existente
            imovel.save(update_fields=['bairro'])
        b.delete()
    else:
        b.nome = novo_nome
        b.save(update_fields=['nome'])

print("Bairros formatados e agrupados com sucesso!")
