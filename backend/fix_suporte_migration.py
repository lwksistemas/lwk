#!/usr/bin/env python
"""
Corrige inconsistências de migrations antes do migrate principal.

1. suporte.0001 aplicada antes de 0000: insere 0000 em django_migrations
2. servicos.0005: coluna loja_id já existe em produção - marca como aplicada
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.utils import timezone

fixed = []

with connection.cursor() as cursor:
    # 1. Suporte: 0000 antes de 0001
    cursor.execute(
        "SELECT 1 FROM django_migrations WHERE app = 'suporte' AND name = '0000_create_schema_suporte'"
    )
    if not cursor.fetchone():
        now = timezone.now().isoformat()
        cursor.execute(
            "INSERT INTO django_migrations (app, name, applied) VALUES ('suporte', '0000_create_schema_suporte', %s)",
            [now],
        )
        fixed.append("suporte.0000_create_schema_suporte")

    # 2. Servicos.0005: se loja_id já existe em servicos_categorias, marcar como aplicada
    cursor.execute(
        "SELECT 1 FROM django_migrations WHERE app = 'servicos' AND name = '0005_add_loja_isolation'"
    )
    if not cursor.fetchone():
        cursor.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'servicos_categorias' AND column_name = 'loja_id'
            """
        )
        if cursor.fetchone():
            now = timezone.now().isoformat()
            cursor.execute(
                "INSERT INTO django_migrations (app, name, applied) VALUES ('servicos', '0005_add_loja_isolation', %s)",
                [now],
            )
            fixed.append("servicos.0005_add_loja_isolation (coluna já existia)")

if fixed:
    print("✅ Corrigido:", ", ".join(fixed))
else:
    print("Nenhuma correção necessária.")
