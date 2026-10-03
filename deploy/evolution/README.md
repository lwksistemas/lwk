# Evolution API — VM dedicada

Separa a Evolution API (WhatsApp Web) do servidor principal LWK para uma VM própria,
isolando o consumo de recursos e as falhas do WhatsApp do ERP.

## Infra

| Item | Valor |
|---|---|
| VM | Magalu `BV2-4-100` (2 vCPU / 4 GB / 100 GB) |
| SO | Ubuntu 24.04 LTS |
| IP público | `169.150.0.111` |
| IP privado (VPC) | `172.18.3.34` |
| Usuário SSH | `ubuntu` (chave "Evolution") |
| Domínio | `evolution.lwksistemas.com.br` |
| Servidor LWK (origem) | `201.23.81.50` público / `172.18.1.174` privado (mesma VPC) |

A VM nova e o wksistemas estão na **mesma VPC** (`vpc_default`, `br-se1-a`), então a
migração de dados usa o **IP privado** — nada trafega pela internet pública.

## Arquitetura após a separação

```
loja/app  ──HTTPS──>  api.lwksistemas.com.br      (backend LWK, wksistemas)
backend   ──HTTPS──>  evolution.lwksistemas.com.br (Evolution, VM nova)   [EVOLUTION_API_URL]
Evolution ──HTTPS──>  api.lwksistemas.com.br/.../webhook/  (eventos de volta)
```

A comunicação já é 100% por URL pública (HTTPS), então separar não quebra nenhuma
dependência de rede interna. O backend só precisa que `EVOLUTION_API_URL` continue
apontando para `https://evolution.lwksistemas.com.br` — o que já é o caso hoje.

## Arquivos

| Arquivo | O que é |
|---|---|
| `docker-compose.yml` | Evolution + Postgres + Redis próprios desta VM |
| `.env.example` | Variáveis (copiar para `.env`) |
| `nginx-evolution.conf` | Proxy + TLS para `evolution.lwksistemas.com.br` |
| `01-setup-vm.sh` | Instala Docker, nginx, certbot, firewall |
| `02-migrar-dados.sh` | Migra banco `evolution` + sessões Baileys do servidor antigo |

---

## Passo a passo

> Faça num horário de baixo movimento. Enquanto o DNS não virar, a Evolution antiga
> continua atendendo — a janela de indisponibilidade do WhatsApp é só a troca de DNS.

### 1. Enviar os arquivos para a VM nova
Da sua máquina (dentro do repo):
```bash
scp -r deploy/evolution/* ubuntu@169.150.0.111:/tmp/evolution/
```
(ou clone o repo na VM; o importante é ter os arquivos em `/opt/evolution/`)

### 2. Setup base da VM
```bash
ssh ubuntu@169.150.0.111
sudo mkdir -p /opt/evolution && sudo chown ubuntu:ubuntu /opt/evolution
cp /tmp/evolution/* /opt/evolution/ && cd /opt/evolution
bash 01-setup-vm.sh
# faça logout/login para o grupo docker valer
```

### 3. Configurar `.env`
```bash
cd /opt/evolution
cp .env.example .env
# EVOLUTION_API_KEY: a MESMA do /opt/lwk-erp/.env do servidor LWK (pegue com o comando abaixo)
#   ssh deploy@172.18.1.174 'grep EVOLUTION_API_KEY /opt/lwk-erp/.env'
# PG_PASS: gere uma nova:  openssl rand -base64 24
nano .env
```

### 4. Nginx + HTTPS
Primeiro aponte o DNS `evolution.lwksistemas.com.br` para `169.150.0.111` (A record).
Depois:
```bash
sudo cp /opt/evolution/nginx-evolution.conf /etc/nginx/sites-available/evolution
sudo ln -sf /etc/nginx/sites-available/evolution /etc/nginx/sites-enabled/evolution
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d evolution.lwksistemas.com.br
```

### 5. Subir os containers
```bash
cd /opt/evolution
docker compose up -d
docker compose ps          # postgres/redis healthy, evolution Up
```

### 6. Migrar os dados (as 3 sessões conectadas)
Para as lojas **não** precisarem reescanear o QR. Rode **na sua máquina local**
(a que já acessa os dois servidores por SSH) — assim não precisa configurar chave
SSH cruzada entre as VMs:
```bash
# da sua máquina, dentro do repo
bash deploy/evolution/02-migrar-dados.sh
```
O script faz: `pg_dump` do banco na origem → empacota as sessões Baileys →
`scp` para a VM nova → restaura banco e sessões → reinicia a Evolution.

Valide na VM nova:
```bash
ssh ubuntu@169.150.0.111 \
  "docker exec evolution-postgres psql -U evolution -d evolution -c 'SELECT name, \"connectionStatus\" FROM \"Instance\";'"
```

### 7. Virar o tráfego
O DNS já foi apontado no passo 4. Confirme que o domínio responde pela VM nova:
```bash
curl -s -H "apikey: <API_KEY>" https://evolution.lwksistemas.com.br/instance/fetchInstances | head
```

### 8. Reconfirmar webhooks (no servidor LWK)
```bash
ssh deploy@201.23.81.50 "docker exec lwk-erp-backend-1 python manage.py ensure_evolution_webhooks"
```

### 9. Desativar a Evolution no servidor antigo
Só depois de confirmar que a VM nova está 100%:
```bash
ssh deploy@201.23.81.50
cd /opt/lwk-erp
# remover o serviço 'evolution' do docker-compose.prod.yml (bloco já comentável)
docker compose -f docker-compose.prod.yml rm -sf evolution
# opcional, depois de dias estável: dropar o banco evolution local
# docker exec lwk-erp-postgres-1 psql -U lwk -c 'DROP DATABASE evolution;'
```

---

## Rollback

Se algo der errado na janela de troca:

1. **Reverter o DNS** `evolution.lwksistemas.com.br` de volta para `201.23.81.50`.
   A Evolution antiga ainda está no ar (só desligamos no passo 9), então o WhatsApp
   volta a funcionar assim que o DNS propagar.
2. Não desligue a Evolution antiga (passo 9) até ter 100% de confiança na nova —
   ela é a sua rede de segurança.
3. As sessões no servidor antigo permanecem intactas; migrar o banco é uma cópia
   (`pg_dump`), não um move — a origem não é alterada.

## Observações

- **Mesma `EVOLUTION_API_KEY`:** reusar a chave evita qualquer mudança no backend LWK.
- **Firewall:** 8080/5432/6379 ficam só no loopback; só 80/443/22 abertos.
- **Capacidade:** com 4 GB a VM comporta dezenas de instâncias; hoje são 3 (~260 MB).
- **Backup futuro:** agende `pg_dump` do banco `evolution` e snapshot do volume
  `evolution_instances` nesta VM (as sessões vivem aí).
