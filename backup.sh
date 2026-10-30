#!/bin/bash
# Dump local às 03:00. A cópia externa só sai cifrada com age, para um
# usuário que não lê a pasta: ele só pode gravar. A chave privada do age
# não fica na máquina que recebe o arquivo.
set -eu
umask 077
BACKUP_DIR="/opt/lwk-erp/backups"
ALERTA_EMAIL="consultorluizfelix@hotmail.com"
MIN_BYTES=$((1024 * 1024))

alert_backup() {
  local msg="$1"
  echo "$msg" >&2
  local key from
  key=$(sed -n 's/^RESEND_API_KEY=//p' /opt/lwk-erp/.env | head -1 | tr -d "\"'")
  from=$(sed -n 's/^DEFAULT_FROM_EMAIL=//p' /opt/lwk-erp/.env | head -1 | tr -d "\"'")
  [ -n "$key" ] && [ -n "$from" ] || return 0
  if ! FROM="$from" TO="$ALERTA_EMAIL" MSG="$msg" KEY="$key" python3 - << 'PY'
import json, os, urllib.request
body = json.dumps({
    "from": os.environ["FROM"],
    "to": [os.environ["TO"]],
    "subject": "LWK Sistemas — backup externo",
    "text": os.environ["MSG"],
}).encode()
req = urllib.request.Request(
    "https://api.resend.com/emails",
    data=body,
    headers={
        "Authorization": "Bearer " + os.environ["KEY"],
        "Content-Type": "application/json",
    },
)
urllib.request.urlopen(req, timeout=15).read()
PY
  then
    echo "Backup: e-mail de alerta não enviado" >&2
  fi
}

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
FILENAME="lwk_$(date +%Y%m%d_%H%M%S).dump"
DUMP_OK=0
if ! docker compose -f /opt/lwk-erp/docker-compose.prod.yml exec -T postgres pg_dump -U lwk -Fc lwk > "$BACKUP_DIR/$FILENAME"; then
  rm -f "$BACKUP_DIR/$FILENAME"
  alert_backup "pg_dump falhou: $FILENAME"
else
  chmod 600 "$BACKUP_DIR/$FILENAME"
  SIZE=$(stat -c %s "$BACKUP_DIR/$FILENAME")
  if [ "$SIZE" -lt "$MIN_BYTES" ]; then
    rm -f "$BACKUP_DIR/$FILENAME"
    alert_backup "dump pequeno demais ($SIZE bytes): $FILENAME"
  else
    DUMP_OK=1
  fi
fi
if [ -f /etc/lwk-backup-offsite ]; then
  # shellcheck disable=SC1091
  . /etc/lwk-backup-offsite
fi
if [ "$DUMP_OK" = 1 ] && [ -n "${BACKUP_OFFSITE_TARGET:-}" ]; then
  if [ -z "${BACKUP_OFFSITE_AGE_RECIPIENT:-}" ]; then
    alert_backup "Backup local ok; copia externa sem destinatario age, nao enviada: $FILENAME"
  elif ! age -r "$BACKUP_OFFSITE_AGE_RECIPIENT" -o "$BACKUP_DIR/$FILENAME.age" "$BACKUP_DIR/$FILENAME"; then
    rm -f "$BACKUP_DIR/$FILENAME.age"
    alert_backup "age falhou: $FILENAME"
  else
    chmod 600 "$BACKUP_DIR/$FILENAME.age"
    SSH_CMD="${BACKUP_OFFSITE_SSH:-ssh -o BatchMode=yes -o IdentitiesOnly=yes}"
    if ! rsync -a --chmod=F600 -e "$SSH_CMD" \
      "$BACKUP_DIR/$FILENAME.age" "${BACKUP_OFFSITE_TARGET}/"; then
      alert_backup "Backup local ok; copia externa falhou: $FILENAME.age"
    fi
    rm -f "$BACKUP_DIR/$FILENAME.age"
  fi
fi
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.age" -mtime +7 -delete
if [ "$DUMP_OK" = 1 ]; then
  echo "Backup: $FILENAME ($(du -h "$BACKUP_DIR/$FILENAME" | cut -f1))"
fi
