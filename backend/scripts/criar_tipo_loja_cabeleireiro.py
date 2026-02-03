"""
Script para criar o tipo de loja Cabeleireiro no banco de dados
Execute: python manage.py shell < scripts/criar_tipo_loja_cabeleireiro.py
"""

from superadmin.models import TipoLoja

# Verificar se já existe
if TipoLoja.objects.filter(slug='cabeleireiro').exists():
    print("✅ Tipo de loja 'Cabeleireiro' já existe!")
    tipo = TipoLoja.objects.get(slug='cabeleireiro')
    print(f"   ID: {tipo.id}")
    print(f"   Nome: {tipo.nome}")
    print(f"   Dashboard: {tipo.dashboard_template}")
else:
    # Criar tipo de loja
    tipo = TipoLoja.objects.create(
        nome='Cabeleireiro',
        slug='cabeleireiro',
        descricao='Salão de beleza, barbearia e cabeleireiro com gestão completa de agendamentos, serviços, produtos e vendas',
        dashboard_template='cabeleireiro',
        cor_primaria='#EC4899',  # Rosa/Pink
        cor_secundaria='#DB2777',  # Rosa escuro
        tem_produtos=True,
        tem_servicos=True,
        tem_agendamento=True,
        tem_delivery=False,
        tem_estoque=True
    )
    print("✅ Tipo de loja 'Cabeleireiro' criado com sucesso!")
    print(f"   ID: {tipo.id}")
    print(f"   Nome: {tipo.nome}")
    print(f"   Slug: {tipo.slug}")
    print(f"   Dashboard: {tipo.dashboard_template}")
    print(f"   Cor Primária: {tipo.cor_primaria}")
    print(f"   Funcionalidades:")
    print(f"   - Produtos: {tipo.tem_produtos}")
    print(f"   - Serviços: {tipo.tem_servicos}")
    print(f"   - Agendamento: {tipo.tem_agendamento}")
    print(f"   - Estoque: {tipo.tem_estoque}")

print("\n🎉 Pronto! Agora você pode criar lojas do tipo 'Cabeleireiro'")
