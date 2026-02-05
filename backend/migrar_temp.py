from cabeleireiro.models import Funcionario, Profissional

funcionarios = Funcionario.objects.filter(funcao='profissional')
print(f"Encontrados {funcionarios.count()} funcionarios profissionais")

migrados = 0
ja_existentes = 0

for func in funcionarios:
    existe = Profissional.objects.filter(loja_id=func.loja_id, email=func.email).first()
    if existe:
        print(f"Ja existe: {func.nome} ID: {existe.id}")
        ja_existentes += 1
        continue
    
    prof = Profissional.objects.create(
        loja_id=func.loja_id,
        nome=func.nome,
        email=func.email,
        telefone=func.telefone,
        especialidade=func.especialidade or 'Geral',
        comissao_percentual=func.comissao_percentual,
        is_active=True
    )
    print(f"Criado: {func.nome} ID: {prof.id}")
    migrados += 1

print(f"Migrados: {migrados}, Ja existentes: {ja_existentes}, Total: {funcionarios.count()}")
