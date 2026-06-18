<?php

declare(strict_types=1);

namespace LWK\WhatsAppEvolution;

/**
 * Manual HTML — Meta Cloud API para sistemas PHP + MySQL (standalone).
 * Códigos completos para integrar em outro ERP/CRM.
 */
final class ManualMetaPhpMysqlRenderer
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
            'meta_api_url' => 'https://graph.facebook.com/v19.0',
            'db_name' => 'meu_sistema',
            'empresa_id_exemplo' => 1,
            'generated_at' => date('d/m/Y H:i'),
        ];
    }

    public function renderHtml(): string
    {
        $c = $this->config;
        $e = fn (mixed $v): string => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
        $app = rtrim((string) $c['app_url'], '/');
        $meta = $e($c['meta_api_url']);

        ob_start();
        ?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Manual — Meta Cloud API · PHP + MySQL</title>
  <?= $this->styles() ?>
</head>
<body>

<h1>WhatsApp Meta Cloud API</h1>
<p class="subtitle">Integração completa em <strong>PHP + MySQL</strong> · <?= $e($c['app_name']) ?> · <?= $e($c['generated_at']) ?></p>

<div class="cover-box">
  <p><strong>Para desenvolvedores</strong> que implementam WhatsApp oficial (Phone ID + token) em sistema próprio com backend PHP, frontend PHP e banco MySQL.</p>
  <p><strong>Pacote de referência:</strong> <code>whatsapp_evolution_php/</code> — classes <code>MetaCloudClient</code>, SQL, exemplos em <code>examples/</code>.</p>
</div>

<h2>1. Arquitetura</h2>
<div class="arch">Paciente (WhatsApp)
    ↕ HTTPS
Meta Graph API (graph.facebook.com)
    ↕ POST /{phone_id}/messages
Seu backend PHP (Apache/Nginx)
    ↕ PDO
MySQL (whatsapp_config, whatsapp_log)
    ↕
Frontend PHP (tela admin: Phone ID + token)</div>

<h2>2. Banco MySQL</h2>
<p>Script: <code>whatsapp_evolution_php/sql/schema_meta.mysql.sql</code></p>
<pre><?= $e($this->schemaSql()) ?></pre>
<pre>mysql -u root -p <?= $e($c['db_name']) ?> &lt; whatsapp_evolution_php/sql/schema_meta.mysql.sql</pre>

<h2>3. config.php</h2>
<pre><?= $e(<<<'PHP'
return [
    'app_url' => 'https://seusite.com.br',
    'db_host' => '127.0.0.1',
    'db_name' => 'meu_sistema',
    'db_user' => 'root',
    'db_pass' => 'senha',
    'meta_api_url' => 'https://graph.facebook.com/v19.0',
];
PHP) ?></pre>

<h2>4. Cliente Meta — MetaCloudClient.php</h2>
<p>Arquivo: <code>src/MetaCloudClient.php</code></p>
<pre><?= $e($this->metaClientExample()) ?></pre>

<h2>5. Serviço de envio — MetaWhatsAppService.php</h2>
<p>Arquivo: <code>examples/MetaWhatsAppService.php</code></p>
<pre><?= $e($this->serviceExample()) ?></pre>

<h2>6. API REST do seu sistema (backend PHP)</h2>

<h3>6.1 GET /api/whatsapp/config.php?empresa_id=1</h3>
<pre><?= $e($this->apiGetConfig()) ?></pre>

<h3>6.2 POST /api/whatsapp/config.php — salvar Phone ID e token</h3>
<pre><?= $e($this->apiSaveConfig()) ?></pre>

<h3>6.3 POST /api/whatsapp/send.php — enviar texto</h3>
<pre><?= $e($this->apiSendText()) ?></pre>

<h2>7. Frontend PHP — tela de configuração</h2>
<p>Arquivo: <code>examples/config_whatsapp_meta.php</code></p>
<pre><?= $e($this->adminFormExample()) ?></pre>

<h2>8. Chamadas diretas à Meta (cURL)</h2>

<h3>8.1 Enviar texto</h3>
<pre>curl -X POST "<?= $meta ?>/SEU_PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "5511999999999",
    "type": "text",
    "text": { "body": "Olá! Mensagem de teste." }
  }'</pre>

<h3>8.2 Enviar PDF (URL pública HTTPS)</h3>
<pre>curl -X POST "<?= $meta ?>/SEU_PHONE_NUMBER_ID/messages" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "5511999999999",
    "type": "document",
    "document": {
      "link": "https://seusite.com.br/docs/proposta.pdf",
      "filename": "proposta.pdf",
      "caption": "Segue sua proposta"
    }
  }'</pre>

<h3>8.3 Resposta de sucesso</h3>
<pre>{
  "messaging_product": "whatsapp",
  "contacts": [{ "input": "5511999999999", "wa_id": "5511999999999" }],
  "messages": [{ "id": "wamid.HBgN..." }]
}</pre>

<h2>9. Normalização de telefone (Brasil)</h2>
<pre><?= $e(<<<'PHP'
// Meta exige: código país + DDD + número, sem +
// (11) 99999-9999 → 5511999999999
$phone = MetaCloudClient::normalizePhone($telefone);
PHP) ?></pre>

