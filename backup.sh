#!/bin/bash
# Dump local às 03:00. Se /etc/lwk-backup-offsite definir BACKUP_OFFSITE_TARGET,
# a mesma cópia segue para outra máquina. O arquivo fica 600 nos dois lados.
set -eu
BACKUP_DIR="/opt/lwk-erp/backups"
mkdir -p "$BACKUP_DIR"
FILENAME="lwk_$(date +%Y%m%d_%H%M%S).dump"
docker compose -f /opt/lwk-erp/docker-compose.prod.yml exec -T postgres pg_dump -U lwk -Fc lwk > "$BACKUP_DIR/$FILENAME"
chmod 600 "$BACKUP_DIR/$FILENAME"
if [ -f /etc/lwk-backup-offsite ]; then
  # shellcheck disable=SC1091
  . /etc/lwk-backup-offsite
fi
if [ -n "${BACKUP_OFFSITE_TARGET:-}" ]; then
  if ! rsync -a --chmod=F600 -e "ssh -o BatchMode=yes -o IdentitiesOnly=yes" \
    "$BACKUP_DIR/$FILENAME" "${BACKUP_OFFSITE_TARGET}/"; then
    echo "Backup local ok; copia externa falhou: $FILENAME" >&2
  fi
fi
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
echo "Backup: $FILENAME ($(du -h "$BACKUP_DIR/$FILENAME" | cut -f1))"
