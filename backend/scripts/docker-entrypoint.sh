#!/bin/sh
# Sobe como root só para ajustar as pastas graváveis e segue como o usuário app.
set -eu

if [ "$(id -u)" = "0" ]; then
  mkdir -p /app/media /app/staticfiles /run
  chown -R app:app /app/media /app/staticfiles
  if [ -f /etc/lwk-encryption.key ]; then
    install -m 400 -o app -g app /etc/lwk-encryption.key /run/lwk-encryption.key
    exec runuser -u app -- env FIELD_ENCRYPTION_KEY_FILE=/run/lwk-encryption.key "$@"
  fi
  exec runuser -u app -- "$@"
fi

exec "$@"
