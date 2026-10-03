#!/usr/bin/env bash
# Setup inicial da VM dedicada da Evolution API (Magalu BV2-4-100, Ubuntu 24.04).
# Rodar como usuário com sudo (ubuntu). Idempotente — pode rodar de novo com segurança.
#
#   bash 01-setup-vm.sh
set -euo pipefail

echo "==> Atualizando pacotes"
sudo apt-get update -y

echo "==> Instalando Docker (engine + compose plugin)"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
fi
sudo usermod -aG docker "$USER" || true

echo "==> Instalando nginx e certbot"
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "==> Configurando firewall (UFW)"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# NÃO expor 8080/5432/6379 — ficam só no loopback via docker.
sudo ufw --force enable
sudo ufw status

echo "==> Preparando diretório da aplicação"
sudo mkdir -p /opt/evolution
sudo chown "$USER":"$USER" /opt/evolution
sudo mkdir -p /var/www/html

echo
echo "=== Setup base concluído ==="
echo "Próximos passos:"
echo "  1. Copie docker-compose.yml, .env.example e nginx-evolution.conf para /opt/evolution/"
echo "  2. cp /opt/evolution/.env.example /opt/evolution/.env  e preencha EVOLUTION_API_KEY e PG_PASS"
echo "  3. Instale o nginx:  sudo cp /opt/evolution/nginx-evolution.conf /etc/nginx/sites-available/evolution"
echo "     sudo ln -sf /etc/nginx/sites-available/evolution /etc/nginx/sites-enabled/evolution"
echo "     sudo nginx -t && sudo systemctl reload nginx"
echo "  4. Aponte o DNS evolution.lwksistemas.com.br -> IP público desta VM"
echo "  5. sudo certbot --nginx -d evolution.lwksistemas.com.br"
echo "  6. Migre os dados: bash 02-migrar-dados.sh (ver README)"
echo "  7. cd /opt/evolution && docker compose up -d"
echo
echo "ATENÇÃO: faça logout/login (ou 'newgrp docker') para o grupo docker valer sem sudo."
