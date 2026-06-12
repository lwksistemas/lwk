<?php

declare(strict_types=1);

namespace LWK\WhatsAppEvolution;

/**
 * Manual HTML — WhatsApp Web (Evolution API) · LWK Sistemas
 * Mesmo conteúdo do docs/manual-whatsapp-evolution-web.html, com valores do config.php.
 */
final class ManualRenderer
{
    /** @param array<string, mixed> $config */
    public function __construct(private array $config = [])
    {
        $this->config = array_merge(self::defaults(), $config);
    }

    /** @return array<string, mixed> */
    public static function defaults(): array
    {
        return [
            'evolution_api_url' => 'https://evolution-api-production-09bf.up.railway.app',
            'evolution_api_key' => '(AUTHENTICATION_API_KEY — não exibir em PDF público)',
            'webhook_url' => 'https://api.lwksistemas.com.br/api/whatsapp/evolution/webhook/',
            'api_base_url' => 'https://api.lwksistemas.com.br',
            'frontend_url' => 'https://lwksistemas.com.br',
            'loja_id' => 15,
            'loja_slug' => 'novaimagem',
            'instance_name' => 'lwk_loja_15',
            'evolution_docker_image' => 'evoapicloud/evolution-api:v2.3.7',
            'generated_at' => date('d/m/Y H:i'),
        ];
    }

    public function renderHtml(): string
    {
        $c = $this->config;
        $e = fn (mixed $v): string => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
        $confirmUrl = rtrim((string) $c['frontend_url'], '/') . '/confirmar-agendamento/{token}';
        $clinicaWhatsapp = rtrim((string) $c['frontend_url'], '/')
            . '/loja/' . $c['loja_slug'] . '/clinica-beleza/configuracoes/whatsapp';

        ob_start();
        ?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Manual — WhatsApp Web (QR) Evolution API · LWK Sistemas (PHP)</title>
  <?= $this->styles() ?>
</head>
<body>

  <h1>WhatsApp Web (QR Code)</h1>
  <p class="subtitle">Manual técnico — Evolution API · LWK Sistemas · gerado em <?= $e($c['generated_at']) ?> · PHP</p>

  <div class="danger">
    <strong>⚠ Não oficial — risco de banimento pela Meta</strong><br />
    Esta integração usa <strong>WhatsApp Web</strong> via biblioteca Baileys (Evolution API). Não é a API oficial da Meta.
    Viola os Termos de Uso do WhatsApp. A Meta pode <strong>banir o número</strong>, limitar envios ou desconectar a sessão sem aviso.
    Use por conta e risco da loja. Para uso comercial estável, prefira <strong>WhatsApp Business (Meta Cloud API)</strong>.
  </div>

  <div class="cover-box">
    <p><strong>Para quem é este manual?</strong> Equipe técnica e administradores do WhatsApp Web no LWK (Clínica da Beleza / CRM).</p>
    <p><strong>Instância exemplo:</strong> loja <?= $e($c['loja_id']) ?> → <code><?= $e($c['instance_name']) ?></code></p>
    <p><strong>Produção LWK:</strong> API <code><?= $e(parse_url((string) $c['api_base_url'], PHP_URL_HOST) ?: $c['api_base_url']) ?></code>
       · Frontend <code><?= $e(parse_url((string) $c['frontend_url'], PHP_URL_HOST) ?: $c['frontend_url']) ?></code>
       · Evolution <code><?= $e(parse_url((string) $c['evolution_api_url'], PHP_URL_HOST) ?: $c['evolution_api_url']) ?></code></p>
  </div>

  <h2>1. Visão geral da arquitetura</h2>
  <p>Cada loja tem instância isolada: <code>lwk_loja_{id}</code> (ex.: <code><?= $e($c['instance_name']) ?></code>).</p>
  <div class="arch">Paciente (WhatsApp)  ←→  evolution-api (Railway)  ←→  lwks-backend (Django)
         ↑                           ↑                           ↑
    QR / botões              Postgres-iP27 + Redis          Postgres principal
                                      │
                              Webhook MESSAGES_UPSERT
                              → <?= $e($c['webhook_url']) ?></div>

  <?= $this->tableServices() ?>

  <h2>2. Evolution API no Railway</h2>
  <div class="warn">
    <strong>Imagem obrigatória:</strong> <code><?= $e($c['evolution_docker_image']) ?></code> ou superior.
    A v2.2.3 retorna <code>{count:0}</code> sem QR.
  </div>
  <?= $this->sectionEvolutionEnv($e) ?>

  <h2>3. Backend LWK (Railway lwks-backend)</h2>
  <pre>EVOLUTION_API_URL=<?= $e($c['evolution_api_url']) ?>
EVOLUTION_API_KEY=&lt;mesma AUTHENTICATION_API_KEY&gt;</pre>
  <pre>npx @railway/cli up --service lwks-backend --detach</pre>
  <div class="warn"><strong>Deploy:</strong> nunca <code>railway up</code> com serviço <code>evolution-api</code> linkado.</div>

  <h2>4. Config PHP (este pacote)</h2>
  <p>Copie <code>config.example.php</code> → <code>config.php</code>:</p>
  <pre><?= $e($this->configPhpExample()) ?></pre>

  <h2>5. Banco de dados e migrations Django</h2>
  <pre>python manage.py ensure_whatsapp_evolution_fields --slug <?= $e($c['loja_slug']) ?>
python manage.py ensure_evolution_webhooks --slug <?= $e($c['loja_slug']) ?></pre>

  <h2>6. Configuração na clínica</h2>
  <ol>
    <li>Acesse <code><?= $e($clinicaWhatsapp) ?></code></li>
    <li>Provedor: <strong>WhatsApp Web (QR)</strong></li>
    <li>Gerar QR → escanear no celular → status <strong>Conectado</strong></li>
    <li>Ativar WhatsApp + opções de envio → Salvar</li>
  </ol>

  <h2>7. Confirmação de agendamento</h2>
  <ul>
    <li>Botões Confirmar / Cancelar</li>
    <li>Link <code><?= $e($confirmUrl) ?></code></li>
    <li>Texto: CONFIRMAR ou CANCELAR</li>
  </ul>
  <p>Webhook: <code><?= $e($c['webhook_url']) ?></code></p>
  <?= $this->sectionPhpWebhook($e) ?>

  <h2>8. Endpoints API LWK</h2>
  <?= $this->tableEndpoints($e) ?>

  <h2>9. Problemas e soluções</h2>
  <?= $this->tableTroubleshooting($e) ?>

  <h2>10. Meta vs Evolution</h2>
  <?= $this->tableCompare() ?>

  <h2>11. Comandos úteis</h2>
  <pre># Gerar PDF deste manual (PHP)
cd whatsapp_evolution_php
composer install
php gerar_pdf.php ../docs/manual-whatsapp-evolution-web-php.pdf

# Registrar webhook via PHP
php registrar_webhook.php

# Django
python manage.py ensure_evolution_webhooks --slug <?= $e($c['loja_slug']) ?>

curl <?= $e(rtrim((string) $c['api_base_url'], '/')) ?>/api/whatsapp/evolution/webhook/</pre>

  <h2>12. Boas práticas</h2>
  <ul>
    <li>Um número WhatsApp por loja</li>
    <li>Não usar para spam</li>
    <li>Logs em WhatsAppLog (LGPD)</li>
    <li>Não apagar volume Postgres da Evolution</li>
  </ul>

  <div class="ok"><strong>Fluxo testado:</strong> QR → mensagem agenda → confirmar/cancelar → status atualiza automaticamente.</div>

  <div class="footer">LWK Sistemas · <?= $e($c['frontend_url']) ?> · Manual PHP · <?= $e($c['generated_at']) ?></div>
</body>
</html>
        <?php
        return (string) ob_get_clean();
    }

