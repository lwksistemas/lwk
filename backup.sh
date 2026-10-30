#!/bin/bash
# Dump local às 03:00. A cópia externa só sai cifrada com age, para um
# usuário que não lê a pasta: ele só pode gravar. A chave privada do age
# não fica na máquina que recebe o arquivo.
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
  if [ -z "${BACKUP_OFFSITE_AGE_RECIPIENT:-}" ]; then
    echo "Backup local ok; copia externa sem destinatario age, nao enviada: $FILENAME" >&2
  else
    age -r "$BACKUP_OFFSITE_AGE_RECIPIENT" -o "$BACKUP_DIR/$FILENAME.age" "$BACKUP_DIR/$FILENAME"
    chmod 600 "$BACKUP_DIR/$FILENAME.age"
    SSH_CMD="${BACKUP_OFFSITE_SSH:-ssh -o BatchMode=yes -o IdentitiesOnly=yes}"
    if ! rsync -a --chmod=F600 -e "$SSH_CMD" \
      "$BACKUP_DIR/$FILENAME.age" "${BACKUP_OFFSITE_TARGET}/"; then
      echo "Backup local ok; copia externa falhou: $FILENAME.age" >&2
    fi
    rm -f "$BACKUP_DIR/$FILENAME.age"
  fi
fi
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.age" -mtime +7 -delete
echo "Backup: $FILENAME ($(du -h "$BACKUP_DIR/$FILENAME" | cut -f1))"