<h2>10. Casos de uso</h2>

<h3>10.1 Confirmação de agendamento</h3>
<pre><?= $e(<<<'PHP'
$msg = "Olá {$nome}!\nConsulta confirmada: {$data} às {$hora}.\n{$link}";
$service->sendText($empresaId, $pacienteTel, $msg);
PHP) ?></pre>

<h3>10.2 Proposta / contrato (PDF)</h3>
<pre><?= $e(<<<'PHP'
$url = $appUrl . '/api/documentos/download.php?token=' . urlencode($token);
$client->sendDocument($phoneId, $token, $tel, $url, 'proposta.pdf', 'Segue proposta');
PHP) ?></pre>

<h3>10.3 Assinatura digital (link)</h3>
<pre><?= $e(<<<'PHP'
$link = $appUrl . '/assinar/' . $token;
$service->sendLinkAssinatura($empresaId, $tel, $nome, 'Proposta #123', $link);
PHP) ?></pre>

<h2>11. Webhook Meta (receber respostas) — opcional</h2>
<p>Para botões e respostas do cliente, configure em Meta → WhatsApp → Configuration → Webhook:</p>
<pre>GET  <?= $e($app) ?>/api/whatsapp/meta_webhook.php  (verificação hub.challenge)
POST <?= $e($app) ?>/api/whatsapp/meta_webhook.php  (eventos messages)</pre>
<p>Valide <code>X-Hub-Signature-256</code> com o App Secret. O LWK usa Evolution para botões; com Meta Cloud API use templates interativos ou links web.</p>

<h2>12. Tabela de endpoints (resumo)</h2>
<table class="field-table">
  <thead><tr><th>Quem</th><th>Método</th><th>URL</th></tr></thead>
  <tbody>
    <tr><td>Seu PHP</td><td>GET/PATCH</td><td><code>/api/whatsapp/config.php</code></td></tr>
    <tr><td>Seu PHP</td><td>POST</td><td><code>/api/whatsapp/send.php</code></td></tr>
    <tr><td>Meta</td><td>POST</td><td><code><?= $meta ?>/{phone_id}/messages</code></td></tr>
    <tr><td>Meta</td><td>GET/POST</td><td><code>Seu webhook (opcional)</code></td></tr>
  </tbody>
</table>

<h2>13. Checklist de implantação</h2>
<ol>
  <li>Criar tabelas MySQL (<code>schema_meta.mysql.sql</code>)</li>
  <li>App Meta + Phone Number ID + token permanente</li>
  <li>Copiar <code>MetaCloudClient.php</code> e <code>MetaWhatsAppService.php</code></li>
  <li>Implementar <code>config.php</code> e tela admin</li>
  <li>Testar envio com número em API Setup → To (modo teste)</li>
  <li>Gravar logs em <code>whatsapp_log</code></li>
  <li>Produção: aprovar templates na Meta para mensagens proativas</li>
</ol>

<h2>14. Gerar este PDF</h2>
<pre>cd whatsapp_evolution_php
composer install
php gerar_manual_meta_mysql.php</pre>

<div class="footer">
  LWK Sistemas · Meta Cloud API · PHP + MySQL · <?= $e($c['generated_at']) ?>
</div>

