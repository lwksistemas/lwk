#!/bin/bash
# Tira o dump da pasta que a chave de produção enxerga e trava a cópia.
# A hora do alerta e da retenção é a de chegada. Link não é seguido.
# A pasta de arquivo fica num volume próprio: no máximo 5 arquivos por
# dia e 50 MB cada. O que passar da cota vai para quarentena nesse
# mesmo volume (no máximo 10). Sem o volume montado, nada é gravado
# no disco do sistema. Um erro não impede os outros nem o alerta.
set -u
IN=/var/backups/lwk
OUT=/var/backups/lwk-arquivo
QUAR=/var/backups/lwk-arquivo/quarentena
PREP=/var/lib/lwk-backup-estado/preparo
LOG=/var/log/lwk-backup-arquivo.log
STAMP=/var/lib/lwk-backup-estado/alerta-stamp
STAMP_VOLUME=/var/lib/lwk-backup-estado/alerta-volume-stamp
STAMP_COTA=/var/lib/lwk-backup-estado/alerta-cota-stamp
LOCK=/var/lib/lwk-backup-estado/job.lock
MAX_BYTES=$((50 * 1024 * 1024))
MAX_DIA=5
MAX_QUAR=10
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
  if ! mountpoint -q "$OUT"; then
    if pode_avisar "$STAMP_VOLUME"; then
      syslog_alerta "lwk-arquivo nao esta num volume proprio"
    fi
    return 0
  fi
  newest=$(find "$OUT" -xdev -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1 || true)
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
  used=$(df -B1 --output=used "$OUT" | tail -1 | tr -d ' ')
  if [ -n "$used" ] && [ "$used" -gt "$ALERTA_TOTAL" ]; then
    if pode_avisar "$STAMP_VOLUME"; then
      syslog_alerta "volume de arquivo acima de 1 GB ($used bytes)"
    fi
  fi
}

install -d -m 700 -o root -g root /var/lib/lwk-backup-estado
exec 9>>"$LOCK"
if ! flock -n 9; then
  exit 0
fi
trap alert_atraso EXIT

exigir_volume() {
  local ponto="$1" msg="$2"
  if ! mountpoint -q "$ponto"; then
    mount "$ponto" >> "$LOG" 2>&1 || true
  fi
  if mountpoint -q "$ponto"; then
    return 0
  fi
  if pode_avisar "$STAMP_VOLUME"; then
    syslog_alerta "$msg"
  fi
  exit 0
}

exigir_volume "$IN" "entrada de backup nao montada; nada foi arquivado"
exigir_volume "$OUT" "lwk-arquivo nao esta num volume proprio; nada foi arquivado"
install -d -m 700 -o lwkbackup -g lwkbackup "$IN"
install -d -m 700 -o root -g root "$OUT"
install -d -m 700 -o root -g root "$PREP"
if [ -L "$QUAR" ]; then
  rm -f -- "$QUAR"
fi
install -d -m 700 -o root -g root "$QUAR"

arquivos_hoje() {
  find "$OUT" -maxdepth 1 -xdev -type f -newermt "$(date +%Y-%m-%d) 00:00:00" -printf . 2>/dev/null | wc -c
}

na_quarentena() {
  find "$QUAR" -maxdepth 1 -xdev -type f -printf . 2>/dev/null | wc -c
}

publicar() {
  local staged="$1" dest="$2" base="$3"
  chown -h root:root -- "$staged" || log "falha chown $base"
  chmod 600 -- "$staged" || log "falha chmod $base"
  touch -- "$staged" || log "falha touch $base"
  if ! mv -- "$staged" "$dest"; then
    rm -f -- "$staged" 2>>"$LOG" || true
    log "falha ao arquivar $base"
    if pode_avisar "$STAMP_VOLUME"; then
      syslog_alerta "nao coube no volume de arquivo: $base"
    fi
    return 1
  fi
  if ! chattr +i -- "$dest"; then
    syslog_alerta "arquivo arquivado sem trava imutavel: $(basename "$dest")"
  fi
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
    if rm -f -- "$f" 2>>"$LOG"; then
      log "descartado link $base"
    else
      log "falha ao remover link $base"
    fi
    continue
  fi
  if [ ! -f "$f" ]; then
    if rm -rf --one-file-system -- "$f" 2>>"$LOG"; then
      log "removido nao-arquivo $base"
    else
      log "falha ao remover nao-arquivo $base"
    fi
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
    if rm -f -- "$staged" 2>>"$LOG"; then
      log "descartado link $base"
    else
      log "falha ao remover link recolhido $base"
    fi
    continue
  fi
  size=$(stat -c %s -- "$staged" 2>/dev/null || echo 0)
  if [ "$size" -gt "$MAX_BYTES" ]; then
    if rm -f -- "$staged" 2>>"$LOG"; then
      log "descartado grande $base ($size bytes)"
    else
      log "falha ao apagar grande $base"
    fi
    continue
  fi
  header=$(head -n 1 -- "$staged" 2>/dev/null || true)
  if [ "$header" != "age-encryption.org/v1" ]; then
    if rm -f -- "$staged" 2>>"$LOG"; then
      log "descartado nao-age $base"
    else
      log "falha ao apagar nao-age $base"
    fi
    continue
  fi
  lugar="$OUT"
  if [ "$(arquivos_hoje)" -ge "$MAX_DIA" ]; then
    if [ "$(na_quarentena)" -ge "$MAX_QUAR" ]; then
      if rm -f -- "$staged" 2>>"$LOG"; then
        log "descartado cota-dia $base"
      else
        log "falha ao apagar cota $base"
      fi
      if pode_avisar "$STAMP_COTA"; then
        syslog_alerta "cota de ${MAX_DIA} no dia e quarentena com ${MAX_QUAR}; descartado $base"
      fi
      continue
    fi
    lugar="$QUAR"
  fi
  dest="$lugar/$base"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    dest="$lugar/${base}.dup-$(date +%Y%m%d%H%M%S%N)"
    nota="repetido guardado $(basename "$dest")"
  elif [ "$lugar" = "$QUAR" ]; then
    nota="quarentena $base"
  else
    nota="arquivado $base"
  fi
  if ! publicar "$staged" "$dest" "$base"; then
    continue
  fi
  log "$nota"
  if [ "$lugar" = "$QUAR" ]; then
    syslog_alerta "cota de ${MAX_DIA} arquivos no dia; $(basename "$dest") ficou em quarentena"
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
done < <(find "$OUT" -xdev -type f -mtime +90 -print0)
