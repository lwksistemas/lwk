# WhatsApp — PHP + MySQL (Evolution API e Meta Cloud API)

Pacote standalone para integrar **WhatsApp** em sistemas **PHP + MySQL** — independente do LWK/Django.

- **Evolution API** — WhatsApp Web (QR code)
- **Meta Cloud API** — Graph API (Phone Number ID + token)

Inclui manuais PDF/HTML, schemas SQL, clientes HTTP, webhook, tela de configuração e exemplos de envio.

## Requisitos

- PHP 8.1+
- MySQL 5.7+ / MariaDB 10.3+
- extensão `curl` e `pdo_mysql`
- Composer

## Instalação

```bash
cd whatsapp_evolution_php
composer install
cp config.example.php config.php
# Edite: db_*, evolution_api_url, evolution_api_key, app_url, webhook_url
```

### Banco MySQL

**Evolution (WhatsApp Web):**

```bash
mysql -u root -p meu_sistema < sql/schema.mysql.sql
```

**Meta Cloud API:**

```bash
mysql -u root -p meu_sistema < sql/schema_meta.mysql.sql
```

## Manuais (geração local)

Os PDFs/HTML são gerados localmente em `output/` (não versionados):

| Manual | Comando |
|--------|---------|
| **Meta Cloud API — LWK Sistemas (admin)** | `php gerar_manual_meta_lwk.php` |
| **Meta Cloud API — PHP + MySQL (códigos)** | `php gerar_manual_meta_mysql.php` |
| WhatsApp Web Evolution — PHP + MySQL | `php gerar_manual_mysql.php` |
| WhatsApp Web Evolution — LWK Django | `php gerar_pdf.php` |

Ver HTML no navegador:

```bash
php -S localhost:8765 -t .
# output/manual-whatsapp-meta-cloud-lwk.html
# output/manual-whatsapp-meta-cloud-php-mysql.html
```

## Estrutura

| Arquivo | Função |
|---------|--------|
| `sql/schema.mysql.sql` | Tabelas Evolution (`whatsapp_config`, `whatsapp_log`, …) |
| `sql/schema_meta.mysql.sql` | Schema Meta Cloud API (`empresas`, `whatsapp_config` com phone_id/token) |
| `src/EvolutionClient.php` | Cliente Evolution (create, connect, QR, sendText, webhook) |
| `src/MetaCloudClient.php` | Cliente Meta Graph API (sendText, sendDocument) |
| `src/ManualMetaLwkRenderer.php` | Manual HTML Meta — painel LWK (admin) |
| `src/ManualMetaPhpMysqlRenderer.php` | Manual HTML Meta — PHP + MySQL (códigos) |
| `src/ManualPhpMysqlRenderer.php` | Manual HTML Evolution — PHP + MySQL |
| `examples/WhatsAppService.php` | Envio Evolution + link assinatura |
| `examples/MetaWhatsAppService.php` | Envio Meta Cloud API |
| `examples/connect.php` | API JSON QR/conexão (Evolution) |
| `examples/config_whatsapp.php` | Tela admin PHP |
| `examples/webhook_evolution.php` | Webhook MESSAGES_UPSERT |
| `examples/bootstrap.php` | PDO MySQL |
| `gerar_manual_meta_lwk.php` | PDF + HTML manual Meta LWK |
| `gerar_manual_meta_mysql.php` | PDF + HTML manual Meta PHP+MySQL |
| `gerar_manual_mysql.php` | PDF + HTML manual Evolution MySQL |

## Uso rápido

1. Copie `examples/` para seu projeto (`api/whatsapp/`, `admin/`).
2. Configure `config.php` com credenciais MySQL e Evolution.
3. Exponha `webhook.php` em HTTPS.
4. Registre webhook: `php registrar_webhook.php empresa_1`
5. Abra `config_whatsapp.php?empresa_id=1` e escaneie o QR.

## Enviar assinatura digital

```php
use App\WhatsApp\WhatsAppService;

$service = new WhatsAppService($pdo, $config);
$token = bin2hex(random_bytes(32));
// INSERT em whatsapp_acao_token ...
$service->sendLinkAssinatura($empresaId, $telefone, $nome, 'Proposta #123', $token, '/assinar/');
```

## Relação com LWK

O sistema principal LWK usa Django + PostgreSQL (`backend/whatsapp/`). Este pacote é **standalone** para quem usa PHP + MySQL em outro projeto, reutilizando a mesma Evolution API.