</body>
</html>
        <?php
        return (string) ob_get_clean();
    }

    private function schemaSql(): string
    {
        return <<<'SQL'
CREATE TABLE IF NOT EXISTS empresas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(200) NOT NULL,
  slug VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS whatsapp_config (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT UNSIGNED NOT NULL,
  provider ENUM('meta','evolution') NOT NULL DEFAULT 'meta',
  whatsapp_numero VARCHAR(20) NOT NULL DEFAULT '',
  whatsapp_phone_id VARCHAR(64) NOT NULL DEFAULT '',
  whatsapp_token VARCHAR(512) NOT NULL DEFAULT '',
  whatsapp_ativo TINYINT(1) NOT NULL DEFAULT 0,
  enviar_confirmacao TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_empresa (empresa_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS whatsapp_log (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT UNSIGNED NOT NULL,
  telefone VARCHAR(20) NOT NULL,
  mensagem TEXT NOT NULL,
  status ENUM('enviado','falhou') NOT NULL,
  response_json JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SQL;
    }

    private function metaClientExample(): string
    {
        return <<<'PHP'
use LWK\WhatsAppEvolution\MetaCloudClient;

$config = require 'config.php';
$client = new MetaCloudClient($config['meta_api_url']);

$result = $client->sendText(
    phoneId: '123456789012345',
    token: 'EAAxxxxxxxx',
    to: '11999999999',
    body: 'Olá! Teste Meta Cloud API.'
);

if ($result['ok']) {
    echo 'Enviado: ' . $result['data']['messages'][0]['id'];
} else {
    echo 'Erro: ' . $result['error'];
}
PHP;
    }

    private function serviceExample(): string
    {
        return <<<'PHP'
use App\WhatsApp\MetaWhatsAppService;

$service = new MetaWhatsAppService($pdo, $config);
$r = $service->sendText($empresaId, '11999999999', 'Confirmação de consulta...');
if (!$r['ok']) { die($r['error']); }
PHP;
    }

    private function apiGetConfig(): string
    {
        return <<<'PHP'
<?php
require 'bootstrap.php';
$empresaId = (int) ($_GET['empresa_id'] ?? 0);
$stmt = $pdo->prepare('SELECT whatsapp_ativo, whatsapp_phone_id,
  whatsapp_numero, provider FROM whatsapp_config WHERE empresa_id=?');
$stmt->execute([$empresaId]);
$row = $stmt->fetch(PDO::FETCH_ASSOC) ?: [];
$row['whatsapp_token_set'] = !empty($row['whatsapp_token'] ?? '');
unset($row['whatsapp_token']); // nunca expor token
header('Content-Type: application/json');
echo json_encode($row);
PHP;
    }

    private function apiSaveConfig(): string
    {
        return <<<'PHP'
<?php
require 'bootstrap.php';
$data = json_decode(file_get_contents('php://input'), true) ?: [];
$empresaId = (int) ($data['empresa_id'] ?? 0);
$stmt = $pdo->prepare('UPDATE whatsapp_config SET
  whatsapp_phone_id=?, whatsapp_token=COALESCE(?, whatsapp_token),
  whatsapp_numero=?, whatsapp_ativo=?, provider=\'meta\'
  WHERE empresa_id=?');
$token = trim($data['whatsapp_token'] ?? '') ?: null;
$stmt->execute([
  trim($data['whatsapp_phone_id'] ?? ''),
  $token,
  preg_replace('/\D/', '', $data['whatsapp_numero'] ?? ''),
  !empty($data['whatsapp_ativo']) ? 1 : 0,
  $empresaId,
]);
echo json_encode(['success' => true]);
PHP;
    }

    private function apiSendText(): string
    {
        return <<<'PHP'
<?php
require 'bootstrap.php';
$data = json_decode(file_get_contents('php://input'), true) ?: [];
$service = new \App\WhatsApp\MetaWhatsAppService($pdo, $config);
$result = $service->sendText(
  (int) $data['empresa_id'],
  (string) $data['telefone'],
  (string) $data['mensagem']
);
header('Content-Type: application/json');
echo json_encode($result);
PHP;
    }

    private function adminFormExample(): string
    {
        return <<<'PHP'
<form method="post">
  <label>Phone Number ID (Meta)</label>
  <input name="whatsapp_phone_id" value="<?= htmlspecialchars($cfg['whatsapp_phone_id']) ?>">
  <label>Token de acesso</label>
  <input type="password" name="whatsapp_token" placeholder="Deixe vazio para manter">
  <label>Número WhatsApp</label>
  <input name="whatsapp_numero" value="<?= htmlspecialchars($cfg['whatsapp_numero']) ?>">
  <label><input type="checkbox" name="whatsapp_ativo" <?= $cfg['whatsapp_ativo']?'checked':'' ?>> WhatsApp ativo</label>
  <button type="submit">Salvar</button>
</form>
PHP;
    }

    private function styles(): string
    {
        return <<<'CSS'
<style>
  @page { margin: 14mm 12mm; }
  * { box-sizing: border-box; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; color: #1f2937; line-height: 1.5; font-size: 10pt; max-width: 210mm; margin: 0 auto; padding: 8mm; }
  h1 { color: #1d4ed8; font-size: 20pt; margin: 0 0 4px; }
  h2 { color: #1e40af; font-size: 12pt; margin: 18px 0 6px; border-bottom: 2px solid #93c5fd; padding-bottom: 3px; page-break-after: avoid; }
  h3 { color: #374151; font-size: 10.5pt; margin: 10px 0 4px; }
  .subtitle { color: #6b7280; font-size: 9.5pt; margin-bottom: 14px; }
  .cover-box { background: #eff6ff; border: 1px solid #60a5fa; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; }
  ol, ul { margin: 4px 0 8px; padding-left: 20px; }
  code { font-family: Consolas, monospace; background: #f3f4f6; padding: 1px 4px; border-radius: 3px; font-size: 9pt; word-break: break-all; }
  pre { background: #1e3a8a; color: #dbeafe; padding: 8px 10px; border-radius: 6px; font-size: 8.5pt; white-space: pre-wrap; page-break-inside: avoid; }
  .field-table { width: 100%; border-collapse: collapse; margin: 8px 0 12px; font-size: 9pt; }
  .field-table th, .field-table td { border: 1px solid #d1d5db; padding: 6px 8px; vertical-align: top; }
  .field-table th { background: #dbeafe; }
  .arch { background: #fafafa; border: 1px dashed #9ca3af; padding: 10px; font-family: monospace; font-size: 8.5pt; white-space: pre-wrap; margin: 8px 0; }
  .footer { margin-top: 20px; padding-top: 10px; border-top: 1px solid #e5e7eb; font-size: 8.5pt; color: #9ca3af; text-align: center; }
</style>
CSS;
    }
}
