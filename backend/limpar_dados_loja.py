#!/usr/bin/env python
"""
Script para limpar TODOS os dados de uma loja específica

ATENÇÃO: Este script é DESTRUTIVO e irá apagar TODOS os dados da loja!
Use com EXTREMO cuidado!

Uso:
    python backend/limpar_dados_loja.py --loja-slug "clinica-daniele-5860"
    python backend/limpar_dados_loja.py --loja-id 123
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from django.db import connection
from superadmin.models import Loja


def limpar_dados_loja(loja):
    """
    Limpa TODOS os dados de uma loja específica
    
    ATENÇÃO: Operação DESTRUTIVA!
    """
    print(f"\n{'='*80}")
    print(f"🗑️  LIMPEZA DE DADOS DA LOJA")
    print(f"{'='*80}")
    print(f"Loja: {loja.nome}")
    print(f"Slug: {loja.slug}")
    print(f"ID: {loja.id}")
    print(f"Tipo: {loja.tipo_loja.nome if loja.tipo_loja else 'N/A'}")
    print(f"Database: {loja.database_name}")
    print(f"{'='*80}\n")
    
    # Confirmação
    print("⚠️  ATENÇÃO: Esta operação irá APAGAR TODOS OS DADOS da loja!")
    print("⚠️  Isso inclui:")
    print("   - Clientes")
    print("   - Profissionais")
    print("   - Procedimentos")
    print("   - Agendamentos")
    print("   - Consultas")
    print("   - Evoluções")
    print("   - Anamneses")
    print("   - Funcionários (exceto o admin)")
    print("   - Bloqueios")
    print("   - Horários")
    print("   - Transações financeiras")
    print("   - Categorias financeiras")
    print("   - E TODOS os outros dados da loja")
    print()
    
    confirmacao = input("Digite 'CONFIRMAR' para prosseguir: ")
    if confirmacao != 'CONFIRMAR':
        print("❌ Operação cancelada.")
        return False
    
    print("\n🔄 Iniciando limpeza...")
    
    try:
        # Usar o banco da loja
        db_name = loja.database_name
        
        # Importar modelos da clínica
        from clinica_estetica.models import (
            Cliente, Profissional, Procedimento, Agendamento,
            Funcionario, ProtocoloProcedimento, EvolucaoPaciente,
            AnamnesesTemplate, Anamnese, HorarioFuncionamento,
            BloqueioAgenda, Consulta, HistoricoLogin,
            CategoriaFinanceira, Transacao
        )
        
        # Contar registros antes
        print("\n📊 Contagem ANTES da limpeza:")
        contagens_antes = {
            'Clientes': Cliente.objects.using(db_name).count(),
            'Profissionais': Profissional.objects.using(db_name).count(),
            'Procedimentos': Procedimento.objects.using(db_name).count(),
            'Agendamentos': Agendamento.objects.using(db_name).count(),
            'Consultas': Consulta.objects.using(db_name).count(),
            'Evoluções': EvolucaoPaciente.objects.using(db_name).count(),
            'Anamneses': Anamnese.objects.using(db_name).count(),
            'Templates Anamnese': AnamnesesTemplate.objects.using(db_name).count(),
            'Protocolos': ProtocoloProcedimento.objects.using(db_name).count(),
            'Funcionários': Funcionario.objects.using(db_name).count(),
            'Bloqueios': BloqueioAgenda.objects.using(db_name).count(),
            'Horários': HorarioFuncionamento.objects.using(db_name).count(),
            'Histórico Login': HistoricoLogin.objects.using(db_name).count(),
            'Categorias Financeiras': CategoriaFinanceira.objects.using(db_name).count(),
            'Transações': Transacao.objects.using(db_name).count(),
        }
        
        for nome, count in contagens_antes.items():
            print(f"   {nome}: {count}")
        
        # Deletar dados (ordem importa por causa de FKs)
        print("\n🗑️  Deletando dados...")
        
        # 1. Transações financeiras
        deleted = Transacao.objects.using(db_name).all().delete()
        print(f"   ✓ Transações: {deleted[0]} deletadas")
        
        # 2. Categorias financeiras
        deleted = CategoriaFinanceira.objects.using(db_name).all().delete()
        print(f"   ✓ Categorias Financeiras: {deleted[0]} deletadas")
        
        # 3. Histórico de login
        deleted = HistoricoLogin.objects.using(db_name).all().delete()
        print(f"   ✓ Histórico Login: {deleted[0]} deletados")
        
        # 4. Consultas
        deleted = Consulta.objects.using(db_name).all().delete()
        print(f"   ✓ Consultas: {deleted[0]} deletadas")
        
        # 5. Evoluções
        deleted = EvolucaoPaciente.objects.using(db_name).all().delete()
        print(f"   ✓ Evoluções: {deleted[0]} deletadas")
        
        # 6. Anamneses
        deleted = Anamnese.objects.using(db_name).all().delete()
        print(f"   ✓ Anamneses: {deleted[0]} deletadas")
        
        # 7. Templates de Anamnese
        deleted = AnamnesesTemplate.objects.using(db_name).all().delete()
        print(f"   ✓ Templates Anamnese: {deleted[0]} deletados")
        
        # 8. Agendamentos
        deleted = Agendamento.objects.using(db_name).all().delete()
        print(f"   ✓ Agendamentos: {deleted[0]} deletados")
        
        # 9. Bloqueios
        deleted = BloqueioAgenda.objects.using(db_name).all().delete()
        print(f"   ✓ Bloqueios: {deleted[0]} deletados")
        
        # 10. Horários
        deleted = HorarioFuncionamento.objects.using(db_name).all().delete()
        print(f"   ✓ Horários: {deleted[0]} deletados")
        
        # 11. Protocolos
        deleted = ProtocoloProcedimento.objects.using(db_name).all().delete()
        print(f"   ✓ Protocolos: {deleted[0]} deletados")
        
        # 12. Procedimentos
        deleted = Procedimento.objects.using(db_name).all().delete()
        print(f"   ✓ Procedimentos: {deleted[0]} deletados")
        
        # 13. Profissionais
        deleted = Profissional.objects.using(db_name).all().delete()
        print(f"   ✓ Profissionais: {deleted[0]} deletados")
        
        # 14. Clientes
        deleted = Cliente.objects.using(db_name).all().delete()
        print(f"   ✓ Clientes: {deleted[0]} deletados")
        
        # 15. Funcionários (MANTER O ADMIN - owner da loja)
        funcionarios_deletados = 0
        for func in Funcionario.objects.using(db_name).all():
            # Manter apenas o funcionário que é o owner da loja
            if func.user_id != loja.owner_id:
                func.delete()
                funcionarios_deletados += 1
        print(f"   ✓ Funcionários: {funcionarios_deletados} deletados (admin mantido)")
        
        # Contar registros depois
        print("\n📊 Contagem DEPOIS da limpeza:")
        contagens_depois = {
            'Clientes': Cliente.objects.using(db_name).count(),
            'Profissionais': Profissional.objects.using(db_name).count(),
            'Procedimentos': Procedimento.objects.using(db_name).count(),
            'Agendamentos': Agendamento.objects.using(db_name).count(),
            'Consultas': Consulta.objects.using(db_name).count(),
            'Evoluções': EvolucaoPaciente.objects.using(db_name).count(),
            'Anamneses': Anamnese.objects.using(db_name).count(),
            'Templates Anamnese': AnamnesesTemplate.objects.using(db_name).count(),
            'Protocolos': ProtocoloProcedimento.objects.using(db_name).count(),
            'Funcionários': Funcionario.objects.using(db_name).count(),
            'Bloqueios': BloqueioAgenda.objects.using(db_name).count(),
            'Horários': HorarioFuncionamento.objects.using(db_name).count(),
            'Histórico Login': HistoricoLogin.objects.using(db_name).count(),
            'Categorias Financeiras': CategoriaFinanceira.objects.using(db_name).count(),
            'Transações': Transacao.objects.using(db_name).count(),
        }
        
        for nome, count in contagens_depois.items():
            print(f"   {nome}: {count}")
        
        print("\n✅ Limpeza concluída com sucesso!")
        print(f"✅ A loja '{loja.nome}' está agora limpa e pronta para uso.")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO durante a limpeza: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpar dados de uma loja')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--loja-slug', help='Slug da loja')
    group.add_argument('--loja-id', type=int, help='ID da loja')
    
    args = parser.parse_args()
    
    # Buscar loja
    try:
        if args.loja_slug:
            loja = Loja.objects.get(slug=args.loja_slug)
        else:
            loja = Loja.objects.get(id=args.loja_id)
    except Loja.DoesNotExist:
        print(f"❌ Loja não encontrada!")
        sys.exit(1)
    
    # Limpar dados
    sucesso = limpar_dados_loja(loja)
    
    if sucesso:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
