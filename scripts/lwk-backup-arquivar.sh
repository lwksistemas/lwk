#!/bin/bash
# Tira o dump da pasta que a chave de produção enxerga e trava a cópia.
# Repetido não é descartado: ganha o sufixo .dup-<carimbo>. Temporário
# oculto do rsync fica de fora. Acima de 200 MB ou sem cabeçalho age, sai.
# Retenção de 90 dias só aqui. Alerta se o mais novo tiver mais de 26 h.
set -eu
IN=/var/backups/lwk
OUT=/var/backups/lwk-arquivo
LOG=/var/log/lwk-backup-arquivo.log
STAMP=/var/lib/lwk-backup-estado/alerta-stamp
MAX_BYTES=$((200 * 1024 * 1024))
IDADE_MAX=$((26 * 3600))
ALERTA_EMAIL="consultorluizfelix@hotmail.com"

log() { echo "$(date -Is) $*" >> "$LOG"; }

if ! mountpoint -q "$IN"; then
  mount "$IN" >> "$LOG" 2>&1 || log "inbox nao montada"
fi
install -d -m 700 -o lwkbackup -g lwkbackup "$IN"
install -d -m 700 -o root -g root "$OUT"
install -d -m 700 -o root -g root /var/lib/lwk-backup-estado

# Sem dotglob: * não pega .arquivo. O teste abaixo cobre os dois casos.
shopt -u dotglob
shopt -s nullglob
for f in "$IN"/*; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  case "$base" in
    .*) continue ;;
  esac
  if [ -n "$(find "$f" -newermt "45 seconds ago" -print -quit)" ]; then
    continue
  fi
  size=$(stat -c %s "$f")
  if [ "$size" -gt "$MAX_BYTES" ]; then
    rm -f -- "$f"
    log "descartado grande $base ($size bytes)"
    continue
  fi
  header=$(head -n 1 -- "$f" || true)
  if [ "$header" != "age-encryption.org/v1" ]; then
    rm -f -- "$f"
    log "descartado nao-age $base"
    continue
  fi
  dest="$OUT/$base"
  if [ -e "$dest" ]; then
    dest="$OUT/${base}.dup-$(date +%Y%m%d%H%M%S)"
    log "repetido guardado $(basename "$dest")"
  else
    log "arquivado $base"
  fi
  mv -- "$f" "$dest"
  chown root:root "$dest"
  chmod 600 "$dest"
  chattr +i "$dest"
done

while IFS= read -r -d '' old; do
  chattr -i "$old"
  rm -f -- "$old"
  log "expirado $(basename "$old")"
done < <(find "$OUT" -type f -mtime +90 -print0)

newest=$(find "$OUT" -type f -printf '%T@\n' | sort -n | tail -1 || true)
now=$(date +%s)
if [ -z "$newest" ] || [ $((now - ${newest%.*})) -gt "$IDADE_MAX" ]; then
  prev=0
  [ -f "$STAMP" ] && prev=$(cat "$STAMP" 2>/dev/null || echo 0)
  if [ $((now - prev)) -ge 21600 ]; then
    msg="Backup externo atrasado: o arquivo mais novo em /var/backups/lwk-arquivo tem mais de 26 horas."
    log "ALERTA: $msg"
    logger -t lwk-backup-arquivo "ALERTA: $msg"
    echo "$now" > "$STAMP"
    if [ -f /etc/lwk-backup-alerta.env ]; then
      set -a
      # shellcheck disable=SC1091
      . /etc/lwk-backup-alerta.env
      set +a
      if [ -n "${RESEND_API_KEY:-}" ] && [ -n "${DEFAULT_FROM_EMAIL:-}" ]; then
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
      else
        log "ALERTA: e-mail sem chave na mídia"
      fi
    else
      log "ALERTA: e-mail não configurado na mídia"
    fi
  fi
fi