    private function styles(): string
    {
        return <<<'CSS'
<style>
  @page { margin: 16mm 14mm; }
  * { box-sizing: border-box; }
  body { font-family: DejaVu Sans, 'Segoe UI', sans-serif; color: #1f2937; line-height: 1.55; font-size: 10.5pt; max-width: 210mm; margin: 0 auto; padding: 10mm; }
  h1 { color: #7c3aed; font-size: 21pt; margin: 0 0 4px; }
  h2 { color: #5b21b6; font-size: 13pt; margin: 20px 0 8px; border-bottom: 2px solid #ddd6fe; padding-bottom: 4px; }
  .subtitle { color: #6b7280; font-size: 10pt; margin-bottom: 16px; }
  .cover-box { background: #f5f3ff; border: 1px solid #c4b5fd; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; }
  .danger { background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 12px 16px; margin: 14px 0; font-size: 10pt; }
  .danger strong { color: #b91c1c; }
  code { font-family: DejaVu Sans Mono, monospace; background: #f3f4f6; padding: 1px 5px; border-radius: 4px; font-size: 9.5pt; word-break: break-all; }
  pre { background: #1e1b4b; color: #e9d5ff; padding: 10px 12px; border-radius: 8px; font-size: 9pt; white-space: pre-wrap; }
  .field-table { width: 100%; border-collapse: collapse; margin: 10px 0 14px; font-size: 9.5pt; }
  .field-table th, .field-table td { border: 1px solid #d1d5db; padding: 7px 9px; text-align: left; vertical-align: top; }
  .field-table th { background: #ede9fe; }
  .warn { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 10px 14px; margin: 10px 0; font-size: 10pt; }
  .ok { background: #ecfdf5; border-left: 4px solid #10b981; padding: 10px 14px; margin: 10px 0; font-size: 10pt; }
  .arch { background: #fafafa; border: 1px dashed #9ca3af; padding: 12px; font-family: monospace; font-size: 9pt; line-height: 1.6; margin: 10px 0; }
  .footer { margin-top: 24px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 9pt; color: #9ca3af; text-align: center; }
  ol, ul { margin: 6px 0 10px; padding-left: 22px; }
  li { margin-bottom: 4px; }
</style>
CSS;
    }

    private function configPhpExample(): string
    {
        $lines = [];
        foreach ($this->config as $k => $v) {
            if ($k === 'generated_at' || $k === 'evolution_api_key') {
                continue;
            }
            if (is_int($v)) {
                $lines[] = "    '{$k}' => {$v},";
            } else {
                $lines[] = "    '{$k}' => '" . addslashes((string) $v) . "',";
            }
        }
        return "return [\n" . implode("\n", $lines) . "\n];";
    }

    private function tableServices(): string
    {
        return <<<'HTML'
<table class="field-table"><thead><tr><th>Serviço Railway</th><th>Função</th></tr></thead><tbody>
<tr><td><strong>lwks-backend</strong></td><td>API Django — envio, webhook, agenda</td></tr>
<tr><td><strong>evolution-api</strong></td><td>WhatsApp Web — QR, Baileys, botões</td></tr>
<tr><td><strong>Postgres-iP27</strong></td><td>Banco Evolution</td></tr>
<tr><td><strong>Redis</strong></td><td>Cache Evolution</td></tr>
<tr><td><strong>Postgres</strong></td><td>Banco LWK principal</td></tr>
</tbody></table>
HTML;
    }

    /** @param callable(mixed): string $e */
    private function sectionEvolutionEnv(callable $e): string
    {
        $url = $e($this->config['evolution_api_url']);
        return <<<HTML
<pre>AUTHENTICATION_API_KEY=&lt;chave-forte&gt;
SERVER_URL={$url}
QRCODE_LIMIT=30
NODE_OPTIONS=--dns-result-order=ipv4first
CONFIG_SESSION_PHONE_CLIENT=Chrome
CONFIG_SESSION_PHONE_NAME=Chrome
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=\${{Postgres-iP27.DATABASE_URL}}
DATABASE_SAVE_DATA_INSTANCE=true
CACHE_REDIS_ENABLED=true
CACHE_REDIS_URI=\${{Redis-_W9Q.REDIS_URL}}
PORT=8080
WPP_LID_MODE=false
CONFIG_SESSION_PHONE_VERSION=2.3000.1041203030</pre>
HTML;
    }

    /** @param callable(mixed): string $e */
    private function sectionPhpWebhook(callable $e): string
    {
        $inst = $e($this->config['instance_name']);
        return <<<HTML
<div class="ok"><strong>PHP — registrar webhook na Evolution:</strong></div>
<pre>php registrar_webhook.php
// ou
\$client = new EvolutionClient(\$config);
\$client->setWebhook('{$inst}');</pre>
HTML;
    }

    /** @param callable(mixed): string $e */
    private function tableEndpoints(callable $e): string
    {
        $api = $e(rtrim((string) $this->config['api_base_url'], '/'));
        return <<<HTML
<table class="field-table"><thead><tr><th>Endpoint</th><th>Método</th><th>Função</th></tr></thead><tbody>
<tr><td><code>/api/clinica-beleza/whatsapp-config/</code></td><td>GET/PATCH</td><td>Config loja</td></tr>
<tr><td><code>.../whatsapp-config/connect/</code></td><td>POST</td><td>QR Code</td></tr>
<tr><td><code>{$api}/api/whatsapp/evolution/webhook/</code></td><td>POST</td><td>Webhook</td></tr>
<tr><td><code>/api/clinica-beleza/confirmar-agendamento/{token}/</code></td><td>GET/POST</td><td>Link paciente</td></tr>
</tbody></table>
HTML;
    }

    /** @param callable(mixed): string $e */
    private function tableTroubleshooting(callable $e): string
    {
        $wh = $e($this->config['webhook_url']);
        $img = $e($this->config['evolution_docker_image']);
        return <<<HTML
<table class="field-table"><thead><tr><th>Problema</th><th>Solução</th></tr></thead><tbody>
<tr><td>QR não aparece</td><td>Usar {$img}</td></tr>
<tr><td>Bad Request / @lid</td><td>WPP_LID_MODE=false + CONFIG_SESSION_PHONE_VERSION</td></tr>
<tr><td>Botão não atualiza agenda</td><td>Webhook em {$wh}</td></tr>
<tr><td>Sessão cai</td><td>Reescanear QR</td></tr>
</tbody></table>
HTML;
    }

    private function tableCompare(): string
    {
        return <<<'HTML'
<table class="field-table"><thead><tr><th></th><th>Meta</th><th>Evolution</th></tr></thead><tbody>
<tr><td>Oficial</td><td>Sim</td><td><strong>Não</strong></td></tr>
<tr><td>Risco ban</td><td>Baixo</td><td><strong>Alto</strong></td></tr>
<tr><td>Setup</td><td>Phone ID + token</td><td>QR Code</td></tr>
</tbody></table>
HTML;
    }
}
