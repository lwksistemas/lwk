#!/usr/bin/env python
"""
Script para limpar todos os dados de uma loja específica
Mantém a loja ativa, mas remove todos os cadastros
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja

def limpar_dados_loja(loja_slug: str):
    """
    Limpa todos os dados de uma loja específica
    """
    try:
        loja = Loja.objects.get(slug=loja_slug)
        print(f'\n{"="*60}')
        print(f'LIMPANDO DADOS DA LOJA: {loja.nome} ({loja_slug})')
        print(f'Tipo: {loja.tipo_loja.nome}')
        print(f'Database: {loja.database_name}')
        print(f'{"="*60}\n')
        
        if not loja.database_created:
            print('⚠️ Loja não tem banco isolado - dados no banco principal')
            return
        
        db_name = loja.database_name
        
        # Conectar ao banco da loja
        with connection.cursor() as cursor:
            cursor.execute(f"ATTACH DATABASE '{db_name}' AS loja_db")
            
            # Listar todas as tabelas da Clínica da Beleza
            tabelas = [
                'clinica_beleza_payment',
                'clinica_beleza_appointment',
                'clinica_beleza_bloqueiohorario',
                'clinica_beleza_procedure',
                'clinica_beleza_professional',
                'clinica_beleza_patient',
            ]
            
            total_deletado = 0
            
            for tabela in tabelas:
                try:
                    # Contar registros antes
                    cursor.execute(f"SELECT COUNT(*) FROM loja_db.{tabela}")
                    count_antes = cursor.fetchone()[0]
                    
                    if count_antes > 0:
                        # Deletar todos os registros
                        cursor.execute(f"DELETE FROM loja_db.{tabela}")
                        print(f'✅ {tabela}: {count_antes} registro(s) deletado(s)')
                        total_deletado += count_antes
                    else:
                        print(f'ℹ️  {tabela}: já estava vazia')
                        
                except Exception as e:
                    print(f'⚠️ {tabela}: {e}')
            
            cursor.execute("DETACH DATABASE loja_db")
            
            print(f'\n{"="*60}')
            print(f'✅ LIMPEZA CONCLUÍDA!')
            print(f'Total de registros deletados: {total_deletado}')
            print(f'{"="*60}\n')
            
    except Loja.DoesNotExist:
        print(f'\n❌ Loja "{loja_slug}" não encontrada!\n')
    except Exception as e:
        print(f'\n❌ Erro: {e}\n')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print('\nUso: python limpar_dados_loja.py <slug-da-loja>')
        print('Exemplo: python limpar_dados_loja.py linda-mulhet-1845\n')
        sys.exit(1)
    
    loja_slug = sys.argv[1]
    
    # Confirmação
    resposta = input(f'\n⚠️  ATENÇÃO: Isso vai deletar TODOS os dados da loja "{loja_slug}"!\nDeseja continuar? (sim/não): ')
    
    if resposta.lower() in ['sim', 's', 'yes', 'y']:
        limpar_dados_loja(loja_slug)
    else:
        print('\n❌ Operação cancelada.\n')
