#!/bin/bash
# Script para resetar senha do usuário andre em produção

echo "🔐 Resetando senha do usuário 'andre' para 'teste123'"
echo ""

heroku run python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()

try:
    user = User.objects.get(username='andre')
    user.set_password('teste123')
    user.save()
    print(f"✅ Senha do usuário '{user.username}' resetada com sucesso!")
    print(f"   Email: {user.email}")
    print(f"   Nova senha: teste123")
except User.DoesNotExist:
    print("❌ Usuário 'andre' não encontrado")
EOF
