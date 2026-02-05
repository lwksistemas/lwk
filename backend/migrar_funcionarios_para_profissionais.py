#!/usr/bin/env python
"""
Script para migrar Funcionários com funcao='profissional' para a tabela Profissional
Solução temporária até fazer a migração completa do banco de dados
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from cabeleireiro.models import Funcionario, Profissional

def migrar_funcionarios():
    """Migra funcionários profissionais para tabela de profissionais"""
    
    # Buscar todos os funcionários com função 'profissional'
    funcionarios_profissionais = Funcionario.objects.filter(funcao='profissional')
    
    print(f"📋 Encontrados {funcionarios_profissionais.count()} funcionários profissionais")
    
    migrados = 0
    ja_existentes = 0
    
    for func in funcionarios_profissionais:
        # Verificar se já existe um profissional com mesmo email/nome
        profissional_existe = Profissional.objects.filter(
            loja_id=func.loja_id,
            email=func.email
        ).first()
        
        if profissional_existe:
            print(f"⚠️  Profissional já existe: {func.nome} (ID: {profissional_existe.id})")
            ja_existentes += 1
            continue
        
        # Criar profissional
        profissional = Profissional.objects.create(
            loja_id=func.loja_id,
            nome=func.nome,
            email=func.email,
            telefone=func.telefone,
            especialidade=func.especialidade or 'Geral',
            comissao_percentual=func.comissao_percentual,
            is_active=func.is_active
        )
        
        print(f"✅ Migrado: {func.nome} → Profissional ID: {profissional.id}")
        migrados += 1
    
    print(f"\n📊 Resumo:")
    print(f"   ✅ Migrados: {migrados}")
    print(f"   ⚠️  Já existentes: {ja_existentes}")
    print(f"   📋 Total: {funcionarios_profissionais.count()}")

if __name__ == '__main__':
    print("🔄 Iniciando migração de Funcionários → Profissionais\n")
    migrar_funcionarios()
    print("\n✅ Migração concluída!")
