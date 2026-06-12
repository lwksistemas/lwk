<?php

declare(strict_types=1);

namespace LWK\WhatsAppEvolution;

/**
 * Manual HTML — WhatsApp Evolution API para sistemas PHP + MySQL (standalone).
 * Não depende de Django/LWK; adaptável a qualquer ERP/CRM em PHP.
 */
final class ManualPhpMysqlRenderer
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
            'app_name' => 'Meu Sistema',
            'app_url' => 'https://seusite.com.br',
            'evolution_api_url' => 'https://evolution-api-production-09bf.up.railway.app',
            'evolution_api_key' => '(AUTHENTICATION_API_KEY)',
            'webhook_url' => 'https://seusite.com.br/api/whatsapp/evolution/webhook.php',
            'instance_prefix' => 'empresa_',
            'empresa_id_exemplo' => 1,
            'evolution_docker_image' => 'evoapicloud/evolution-api:v2.3.7',
            'db_name' => 'meu_sistema',
            'generated_at' => date('d/m/Y H:i'),
        ];
    }

    public function renderHtml(): string
    {
        $c = $this->config;
        $e = fn (mixed $v): string => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
        $inst = $e($c['instance_prefix'] . $c['empresa_id_exemplo']);
        $app = $e($c['app_url']);
        $wh = $e($c['webhook_url']);
        $evo = $e($c['evolution_api_url']);

        ob_start();
        ?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Manual — WhatsApp Evolution API · PHP + MySQL</title>
  <?= $this->styles() ?>
</head>
<body>

<h1>WhatsApp Web (Evolution API)</h1>
<p class="subtitle">Integração em sistemas <strong>PHP + MySQL</strong> · <?= $e($c['app_name']) ?> · gerado em <?= $e($c['generated_at']) ?></p>

<div class="danger">
  <strong>⚠ Não oficial — risco de banimento</strong><br />
  WhatsApp Web via Baileys (Evolution API) viola os Termos de Uso da Meta. Use por conta e risco.
  Para produção comercial estável, prefira a Meta Cloud API.
</div>

<div class="cover-box">
  <p><strong>Para quem é este manual?</strong> Desenvolvedores que integram Evolution em ERP, CRM, clínica ou outro sistema com <strong>backend PHP</strong>, <strong>frontend PHP</strong> e <strong>MySQL</strong>.</p>
  <p><strong>Pacote de referência:</strong> pasta <code>whatsapp_evolution_php/</code> no repositório LWK (cliente HTTP, SQL, exemplos).</p>
  <p><strong>Instância por empresa:</strong> <code><?= $inst ?></code> (padrão: <code><?= $e($c['instance_prefix']) ?>{empresa_id}</code>)</p>
</div>

<h2>1. Arquitetura (PHP + MySQL + Evolution)</h2>
<div class="arch">Cliente (WhatsApp)
    ↕
Evolution API (Docker / Railway)  ←→  Postgres + Redis (Evolution)
    ↕ webhook MESSAGES_UPSERT
Seu backend PHP (Apache/Nginx)
    ↕ PDO
MySQL (config, logs, tokens, agendamentos)
    ↕
Frontend PHP (telas de config, QR, assinatura pública)</div>

<p>Cada <strong>empresa/loja</strong> do seu sistema tem:</p>
<ul>
  <li>1 registro em <code>whatsapp_config</code> (MySQL)</li>
  <li>1 instância Evolution: <code><?= $e($c['instance_prefix']) ?>ID</code></li>
  <li>1 webhook apontando para <code><?= $wh ?></code></li>
</ul>

<h2>2. Banco MySQL — tabelas sugeridas</h2>
<p>Script completo: <code>whatsapp_evolution_php/sql/schema.mysql.sql</code></p>
<table class="field-table">
  <thead><tr><th>Tabela</th><th>Função</th></tr></thead>
  <tbody>
    <tr><td><code>empresas</code></td><td>Sua tabela de clientes/lojas (já existente ou nova)</td></tr>
    <tr><td><code>whatsapp_config</code></td><td>Provedor, instância, status QR, flags de envio</td></tr>
    <tr><td><code>whatsapp_log</code></td><td>Auditoria de mensagens enviadas</td></tr>
    <tr><td><code>whatsapp_acao_token</code></td><td>Tokens públicos (confirmar agenda, assinar proposta/termo)</td></tr>
  </tbody>
</table>

<pre>mysql -u root -p <?= $e($c['db_name']) ?> &lt; whatsapp_evolution_php/sql/schema.mysql.sql</pre>

<h2>3. Estrutura de pastas (exemplo)</h2>
<div class="arch">seu-sistema/
├── config.php                 # DB + Evolution API key
├── public/
│   ├── admin/config_whatsapp.php
│   └── assinar/index.php      # página pública assinatura digital
├── api/whatsapp/
│   ├── webhook.php            # POST Evolution
│   ├── connect.php            # gera QR (JSON)
│   └── send.php               # envio interno
├── src/WhatsApp/
│   ├── EvolutionClient.php    # copiar ou composer
│   └── WhatsAppService.php
└── sql/schema.mysql.sql</div>

<h2>4. config.php</h2>
<pre><?= $e(<<<'PHP'
return [
    'app_url' => 'https://seusite.com.br',
    'db_host' => '127.0.0.1',
    'db_name' => 'meu_sistema',
    'db_user' => 'root',
    'db_pass' => 'senha',
    'evolution_api_url' => 'https://sua-evolution.up.railway.app',
    'evolution_api_key' => 'SUA_AUTHENTICATION_API_KEY',
    'webhook_url' => 'https://seusite.com.br/api/whatsapp/evolution/webhook.php',
    'instance_prefix' => 'empresa_',
];
PHP) ?></pre>

<h2>5. Cliente Evolution (PHP)</h2>
<p>Classe <code>LWK\WhatsAppEvolution\EvolutionClient</code> — métodos principais:</p>
<table class="field-table">
  <thead><tr><th>Método</th><th>Descrição</th></tr></thead>
  <tbody>
    <tr><td><code>setWebhook($instance)</code></td><td>Registra webhook MESSAGES_UPSERT</td></tr>
    <tr><td><code>connectionState($instance)</code></td><td>Status + QR base64 se pendente</td></tr>
    <tr><td><code>sendText($instance, $numero, $texto)</code></td><td>Envia mensagem</td></tr>
  </tbody>
</table>

<pre><?= $e(<<<'PHP'
require 'vendor/autoload.php';
$config = require 'config.php';
$client = new \LWK\WhatsAppEvolution\EvolutionClient($config);
$client->setWebhook('empresa_1');
$state = $client->connectionState('empresa_1');
PHP) ?></pre>

<h2>6. Serviço de envio (WhatsAppService)</h2>
<p>Exemplo em <code>examples/WhatsAppService.php</code>:</p>
<ul>
  <li>Valida <code>whatsapp_ativo</code> e <code>connection_status = connected</code> no MySQL</li>
  <li>Normaliza telefone BR (55 + DDD)</li>
  <li>Grava log em <code>whatsapp_log</code></li>
  <li><code>sendLinkAssinatura()</code> — mensagem com link para página pública de assinatura</li>
</ul>

<h2>7. Webhook (respostas do cliente)</h2>
<p>Arquivo: <code>examples/webhook_evolution.php</code> → copie para <code>public/api/whatsapp/evolution/webhook.php</code></p>
<p>Processa:</p>
<ul>
  <li>Botões: <code>ag_confirm_{id}</code> / <code>ag_cancel_{id}</code></li>
  <li>Texto: confirmar, sim, cancelar</li>
</ul>
<p>Adapte <code>processarConfirmacaoAgenda()</code> à sua tabela <code>agendamentos</code>.</p>

<div class="tip">
  <strong>GET no webhook</strong> deve retornar <code>{"status":"ok"}</code> — útil para teste no navegador.
</div>

<h2>8. Frontend PHP — tela de configuração + QR</h2>
<div class="step"><span class="step-num">1</span> Form POST salva flags em <code>whatsapp_config</code> (enviar proposta, termo, etc.)</div>
<div class="step"><span class="step-num">2</span> Botão "Conectar" chama <code>api/whatsapp/connect.php</code> (POST) → Evolution cria instância + QR</div>
<div class="step"><span class="step-num">3</span> JavaScript faz polling a cada 3s em <code>connect.php?status=1</code> até <code>connected</code></div>
<div class="step"><span class="step-num">4</span> Ao conectar, atualize MySQL: <code>connection_status='connected'</code>, <code>connected_phone</code></div>

<pre><?= $e(<<<'JS'
// Polling simplificado (frontend)
async function pollQr() {
  const r = await fetch('/api/whatsapp/connect.php?qr=1');
  const j = await r.json();
  if (j.qr_base64) document.getElementById('qr').src = 'data:image/png;base64,' + j.qr_base64;
  if (j.connection_status === 'connected') location.reload();
  else setTimeout(pollQr, 3000);
}
JS) ?></pre>

<h2>9. Casos de uso no seu sistema</h2>

<h3>9.1 CRM — proposta/contrato (PDF)</h3>
<pre><?= $e(<<<'PHP'
// Gera PDF, hospeda URL pública com token temporário, envia via Evolution sendDocument
$docUrl = $appUrl . '/api/documentos/download.php?token=' . $token;
// Evolution API: POST /message/sendMedia/{instance}
PHP) ?></pre>

<h3>9.2 CRM — assinatura digital por WhatsApp</h3>
<pre><?= $e(<<<'PHP'
$token = bin2hex(random_bytes(32));
// INSERT whatsapp_acao_token (tipo=assinatura_proposta, referencia_id=...)
$service->sendLinkAssinatura($empresaId, $leadTelefone, $leadNome, 'Proposta #123', $token, '/assinar/');
// Cliente abre: https://seusite.com.br/assinar/{token}
PHP) ?></pre>

<h3>9.3 Clínica — termo de consentimento</h3>
<pre><?= $e(<<<'PHP'
$service->sendLinkAssinatura($empresaId, $pacienteTel, $pacienteNome,
    'Termo — Botox', $token, '/assinar-consentimento/');
PHP) ?></pre>

<h3>9.4 Agenda — confirmar/cancelar (botões)</h3>
<p>Envie botões Evolution (<code>sendButtons</code>) ou link <code><?= $app ?>/confirmar/{token}</code>.</p>
<p>No webhook, atualize status do agendamento no MySQL quando receber clique ou texto.</p>

<h2>10. Servidor Evolution (Docker)</h2>
<table class="field-table">
  <thead><tr><th>Variável</th><th>Valor recomendado</th></tr></thead>
  <tbody>
    <tr><td>Imagem</td><td><code><?= $e($c['evolution_docker_image']) ?></code></td></tr>
    <tr><td>AUTHENTICATION_API_KEY</td><td>Igual ao <code>evolution_api_key</code> do PHP</td></tr>
    <tr><td>WPP_LID_MODE</td><td><code>false</code></td></tr>
    <tr><td>CONFIG_SESSION_PHONE_VERSION</td><td>Atualizar se QR falhar (ex.: 2.3000.1041203030)</td></tr>
  </tbody>
</table>

<h2>11. Checklist de implantação</h2>
<ol>
  <li>Criar tabelas MySQL (<code>schema.mysql.sql</code>)</li>
  <li>Configurar <code>config.php</code> (DB + Evolution URL + API key)</li>
  <li>Subir Evolution API (Docker/Railway)</li>
  <li>Implementar webhook PHP público (HTTPS)</li>
  <li>Tela admin: conectar QR por empresa</li>
  <li>Registrar webhook: <code>php registrar_webhook.php empresa_1</code></li>
  <li>Testar envio de texto e link de assinatura</li>
  <li>Testar botão confirmar → webhook → UPDATE MySQL</li>
</ol>

<h2>12. Diferença vs sistema LWK (Django)</h2>
<table class="field-table">
  <thead><tr><th>LWK (Django)</th><th>Seu sistema PHP</th></tr></thead>
  <tbody>
    <tr><td>Multi-tenant Postgres schemas</td><td>MySQL + <code>empresa_id</code> em cada tabela</td></tr>
    <tr><td><code>WhatsAppConfig</code> model</td><td>Tabela <code>whatsapp_config</code></td></tr>
    <tr><td>Django REST endpoints</td><td>Scripts PHP em <code>api/whatsapp/</code></td></tr>
    <tr><td>Next.js frontend</td><td>PHP templates ou SPA consumindo API PHP</td></tr>
    <tr><td><code>lwk_loja_{id}</code></td><td><code><?= $e($c['instance_prefix']) ?>ID</code> (configurável)</td></tr>
  </tbody>
</table>

<div class="footer">
  LWK Sistemas · Manual PHP + MySQL · Evolution API · <?= $e($c['generated_at']) ?><br />
  Evolution: <?= $evo ?> · Webhook: <?= $wh ?>
</div>

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
  body { font-family: 'Segoe UI', system-ui, sans-serif; color: #1f2937; line-height: 1.55; font-size: 10.5pt; max-width: 210mm; margin: 0 auto; padding: 10mm; }
  h1 { color: #0d9488; font-size: 21pt; margin: 0 0 4px; }
  h2 { color: #0f766e; font-size: 13pt; margin: 20px 0 8px; border-bottom: 2px solid #99f6e4; padding-bottom: 4px; page-break-after: avoid; }
  h3 { color: #374151; font-size: 11pt; margin: 12px 0 6px; }
  .subtitle { color: #6b7280; font-size: 10pt; margin-bottom: 16px; }
  .cover-box { background: linear-gradient(135deg, #ecfdf5, #d1fae5); border: 1px solid #6ee7b7; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; }
  .cover-box p { margin: 4px 0; }
  .danger { background: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 12px 16px; margin: 14px 0; font-size: 10pt; }
  .danger strong { color: #b91c1c; }
  .tip { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 14px; margin: 10px 0; font-size: 10pt; }
  ol, ul { margin: 6px 0 10px; padding-left: 22px; }
  li { margin-bottom: 4px; }
  code { font-family: Consolas, monospace; background: #f3f4f6; padding: 1px 5px; border-radius: 4px; font-size: 9.5pt; word-break: break-all; }
  pre { background: #134e4a; color: #ccfbf1; padding: 10px 12px; border-radius: 8px; font-size: 9pt; overflow-x: auto; white-space: pre-wrap; page-break-inside: avoid; }
  .field-table { width: 100%; border-collapse: collapse; margin: 10px 0 14px; font-size: 9.5pt; }
  .field-table th, .field-table td { border: 1px solid #d1d5db; padding: 7px 9px; text-align: left; vertical-align: top; }
  .field-table th { background: #ccfbf1; }
  .arch { background: #fafafa; border: 1px dashed #9ca3af; padding: 12px; font-family: monospace; font-size: 9pt; line-height: 1.6; margin: 10px 0; white-space: pre-wrap; }
  .step { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px 12px; margin: 8px 0; }
  .step-num { display: inline-block; background: #0d9488; color: #fff; width: 22px; height: 22px; border-radius: 50%; text-align: center; line-height: 22px; font-size: 10pt; font-weight: bold; margin-right: 8px; }
  .footer { margin-top: 24px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 9pt; color: #9ca3af; text-align: center; }
</style>
CSS;
    }
}
