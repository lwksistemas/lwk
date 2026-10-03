#!/usr/bin/env bash
# Migra os dados da Evolution do servidor LWK (wksistemas) para a VM dedicada.
#
# RODAR NA SUA MÁQUINA LOCAL (a que já tem acesso SSH aos dois servidores).
# Assim não é preciso configurar chave SSH cruzada entre as VMs.
#
# Transfere:
#   1. Dump do banco `evolution` (instâncias + credenciais de sessão no Postgres)
#   2. Volume de sessões Baileys (/evolution/instances) — auth do WhatsApp
# Migrar os dois é o que evita as lojas terem de reescanear o QR Code.
#
# Pré-requisitos:
#   - Containers da VM nova no ar: docker compose up -d (postgres saudável)
#   - Seu ~/.ssh com acesso a: deploy@<wksistemas> e ubuntu@<vm-evolution>
#
# Uso:
#   bash 02-migrar-dados.sh
set -euo pipefail

# --- Origem (wksistemas) ---
SRC="${SRC:-deploy@201.23.81.50}"
SRC_PG_CONTAINER="${SRC_PG_CONTAINER:-lwk-erp-postgres-1}"
SRC_EVO_CONTAINER="${SRC_EVO_CONTAINER:-lwk-erp-evolution-1}"

# --- Destino (VM Evolution) ---
DST="${DST:-ubuntu@169.150.0.111}"
DST_PG_CONTAINER="${DST_PG_CONTAINER:-evolution-postgres}"
DST_EVO_CONTAINER="${DST_EVO_CONTAINER:-evolution-api}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> Origem:  $SRC   ($SRC_PG_CONTAINER / $SRC_EVO_CONTAINER)"
echo "==> Destino: $DST   ($DST_PG_CONTAINER / $DST_EVO_CONTAINER)"
echo

echo "==> [1/6] Dump do banco 'evolution' (origem)"
ssh "$SRC" "docker exec $SRC_PG_CONTAINER pg_dump -U lwk --clean --if-exists evolution" > "$WORKDIR/evolution.sql"
echo "    dump: $(du -h "$WORKDIR/evolution.sql" | cut -f1)"

echo "==> [2/6] Empacotando sessões Baileys (/evolution/instances) (origem)"
ssh "$SRC" "docker exec $SRC_EVO_CONTAINER sh -c 'cd /evolution && tar czf - instances'" > "$WORKDIR/instances.tgz" 2>/dev/null || {
  echo "    (aviso) /evolution/instances vazio ou inacessível — seguindo só com o banco."
  : > "$WORKDIR/instances.tgz"
}
echo "    instances: $(du -h "$WORKDIR/instances.tgz" | cut -f1)"

echo "==> [3/6] Enviando arquivos para a VM nova"
scp -q "$WORKDIR/evolution.sql" "$WORKDIR/instances.tgz" "$DST:/tmp/"

echo "==> [4/6] Restaurando banco no Postgres da VM nova"
ssh "$DST" "cat /tmp/evolution.sql | docker exec -i $DST_PG_CONTAINER psql -U evolution -d evolution"
echo "    banco restaurado"

echo "==> [5/6] Restaurando sessões Baileys na VM nova"
ssh "$DST" "
  if [ -s /tmp/instances.tgz ]; then
    docker exec $DST_EVO_CONTAINER sh -c 'rm -rf /evolution/instances && mkdir -p /evolution/instances'
    cat /tmp/instances.tgz | docker exec -i $DST_EVO_CONTAINER sh -c 'cd /evolution && tar xzf -'
    echo '    sessões restauradas'
  else
    echo '    sem sessões para restaurar (seguindo só com o banco)'
  fi
  rm -f /tmp/evolution.sql /tmp/instances.tgz
"

echo "==> [6/6] Reiniciando Evolution para carregar as instâncias"
ssh "$DST" "docker restart $DST_EVO_CONTAINER >/dev/null"

echo
echo "=== Migração concluída ==="
echo "Confira as instâncias na VM nova:"
echo "  ssh $DST \"docker exec $DST_PG_CONTAINER psql -U evolution -d evolution -c 'SELECT name, \\\"connectionStatus\\\" FROM \\\"Instance\\\";'\""
