#!/bin/sh
# Release Railway resiliente (lwks-backend / staging).
#
# Objetivo: migrate public/suporte e collectstatic são obrigatórios; migrate_all_lojas
# pode falhar em lojas legadas sem bloquear ensure_all nem corrigir_schema_*.
#
# Ordem:
#   1. migrate public + suporte (falha = aborta release)
#   2. migrate_all_lojas (best-effort)
#   3. ensure_all (sempre executa)
#   4. corrigir_schema_* por tipo de loja (best-effort — alinha beta/prod pós-migration)
#   5. setup_initial_data (best-effort)
#   6. collectstatic (falha = aborta release)

set -e

log_step() {
  echo ""
  echo "========== $* =========="
}

run_best_effort() {
  label=$1
  shift
  log_step "$label"
  if "$@"; then
    echo "OK: $label"
  else
    code=$?
    echo "WARN: $label falhou (exit $code) — continuando release" >&2
  fi
}

log_step "migrate public"
python manage.py migrate --noinput

log_step "migrate suporte"
python manage.py migrate --database=suporte --noinput

run_best_effort "migrate_all_lojas" python manage.py migrate_all_lojas

log_step "ensure_all"
python manage.py ensure_all

run_best_effort "corrigir_schema_clinica_beleza" python manage.py corrigir_schema_clinica_beleza
run_best_effort "corrigir_schema_crm" python manage.py corrigir_schema_crm

run_best_effort "setup_initial_data" python manage.py setup_initial_data

log_step "collectstatic"
python manage.py collectstatic --noinput

echo ""
echo "Release concluído."
