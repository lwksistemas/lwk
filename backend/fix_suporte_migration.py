#!/usr/bin/env python
"""
Corrige inconsistência: suporte.0001 aplicada antes de suporte.0000.
Insere 0000 em django_migrations para que o histórico fique consistente.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(
        "SELECT 1 FROM django_migrations WHERE app = 'suporte' AND name = '0000_create_schema_suporte'"
    )
    if cursor.fetchone():
        print("suporte.0000_create_schema_suporte já está registrada. Nada a fazer.")
        sys.exit(0)

    from django.utils import timezone
    now = timezone.now().isoformat()
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES ('suporte', '0000_create_schema_suporte', %s)",
        [now]
    )
    print("✅ Inserido suporte.0000_create_schema_suporte em django_migrations")
