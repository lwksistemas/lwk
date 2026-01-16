#!/usr/bin/env python
"""
Script para criar chamados de teste no banco de suporte
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from suporte.models import Chamado, RespostaChamado
from django.contrib.auth.models import User

print("=" * 60)
print("CRIANDO CHAMADOS DE TESTE")
print("=" * 60)

# Criar chamados de teste
chamados_data = [
    {
        'titulo': 'Problema com pagamento',
        'descricao': 'Não consigo processar pagamentos via cartão de crédito',
        'status': 'aberto',
        'prioridade': 'alta',
        'loja_slug': 'loja-tech',
        'loja_nome': 'Loja Tech',
        'usuario_nome': 'Admin Tech',
        'usuario_email': 'admin@lojatech.com',
    },
    {
        'titulo': 'Dúvida sobre estoque',
        'descricao': 'Como faço para importar produtos em massa?',
        'status': 'em_andamento',
        'prioridade': 'media',
        'loja_slug': 'moda-store',
        'loja_nome': 'Moda Store',
        'usuario_nome': 'Admin Moda',
        'usuario_email': 'admin@modastore.com',
    },
    {
        'titulo': 'Erro ao gerar relatório',
        'descricao': 'O relatório de vendas não está sendo gerado',
        'status': 'aberto',
        'prioridade': 'baixa',
        'loja_slug': 'loja-tech',
        'loja_nome': 'Loja Tech',
        'usuario_nome': 'Admin Tech',
        'usuario_email': 'admin@lojatech.com',
    },
    {
        'titulo': 'Sistema lento',
        'descricao': 'O sistema está muito lento para carregar produtos',
        'status': 'resolvido',
        'prioridade': 'media',
        'loja_slug': 'moda-store',
        'loja_nome': 'Moda Store',
        'usuario_nome': 'Admin Moda',
        'usuario_email': 'admin@modastore.com',
    },
    {
        'titulo': 'Integração com WhatsApp',
        'descricao': 'Preciso integrar minha loja com WhatsApp Business',
        'status': 'aberto',
        'prioridade': 'urgente',
        'loja_slug': 'loja-exemplo',
        'loja_nome': 'Loja Exemplo',
        'usuario_nome': 'Admin Exemplo',
        'usuario_email': 'admin@exemplo.com',
    },
]

for chamado_data in chamados_data:
    chamado, created = Chamado.objects.using('suporte').get_or_create(
        titulo=chamado_data['titulo'],
        loja_slug=chamado_data['loja_slug'],
        defaults=chamado_data
    )
    
    if created:
        print(f"✅ Chamado criado: {chamado.titulo} ({chamado.loja_nome})")
        
        # Adicionar resposta se estiver em andamento ou resolvido
        if chamado.status in ['em_andamento', 'resolvido']:
            RespostaChamado.objects.using('suporte').create(
                chamado=chamado,
                usuario_nome='Equipe Suporte',
                mensagem='Estamos analisando seu chamado e em breve retornaremos.',
                is_suporte=True
            )
            print(f"   ↳ Resposta adicionada")
    else:
        print(f"ℹ️  Chamado já existe: {chamado.titulo}")

print("\n" + "=" * 60)
print("✅ CHAMADOS DE TESTE CRIADOS!")
print("=" * 60)
print("\n📝 Acesse o Dashboard de Suporte:")
print("   URL: http://localhost:3000/suporte/dashboard")
print("   Usuário: suporte")
print("   Senha: suporte123")
print("\n" + "=" * 60)
