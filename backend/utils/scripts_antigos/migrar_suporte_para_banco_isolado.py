#!/usr/bin/env python
"""
Script para migrar dados de suporte do banco 'default' para banco 'suporte' isolado
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from suporte.models import Chamado, RespostaChamado

print("=" * 60)
print("MIGRAÇÃO DE DADOS: default → suporte")
print("=" * 60)

# Verificar dados no banco default
print("\n1. Verificando dados no banco 'default'...")
chamados_default = list(Chamado.objects.using('default').all())
respostas_default = list(RespostaChamado.objects.using('default').all())

print(f"   Chamados encontrados: {len(chamados_default)}")
print(f"   Respostas encontradas: {len(respostas_default)}")

if len(chamados_default) == 0:
    print("\n✅ Nenhum dado para migrar. Banco 'default' está limpo.")
    print("=" * 60)
    exit(0)

# Verificar dados no banco suporte
print("\n2. Verificando dados no banco 'suporte'...")
chamados_suporte = Chamado.objects.using('suporte').count()
respostas_suporte = RespostaChamado.objects.using('suporte').count()

print(f"   Chamados existentes: {chamados_suporte}")
print(f"   Respostas existentes: {respostas_suporte}")

# Migrar chamados
print("\n3. Migrando chamados...")
chamados_migrados = 0
for chamado in chamados_default:
    # Verificar se já existe no banco suporte
    if not Chamado.objects.using('suporte').filter(id=chamado.id).exists():
        # Criar no banco suporte
        Chamado.objects.using('suporte').create(
            id=chamado.id,
            titulo=chamado.titulo,
            descricao=chamado.descricao,
            tipo=chamado.tipo,
            status=chamado.status,
            prioridade=chamado.prioridade,
            loja_slug=chamado.loja_slug,
            loja_nome=chamado.loja_nome,
            usuario_nome=chamado.usuario_nome,
            usuario_email=chamado.usuario_email,
            atendente=chamado.atendente,
            created_at=chamado.created_at,
            updated_at=chamado.updated_at,
            resolvido_em=chamado.resolvido_em
        )
        chamados_migrados += 1
        print(f"   ✅ Chamado #{chamado.id} migrado")
    else:
        print(f"   ⏭️  Chamado #{chamado.id} já existe no banco suporte")

print(f"\n   Total migrado: {chamados_migrados} chamados")

# Migrar respostas
print("\n4. Migrando respostas...")
respostas_migradas = 0
for resposta in respostas_default:
    # Verificar se já existe no banco suporte
    if not RespostaChamado.objects.using('suporte').filter(id=resposta.id).exists():
        # Verificar se o chamado existe no banco suporte
        if Chamado.objects.using('suporte').filter(id=resposta.chamado_id).exists():
            # Criar no banco suporte
            RespostaChamado.objects.using('suporte').create(
                id=resposta.id,
                chamado_id=resposta.chamado_id,
                usuario_nome=resposta.usuario_nome,
                mensagem=resposta.mensagem,
                is_suporte=resposta.is_suporte,
                created_at=resposta.created_at
            )
            respostas_migradas += 1
            print(f"   ✅ Resposta #{resposta.id} migrada")
        else:
            print(f"   ⚠️  Resposta #{resposta.id} ignorada (chamado não existe)")
    else:
        print(f"   ⏭️  Resposta #{resposta.id} já existe no banco suporte")

print(f"\n   Total migrado: {respostas_migradas} respostas")

# Verificar resultado
print("\n5. Verificando resultado...")
chamados_final = Chamado.objects.using('suporte').count()
respostas_final = RespostaChamado.objects.using('suporte').count()

print(f"   Chamados no banco 'suporte': {chamados_final}")
print(f"   Respostas no banco 'suporte': {respostas_final}")

print("\n" + "=" * 60)
print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 60)
print("\nPróximos passos:")
print("1. Testar o sistema de suporte")
print("2. Se tudo funcionar, limpar dados do banco 'default'")
print("3. Fazer deploy no Heroku")
