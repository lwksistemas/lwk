#!/usr/bin/env python
"""
Script para auditar uso de Raw SQL no código.

Busca por padrões que podem bypassar o LojaIsolationManager:
- .raw()
- .extra()
- cursor.execute()
- connection.cursor()

Uso:
    python backend/scripts/auditar_raw_sql.py
"""
import os
import re
from pathlib import Path


def find_raw_sql_usage():
    """Busca por uso de raw SQL em todo o código."""
    
    patterns = [
        (r'\.raw\(', 'QuerySet.raw()'),
        (r'\.extra\(', 'QuerySet.extra()'),
        (r'cursor\.execute\(', 'cursor.execute()'),
        (r'connection\.cursor\(\)', 'connection.cursor()'),
        (r'connections\[', 'connections[]'),
    ]
    
    results = []
    backend_path = Path('backend')
    
    # Buscar em todos os arquivos Python
    for py_file in backend_path.rglob('*.py'):
        # Ignorar migrations e __pycache__
        if 'migrations' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for pattern, description in patterns:
                    if re.search(pattern, line):
                        results.append({
                            'file': str(py_file),
                            'line': line_num,
                            'code': line.strip(),
                            'pattern': description,
                        })
        except Exception as e:
            print(f"Erro ao ler {py_file}: {e}")
    
    return results


def main():
    print("=" * 80)
    print("AUDITORIA DE RAW SQL - SEGURANÇA MULTI-TENANT")
    print("=" * 80)
    print()
    
    results = find_raw_sql_usage()
    
    if not results:
        print("✅ Nenhum uso de Raw SQL encontrado!")
        return
    
    print(f"⚠️  Encontrados {len(results)} usos de Raw SQL:")
    print()
    
    # Agrupar por arquivo
    by_file = {}
    for result in results:
        file = result['file']
        if file not in by_file:
            by_file[file] = []
        by_file[file].append(result)
    
    for file, items in sorted(by_file.items()):
        print(f"\n📄 {file}")
        print("-" * 80)
        for item in items:
            print(f"  Linha {item['line']}: {item['pattern']}")
            print(f"    {item['code']}")
    
    print()
    print("=" * 80)
    print("RECOMENDAÇÕES:")
    print("=" * 80)
    print("1. Revisar cada uso de Raw SQL")
    print("2. Garantir que filtro por loja_id está presente")
    print("3. Considerar refatorar para usar ORM quando possível")
    print("4. Documentar queries que precisam ser raw")
    print()


if __name__ == '__main__':
    main()
