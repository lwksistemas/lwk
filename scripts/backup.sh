#!/bin/bash
# Script de backup do banco de dados e logs

set -e

echo "💾 Iniciando backup do Sistema de Monitoramento..."

# Configurações
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="lwksistemas_db"
DB_USER="postgres"

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# 1. Backup do banco de dados
echo "📊 Fazendo backup do banco de dados..."
pg_dump -U $DB_USER -d $DB_NAME -F c -f "$BACKUP_DIR/db_backup_$DATE.dump"
echo "✓ Backup do banco salvo em: $BACKUP_DIR/db_backup_$DATE.dump"

# 2. Backup dos logs
echo "📝 Fazendo backup dos logs..."
tar -czf "$BACKUP_DIR/logs_backup_$DATE.tar.gz" backend/logs/
echo "✓ Backup dos logs salvo em: $BACKUP_DIR/logs_backup_$DATE.tar.gz"

# 3. Backup de arquivos de configuração
echo "⚙️  Fazendo backup das configurações..."
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
    backend/config/settings.py \
    backend/config/settings_production.py \
    .env 2>/dev/null || true
echo "✓ Backup das configurações salvo em: $BACKUP_DIR/config_backup_$DATE.tar.gz"

# 4. Limpar backups antigos (manter últimos 7 dias)
echo "🧹 Limpando backups antigos..."
find $BACKUP_DIR -name "*.dump" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
echo "✓ Backups antigos removidos"

# 5. Resumo
echo ""
echo "✅ Backup concluído com sucesso!"
echo ""
echo "📦 Arquivos criados:"
ls -lh $BACKUP_DIR/*$DATE*
echo ""
echo "💡 Para restaurar:"
echo "  pg_restore -U $DB_USER -d $DB_NAME $BACKUP_DIR/db_backup_$DATE.dump"
