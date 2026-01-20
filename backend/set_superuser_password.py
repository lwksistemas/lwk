#!/usr/bin/env python
"""
Script para definir senha do superusuário
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')
django.setup()

from django.contrib.auth.models import User

try:
    user = User.objects.get(username='superadmin')
    user.set_password('super123')
    user.save()
    print("✅ Senha do superadmin definida com sucesso!")
except User.DoesNotExist:
    print("❌ Usuário superadmin não encontrado")
except Exception as e:
    print(f"❌ Erro: {e}")