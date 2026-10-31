#!/bin/bash
# Tira o dump da pasta que a chave de produção enxerga e trava a cópia.
# A hora do alerta e da retenção é a de chegada. Link não é seguido.
# A pasta de arquivo fica num volume próprio: no máximo 5 arquivos por
# dia e 50 MB cada. Um erro não impede os outros nem o alerta.
set -u
IN=/var/backups/lwk
OUT=/var/backups/lwk-arquivo
PREP=/var/lib/lwk-backup-estado/preparo
LOG=/var/log/lwk-backup-arquivo.log
STAMP=/var/lib/lwk-backup-estado/alerta-stamp
STAMP_VOLUME=/var/lib/lwk-backup-estado/alerta-volume-stamp
STAMP_COTA=/var/lib/lwk-backup-estado/alerta-cota-stamp
LOCK=/var/lib/lwk-backup-estado/job.lock
MAX_BYTES=$((50 * 1024 * 1024))
MAX_DIA=5
ALERTA_TOTAL=$((1024 * 1024 * 1024))
IDADE_MAX=$((26 * 3600))
ESPERA=45
ALERTA_EMAIL="consultorluizfelix@hotmail.com"

log() { echo "$(date -Is) $*" >> "$LOG"; }

syslog_alerta() {
  logger -t lwk-backup-arquivo "ALERTA: $*"
  log "ALERTA: $*"
}

pode_avisar() {
  local stamp="$1" now prev
  now=$(date +%s)
  prev=0
  [ -f "$stamp" ] && prev=$(cat "$stamp" 2>/dev/null || echo 0)
  if [ $((now - prev)) -lt 21600 ]; then
    return 1
  fi
  echo "$now" > "$stamp" || true
  return 0
}

alert_atraso() {
  local newest now msg used
  newest=$(find "$OUT" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1 || true)
  now=$(date +%s)
  if [ -z "$newest" ] || [ $((now - ${newest%.*})) -gt "$IDADE_MAX" ]; then
    if pode_avisar "$STAMP"; then
      msg="Backup externo atrasado: o arquivo mais novo em /var/backups/lwk-arquivo tem mais de 26 horas."
      syslog_alerta "$msg"
      if [ ! -f /etc/lwk-backup-alerta.env ]; then
        log "ALERTA: e-mail não configurado na mídia"
      else
        set -a
        # shellcheck disable=SC1091
        . /etc/lwk-backup-alerta.env
        set +a
        if [ -z "${RESEND_API_KEY:-}" ] || [ -z "${DEFAULT_FROM_EMAIL:-}" ]; then
          log "ALERTA: e-mail sem chave na mídia"
        elif FROM="$DEFAULT_FROM_EMAIL" TO="$ALERTA_EMAIL" MSG="$msg" KEY="$RESEND_API_KEY" python3 - << 'PY'
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
      fi
    fi
  fi
  if mountpoint -q "$OUT"; then
    used=$(df -B1 --output=used "$OUT" | tail -1 | tr -d ' ')
    if [ -n "$used" ] && [ "$used" -gt "$ALERTA_TOTAL" ]; then
      if pode_avisar "$STAMP_VOLUME"; then
        syslog_alerta "volume de arquivo acima de 1 GB ($used bytes)"
      fi
    fi
  else
    if pode_avisar "$STAMP_VOLUME"; then
      syslog_alerta "lwk-arquivo nao esta num volume proprio"
    fi
  fi
}

install -d -m 700 -o root -g root /var/lib/lwk-backup-estado
exec 9>>"$LOCK"
if ! flock -n 9; then
  exit 0
fi
trap alert_atraso EXIT

if ! mountpoint -q "$IN"; then
  mount "$IN" >> "$LOG" 2>&1 || log "inbox nao montada"
fi
if ! mountpoint -q "$OUT"; then
  mount "$OUT" >> "$LOG" 2>&1 || log "arquivo nao montado"
fi
install -d -m 700 -o lwkbackup -g lwkbackup "$IN"
install -d -m 700 -o root -g root "$OUT"
install -d -m 700 -o root -g root "$PREP"

arquivos_hoje() {
  find "$OUT" -type f -newermt "$(date +%Y-%m-%d) 00:00:00" -printf . 2>/dev/null | wc -c
}

shopt -u dotglob
shopt -s nullglob
for f in "$IN"/*; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  case "$base" in
    .*) continue ;;
    lost+found) continue ;;
  esac
  if [ -L "$f" ]; then
    rm -f -- "$f" || log "falha ao remover link $base"
    log "descartado link $base"
    continue
  fi
  if [ ! -f "$f" ]; then
    rm -f -- "$f" || log "falha ao remover nao-arquivo $base"
    log "removido nao-arquivo $base"
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
  if [ "$(arquivos_hoje)" -ge "$MAX_DIA" ]; then
    rm -f -- "$staged" || log "falha ao apagar cota $base"
    log "descartado cota-dia $base"
    if pode_avisar "$STAMP_COTA"; then
      syslog_alerta "cota de ${MAX_DIA} arquivos no dia; descartado $base"
    fi
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
  if ! chattr +i -- "$dest"; then
    syslog_alerta "arquivo arquivado sem trava imutavel: $base"
  fi
done

while IFS= read -r -d '' old; do
  if ! chattr -i -- "$old"; then
    syslog_alerta "nao consegui soltar imutavel $(basename "$old")"
    continue
  fi
  if ! rm -f -- "$old"; then
    log "falha ao apagar $(basename "$old")"
    continue
  fi
  log "expirado $(basename "$old")"
done < <(find "$OUT" -type f -mtime +90 -print0)
