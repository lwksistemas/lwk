from superadmin.models import TipoLoja, PlanoAssinatura

# Buscar todos os tipos de loja
tipos = TipoLoja.objects.all()

print(f"✅ Encontrados {tipos.count()} tipos de loja")

# Definir 4 planos para cada tipo
planos_config = [
    {
        'nome': 'Starter',
        'ordem': 1,
        'descricao': 'Ideal para começar',
        'preco_mensal': '49.90',
        'preco_anual': '499.00',
        'max_produtos': 50,
        'max_usuarios': 2,
        'max_pedidos_mes': 50,
        'espaco_storage_gb': 2,
        'tem_relatorios_avancados': False,
        'tem_api_acesso': False,
        'tem_suporte_prioritario': False,
        'tem_dominio_customizado': False,
        'tem_whatsapp_integration': False,
    },
    {
        'nome': 'Básico',
        'ordem': 2,
        'descricao': 'Para pequenos negócios',
        'preco_mensal': '99.90',
        'preco_anual': '999.00',
        'max_produtos': 200,
        'max_usuarios': 5,
        'max_pedidos_mes': 200,
        'espaco_storage_gb': 10,
        'tem_relatorios_avancados': True,
        'tem_api_acesso': False,
        'tem_suporte_prioritario': False,
        'tem_dominio_customizado': False,
        'tem_whatsapp_integration': True,
    },
    {
        'nome': 'Profissional',
        'ordem': 3,
        'descricao': 'Para negócios em crescimento',
        'preco_mensal': '199.90',
        'preco_anual': '1999.00',
        'max_produtos': 1000,
        'max_usuarios': 15,
        'max_pedidos_mes': 1000,
        'espaco_storage_gb': 50,
        'tem_relatorios_avancados': True,
        'tem_api_acesso': True,
        'tem_suporte_prioritario': True,
        'tem_dominio_customizado': True,
        'tem_whatsapp_integration': True,
    },
    {
        'nome': 'Enterprise',
        'ordem': 4,
        'descricao': 'Solução completa e ilimitada',
        'preco_mensal': '399.90',
        'preco_anual': '3999.00',
        'max_produtos': 999999,
        'max_usuarios': 50,
        'max_pedidos_mes': 999999,
        'espaco_storage_gb': 200,
        'tem_relatorios_avancados': True,
        'tem_api_acesso': True,
        'tem_suporte_prioritario': True,
        'tem_dominio_customizado': True,
        'tem_whatsapp_integration': True,
    },
]

# Criar planos para cada tipo de loja
total_criados = 0
for tipo in tipos:
    print(f"\n📦 Criando planos para: {tipo.nome}")
    
    for plano_config in planos_config:
        # Gerar slug único
        slug = f"{plano_config['nome'].lower()}-{tipo.slug}"
        
        # Verificar se já existe
        if PlanoAssinatura.objects.filter(slug=slug).exists():
            print(f"  ⚠️  Plano {plano_config['nome']} já existe para {tipo.nome}")
            continue
        
        # Criar plano
        plano = PlanoAssinatura.objects.create(
            nome=plano_config['nome'],
            slug=slug,
            descricao=plano_config['descricao'],
            preco_mensal=plano_config['preco_mensal'],
            preco_anual=plano_config['preco_anual'],
            max_produtos=plano_config['max_produtos'],
            max_usuarios=plano_config['max_usuarios'],
            max_pedidos_mes=plano_config['max_pedidos_mes'],
            espaco_storage_gb=plano_config['espaco_storage_gb'],
            tem_relatorios_avancados=plano_config['tem_relatorios_avancados'],
            tem_api_acesso=plano_config['tem_api_acesso'],
            tem_suporte_prioritario=plano_config['tem_suporte_prioritario'],
            tem_dominio_customizado=plano_config['tem_dominio_customizado'],
            tem_whatsapp_integration=plano_config['tem_whatsapp_integration'],
            ordem=plano_config['ordem'],
            is_active=True,
        )
        
        # Associar ao tipo de loja
        plano.tipos_loja.add(tipo)
        
        print(f"  ✅ {plano_config['nome']} - R$ {plano_config['preco_mensal']}/mês")
        total_criados += 1

print(f"\n🎉 Total de planos criados: {total_criados}")
print(f"📊 Resumo: {tipos.count()} tipos × 4 planos = {tipos.count() * 4} planos")
