#!/usr/bin/env python
"""
Script para migrar funcionários profissionais para tabela de profissionais
Executa diretamente no banco sem usar o LojaIsolationManager
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def migrar_profissionais():
    print('🔄 Iniciando migração direta...\n')
    
    with connection.cursor() as cursor:
        # Buscar funcionários profissionais diretamente
        cursor.execute("""
            SELECT id, loja_id, nome, email, telefone, especialidade, comissao_percentual, is_active
            FROM cabeleireiro_funcionarios
            WHERE funcao = 'profissional'
        """)
        
        funcionarios = cursor.fetchall()
        print(f'📋 Encontrados {len(funcionarios)} funcionários profissionais\n')
        
        migrados = 0
        ja_existentes = 0
        
        for func in funcionarios:
            func_id, loja_id, nome, email, telefone, especialidade, comissao, is_active = func
            
            # Verificar se já existe
            cursor.execute("""
                SELECT id FROM cabeleireiro_profissionais
                WHERE loja_id = %s AND email = %s
            """, [loja_id, email])
            
            existe = cursor.fetchone()
            
            if existe:
                print(f'⚠️  Já existe: {nome} (ID: {existe[0]})')
                ja_existentes += 1
                continue
            
            # Criar profissional
            cursor.execute("""
                INSERT INTO cabeleireiro_profissionais 
                (loja_id, nome, email, telefone, especialidade, comissao_percentual, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            """, [loja_id, nome, email, telefone, especialidade or 'Geral', comissao, is_active])
            
            prof_id = cursor.fetchone()[0]
            print(f'✅ Criado: {nome} (Func ID: {func_id} → Prof ID: {prof_id})')
            migrados += 1
    
    print('\n📊 Resumo:')
    print(f'   ✅ Migrados: {migrados}')
    print(f'   ⚠️  Já existentes: {ja_existentes}')
    print(f'   📋 Total: {len(funcionarios)}')
    print('\n✅ Migração concluída!')

if __name__ == '__main__':
    migrar_profissionais()
