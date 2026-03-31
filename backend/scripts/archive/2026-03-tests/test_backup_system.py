#!/usr/bin/env python
"""
Script de Teste do Sistema de Backup

Testa todas as funcionalidades implementadas:
- Criação de configuração
- Verificação de modelos
- Métodos auxiliares
- Validações

Execute: python test_backup_system.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from superadmin.models import Loja, ConfiguracaoBackup, HistoricoBackup
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, time


def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def test_models_exist():
    """Testa se os modelos foram criados corretamente"""
    print_header("Teste 1: Verificar Modelos")
    
    try:
        # Verificar se tabelas existem
        config_count = ConfiguracaoBackup.objects.count()
        historico_count = HistoricoBackup.objects.count()
        
        print(f"✅ ConfiguracaoBackup: {config_count} registros")
        print(f"✅ HistoricoBackup: {historico_count} registros")
        print("✅ Modelos criados com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar modelos: {e}")
        return False


def test_create_configuration():
    """Testa criação de configuração de backup"""
    print_header("Teste 2: Criar Configuração de Backup")
    
    try:
        # Buscar primeira loja
        loja = Loja.objects.first()
        
        if not loja:
            print("⚠️ Nenhuma loja encontrada. Crie uma loja primeiro.")
            return False
        
        # Criar ou buscar configuração
        config, created = ConfiguracaoBackup.objects.get_or_create(
            loja=loja,
            defaults={
                'backup_automatico_ativo': True,
                'horario_envio': time(3, 0, 0),
                'frequencia': 'semanal',
                'dia_semana': 0,
                'incluir_imagens': False,
                'manter_ultimos_n_backups': 5
            }
        )
        
        if created:
            print(f"✅ Configuração criada para loja: {loja.nome}")
        else:
            print(f"✅ Configuração já existe para loja: {loja.nome}")
        
        print(f"   - Backup automático: {'Ativo' if config.backup_automatico_ativo else 'Inativo'}")
        print(f"   - Horário: {config.horario_envio}")
        print(f"   - Frequência: {config.get_frequencia_display()}")
        print(f"   - Total de backups: {config.total_backups_realizados}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao criar configuração: {e}")
        return False


def test_configuration_methods():
    """Testa métodos da ConfiguracaoBackup"""
    print_header("Teste 3: Métodos da Configuração")
    
    try:
        config = ConfiguracaoBackup.objects.first()
        
        if not config:
            print("⚠️ Nenhuma configuração encontrada")
            return False
        
        # Testar deve_executar_backup_hoje()
        deve_executar = config.deve_executar_backup_hoje()
        print(f"✅ deve_executar_backup_hoje(): {deve_executar}")
        
        # Testar incrementar_contador()
        contador_antes = config.total_backups_realizados
        config.incrementar_contador()
        config.refresh_from_db()
        contador_depois = config.total_backups_realizados
        
        print(f"✅ incrementar_contador(): {contador_antes} → {contador_depois}")
        print(f"✅ Último backup: {config.ultimo_backup}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar métodos: {e}")
        return False


def test_create_historico():
    """Testa criação de histórico de backup"""
    print_header("Teste 4: Criar Histórico de Backup")
    
    try:
        loja = Loja.objects.first()
        
        if not loja:
            print("⚠️ Nenhuma loja encontrada")
            return False
        
        # Criar histórico de teste
        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo='manual',
            status='processando',
            arquivo_nome='backup_teste.zip'
        )
        
        print(f"✅ Histórico criado: ID {historico.id}")
        print(f"   - Loja: {historico.loja.nome}")
        print(f"   - Tipo: {historico.get_tipo_display()}")
        print(f"   - Status: {historico.get_status_display()}")
        
        # Testar marcar_como_concluido()
        historico.marcar_como_concluido(
            tamanho_mb=15.5,
            total_registros=1234,
            tabelas={'clientes': 100, 'produtos': 50}
        )
        
        print(f"✅ Marcado como concluído:")
        print(f"   - Tamanho: {historico.get_tamanho_formatado()}")
        print(f"   - Registros: {historico.total_registros}")
        print(f"   - Tempo: {historico.get_tempo_processamento_formatado()}")
        
        # Limpar teste
        historico.delete()
        print(f"✅ Histórico de teste removido")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao criar histórico: {e}")
        return False


def test_historico_methods():
    """Testa métodos do HistoricoBackup"""
    print_header("Teste 5: Métodos do Histórico")
    
    try:
        loja = Loja.objects.first()
        
        if not loja:
            print("⚠️ Nenhuma loja encontrada")
            return False
        
        # Criar histórico de teste
        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo='automatico',
            status='processando',
            arquivo_nome='backup_teste_metodos.zip'
        )
        
        # Testar marcar_como_erro()
        historico.marcar_como_erro("Erro de teste")
        print(f"✅ marcar_como_erro(): Status = {historico.status}")
        print(f"   - Erro: {historico.erro_mensagem}")
        
        # Testar marcar_email_enviado()
        historico.marcar_email_enviado("teste@example.com")
        print(f"✅ marcar_email_enviado(): {historico.email_enviado}")
        print(f"   - Destinatário: {historico.email_destinatario}")
        
        # Limpar teste
        historico.delete()
        print(f"✅ Histórico de teste removido")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar métodos: {e}")
        return False


def test_validations():
    """Testa validações dos modelos"""
    print_header("Teste 6: Validações")
    
    try:
        from django.core.exceptions import ValidationError
        
        loja = Loja.objects.first()
        
        if not loja:
            print("⚠️ Nenhuma loja encontrada")
            return False
        
        # Testar validação de dia_semana para backup semanal
        config = ConfiguracaoBackup(
            loja=loja,
            frequencia='semanal',
            dia_semana=None  # Inválido
        )
        
        try:
            config.full_clean()
            print("❌ Validação deveria ter falhado (dia_semana obrigatório)")
            return False
        except ValidationError as e:
            print(f"✅ Validação funcionou: {e.message_dict.get('dia_semana', [''])[0]}")
        
        # Testar validação de dia_mes para backup mensal
        config2 = ConfiguracaoBackup(
            loja=loja,
            frequencia='mensal',
            dia_mes=35  # Inválido (deve ser 1-28)
        )
        
        try:
            config2.full_clean()
            print("❌ Validação deveria ter falhado (dia_mes inválido)")
            return False
        except ValidationError as e:
            print(f"✅ Validação funcionou: {e.message_dict.get('dia_mes', [''])[0]}")
        
        print("✅ Todas as validações funcionando corretamente!")
        return True
    except Exception as e:
        print(f"❌ Erro ao testar validações: {e}")
        return False


def test_summary():
    """Mostra resumo dos testes"""
    print_header("Resumo do Sistema")
    
    try:
        total_lojas = Loja.objects.count()
        total_configs = ConfiguracaoBackup.objects.count()
        total_historico = HistoricoBackup.objects.count()
        configs_ativas = ConfiguracaoBackup.objects.filter(backup_automatico_ativo=True).count()
        
        print(f"📊 Estatísticas:")
        print(f"   - Total de lojas: {total_lojas}")
        print(f"   - Configurações de backup: {total_configs}")
        print(f"   - Backups automáticos ativos: {configs_ativas}")
        print(f"   - Histórico de backups: {total_historico}")
        
        if total_configs > 0:
            config = ConfiguracaoBackup.objects.first()
            print(f"\n📋 Exemplo de Configuração:")
            print(f"   - Loja: {config.loja.nome}")
            print(f"   - Status: {'Ativo' if config.backup_automatico_ativo else 'Inativo'}")
            print(f"   - Frequência: {config.get_frequencia_display()}")
            print(f"   - Horário: {config.horario_envio}")
            print(f"   - Total de backups: {config.total_backups_realizados}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar resumo: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 70)
    print("  🧪 TESTE DO SISTEMA DE BACKUP")
    print("=" * 70)
    
    results = []
    
    # Executar testes
    results.append(("Verificar Modelos", test_models_exist()))
    results.append(("Criar Configuração", test_create_configuration()))
    results.append(("Métodos da Configuração", test_configuration_methods()))
    results.append(("Criar Histórico", test_create_historico()))
    results.append(("Métodos do Histórico", test_historico_methods()))
    results.append(("Validações", test_validations()))
    results.append(("Resumo", test_summary()))
    
    # Mostrar resultados
    print_header("Resultados dos Testes")
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Total: {passed} passaram, {failed} falharam")
    
    if failed == 0:
        print("\n🎉 Todos os testes passaram! Sistema funcionando perfeitamente!")
    else:
        print(f"\n⚠️ {failed} teste(s) falharam. Verifique os erros acima.")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
