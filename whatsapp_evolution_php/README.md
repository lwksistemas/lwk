# WhatsApp Web (Evolution API) — PHP + MySQL

Pacote para integrar **WhatsApp Web via Evolution API** em sistemas com **backend PHP**, **frontend PHP** e **banco MySQL** — independente do LWK/Django.

Inclui manual PDF/HTML, schema SQL, cliente HTTP, webhook, tela de configuração com QR e exemplos de envio (proposta, contrato, termo, assinatura digital).

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

```bash
mysql -u root -p meu_sistema < sql/schema.mysql.sql
```

## Manuais (geração local)

Os PDFs/HTML são gerados localmente em `output/` (não versionados):

| Manual | Comando |
|--------|---------|
| **PHP + MySQL (standalone)** | `php gerar_manual_mysql.php` |
| LWK Django (referência) | `php gerar_pdf.php` |

Ver HTML no navegador:

```bash
php -S localhost:8765 -t .
# http://localhost:8765/manual_mysql.php   ← PHP + MySQL
# http://localhost:8765/manual.php           ← LWK Django
```

## Estrutura

| Arquivo | Função |
|---------|--------|
| `sql/schema.mysql.sql` | Tabelas `whatsapp_config`, `whatsapp_log`, `whatsapp_acao_token` |
| `src/EvolutionClient.php` | Cliente Evolution (create, connect, QR, sendText, webhook) |
| `src/ManualPhpMysqlRenderer.php` | Manual HTML PHP + MySQL |
| `examples/WhatsAppService.php` | Envio texto + link assinatura |
| `examples/connect.php` | API JSON QR/conexão |
| `examples/config_whatsapp.php` | Tela admin PHP |
| `examples/webhook_evolution.php` | Webhook MESSAGES_UPSERT |
| `examples/bootstrap.php` | PDO MySQL |
| `gerar_manual_mysql.php` | Gera PDF + HTML do manual MySQL |

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
