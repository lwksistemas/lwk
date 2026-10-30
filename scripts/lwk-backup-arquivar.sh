#!/bin/bash
# Tira o dump da pasta que a chave de produção enxerga e trava a cópia.
# A hora usada no alerta e na retenção é a de chegada, não a que o
# remetente gravou no arquivo. Link não é seguido. Um arquivo com erro
# não impede o restante nem o alerta.
set -u
IN=/var/backups/lwk
OUT=/var/backups/lwk-arquivo
PREP=/var/lib/lwk-backup-estado/preparo
LOG=/var/log/lwk-backup-arquivo.log
STAMP=/var/lib/lwk-backup-estado/alerta-stamp
MAX_BYTES=$((200 * 1024 * 1024))
IDADE_MAX=$((26 * 3600))
ESPERA=45
ALERTA_EMAIL="consultorluizfelix@hotmail.com"

log() { echo "$(date -Is) $*" >> "$LOG"; }

alert_atraso() {
  local newest now prev msg
  newest=$(find "$OUT" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1 || true)
  now=$(date +%s)
  if [ -n "$newest" ] && [ $((now - ${newest%.*})) -le "$IDADE_MAX" ]; then
    return 0
  fi
  prev=0
  [ -f "$STAMP" ] && prev=$(cat "$STAMP" 2>/dev/null || echo 0)
  if [ $((now - prev)) -lt 21600 ]; then
    return 0
  fi
  msg="Backup externo atrasado: o arquivo mais novo em /var/backups/lwk-arquivo tem mais de 26 horas."
  log "ALERTA: $msg"
  logger -t lwk-backup-arquivo "ALERTA: $msg"
  echo "$now" > "$STAMP" || true
  if [ ! -f /etc/lwk-backup-alerta.env ]; then
    log "ALERTA: e-mail não configurado na mídia"
    return 0
  fi
  set -a
  # shellcheck disable=SC1091
  . /etc/lwk-backup-alerta.env
  set +a
  if [ -z "${RESEND_API_KEY:-}" ] || [ -z "${DEFAULT_FROM_EMAIL:-}" ]; then
    log "ALERTA: e-mail sem chave na mídia"
    return 0
  fi
  if FROM="$DEFAULT_FROM_EMAIL" TO="$ALERTA_EMAIL" MSG="$msg" KEY="$RESEND_API_KEY" python3 - << 'PY'
import json, os, urllib.request
body = json.dumps({
    "from": os.environ["FROM"],
    "to": [os.environ["TO"]],
    "subject": "LWK Sistemas — backup externo atrasado",
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
urllib.request.urlopen(req, timeout=10).read()
PY
  then
    log "alerta enviado"
  else
    log "ALERTA: e-mail não enviado"
  fi
}

trap alert_atraso EXIT

if ! mountpoint -q "$IN"; then
  mount "$IN" >> "$LOG" 2>&1 || log "inbox nao montada"
fi
install -d -m 700 -o lwkbackup -g lwkbackup "$IN"
install -d -m 700 -o root -g root "$OUT"
install -d -m 700 -o root -g root /var/lib/lwk-backup-estado
install -d -m 700 -o root -g root "$PREP"

shopt -u dotglob
shopt -s nullglob
for f in "$IN"/*; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  case "$base" in
    .*) continue ;;
  esac
  if [ -L "$f" ]; then
    rm -f -- "$f" || log "falha ao remover link $base"
    log "descartado link $base"
    continue
  fi
  if [ ! -f "$f" ]; then
    log "descartado nao-arquivo $base"
    continue
  fi
  agora=$(date +%s)
  ctime=$(stat -c %Z -- "$f" 2>/dev/null || echo "$agora")
  if [ $((agora - ctime)) -lt "$ESPERA" ]; then
    continue
  fi
  staged="$PREP/${base}.$$"
  if ! mv -- "$f" "$staged"; then
    log "falha ao recolher $base"
    continue
  fi
  if [ -L "$staged" ]; then
    rm -f -- "$staged" || log "falha ao remover link recolhido $base"
    log "descartado link $base"
    continue
  fi
  size=$(stat -c %s -- "$staged" 2>/dev/null || echo 0)
  if [ "$size" -gt "$MAX_BYTES" ]; then
    rm -f -- "$staged" || log "falha ao apagar grande $base"
    log "descartado grande $base ($size bytes)"
    continue
  fi
  header=$(head -n 1 -- "$staged" 2>/dev/null || true)
  if [ "$header" != "age-encryption.org/v1" ]; then
    rm -f -- "$staged" || log "falha ao apagar nao-age $base"
    log "descartado nao-age $base"
    continue
  fi
  dest="$OUT/$base"
  if [ -e "$dest" ]; then
    dest="$OUT/${base}.dup-$(date +%Y%m%d%H%M%S%N)"
    log "repetido guardado $(basename "$dest")"
  else
    log "arquivado $base"
  fi
  chown -h root:root -- "$staged" || log "falha chown $base"
  chmod 600 -- "$staged" || log "falha chmod $base"
  touch -- "$staged" || log "falha touch $base"
  if ! mv -- "$staged" "$dest"; then
    log "falha ao arquivar $base"
    continue
  fi
  chattr +i -- "$dest" || log "falha chattr $base"
done

while IFS= read -r -d '' old; do
  if ! chattr -i -- "$old"; then
    log "falha ao soltar $(basename "$old")"
    continue
  fi
  if ! rm -f -- "$old"; then
    log "falha ao apagar $(basename "$old")"
    continue
  fi
  log "expirado $(basename "$old")"
done < <(find "$OUT" -type f -mtime +90 -print0)
