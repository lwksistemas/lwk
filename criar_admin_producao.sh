#!/bin/bash

# Script para criar admin da Clínica Harmonis em produção

echo "🔧 Criando admin da loja em produção..."

heroku run python backend/criar_admin_clinica.py --app lwksistemas

echo "✅ Concluído!"
