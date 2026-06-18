<?php

declare(strict_types=1);

namespace LWK\WhatsAppEvolution;

/**
 * Manual HTML — Meta Cloud API (Phone ID + Token) · LWK Sistemas
 * Para administradores da loja (clínica, CRM, etc.).
 */
final class ManualMetaLwkRenderer
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
            'api_base_url' => 'https://api.lwksistemas.com.br',
            'frontend_url' => 'https://lwksistemas.com.br',
            'loja_slug' => 'vidanova',
            'loja_nome' => 'Vida Nova',
            'meta_api_url' => 'https://graph.facebook.com/v19.0',
            'generated_at' => date('d/m/Y H:i'),
        ];
    }

    public function renderHtml(): string
    {
        $c = $this->config;
        $e = fn (mixed $v): string => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
        $api = rtrim((string) $c['api_base_url'], '/');
        $front = rtrim((string) $c['frontend_url'], '/');
        $slug = $e($c['loja_slug']);
        $configUrl = "{$front}/loja/{$slug}/configuracoes/whatsapp";

        ob_start();
        ?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Manual — WhatsApp Meta Cloud API · LWK Sistemas</title>
  <?= $this->styles() ?>
</head>
<body>

<h1>WhatsApp — Meta Cloud API</h1>
<p class="subtitle">Manual do administrador · LWK Sistemas · <?= $e($c['generated_at']) ?></p>

<div class="cover-box">
  <p><strong>Integração oficial Meta</strong> — cada loja usa seu próprio <strong>Phone Number ID</strong> e <strong>token de acesso</strong>.</p>
  <p><strong>Loja exemplo:</strong> <?= $e($c['loja_nome']) ?> · slug <code><?= $slug ?></code></p>
  <p><strong>Tela de configuração:</strong><br /><code><?= $e($configUrl) ?></code></p>
</div>

<h2>1. O que é a Meta Cloud API?</h2>
<p>A <strong>WhatsApp Business Platform (Cloud API)</strong> é a forma oficial da Meta para enviar mensagens pelo WhatsApp em sistemas comerciais. No LWK, cada loja conecta <em>seu</em> número Business — não há número central compartilhado.</p>
<ul>
  <li><strong>Phone Number ID</strong> — identificador do número na Meta (não é o telefone em si).</li>
  <li><strong>Token de acesso</strong> — chave permanente com permissão de enviar mensagens.</li>
  <li><strong>Número WhatsApp</strong> — ex.: <code>5511999999999</code> (referência e exibição).</li>
</ul>

<div class="tip">
  <strong>Documentação oficial:</strong>
  developers.facebook.com/docs/whatsapp/cloud-api/get-started
</div>

<h2>2. Passo a passo na Meta (developers.facebook.com)</h2>
<div class="step"><span class="step-num">1</span> Crie um app em <strong>developers.facebook.com/apps</strong> e adicione o produto <strong>WhatsApp</strong>.</div>
<div class="step"><span class="step-num">2</span> Em <strong>WhatsApp → API Setup</strong>, copie o <strong>Phone number ID</strong>.</div>
<div class="step"><span class="step-num">3</span> Gere um <strong>token permanente</strong> (System User ou token de longa duração) com permissões de mensagens WhatsApp.</div>
<div class="step"><span class="step-num">4</span> <strong>Modo teste:</strong> cadastre o celular do destinatário em <strong>API Setup → To</strong> antes de enviar (até o app ser aprovado para produção).</div>
<div class="step"><span class="step-num">5</span> Para uso comercial em escala, crie e aprove <strong>templates de mensagem</strong> na Meta (mensagens iniciadas pela empresa fora da janela de 24h).</div>

<h2>3. Configuração no LWK Sistemas</h2>
<ol>
  <li>Acesse <code><?= $e($configUrl) ?></code> (menu Configurações → WhatsApp).</li>
  <li>Em <strong>Tipo de integração</strong>, selecione <strong>Meta Cloud API</strong> (Oficial — Phone ID + token).</li>
  <li>Preencha:
    <ul>
      <li><strong>Phone Number ID</strong> — colado da Meta.</li>
      <li><strong>Token de acesso</strong> — colado da Meta (não é exibido depois de salvo).</li>
      <li><strong>Número WhatsApp</strong> — opcional, para referência (ex.: 55 + DDD + celular).</li>
    </ul>
  </li>
  <li>Marque <strong>WhatsApp ativo</strong>.</li>
  <li>Configure as opções de envio automático (conforme o tipo de loja).</li>
  <li>Clique em <strong>Salvar</strong>.</li>
</ol>

<p>Status esperado após salvar: <strong>✅ Integração ativa</strong> — confirmações e lembretes podem ser enviados.</p>

<h2>4. Mensagens automáticas por tipo de loja</h2>
<table class="field-table">
  <thead><tr><th>Tipo de loja</th><th>Envios automáticos</th></tr></thead>
  <tbody>
    <tr>
      <td><strong>Clínica da Beleza / Estética</strong></td>
      <td>Confirmação de agendamento · Lembrete 24h · Lembrete 2h · Cobrança de débitos · Termo de consentimento (manual)</td>
    </tr>
    <tr>
      <td><strong>CRM Vendas</strong></td>
      <td>Lembrete de tarefas do calendário (1x/dia, 7h–9h) · Proposta/contrato por WhatsApp (se habilitado)</td>
    </tr>
    <tr>
      <td><strong>Outros apps</strong></td>
      <td>Configuração base; envios conforme módulos habilitados no plano</td>
    </tr>
  </tbody>
</table>

<h2>5. API interna do LWK (referência técnica)</h2>
<p>O painel web consome a API abaixo. Headers obrigatórios: <code>Authorization: Bearer &lt;JWT&gt;</code> e <code>X-Tenant-Slug: <?= $slug ?></code> (ou <code>X-Loja-ID</code>).</p>

<table class="field-table">
  <thead><tr><th>Método</th><th>Endpoint</th><th>Descrição</th></tr></thead>
  <tbody>
    <tr><td><code>GET</code></td><td><code><?= $e($api) ?>/api/whatsapp/config/</code></td><td>Lê configuração da loja</td></tr>
    <tr><td><code>PATCH</code></td><td><code><?= $e($api) ?>/api/whatsapp/config/</code></td><td>Salva Phone ID, token, flags</td></tr>
    <tr><td><code>GET</code></td><td><code><?= $e($api) ?>/api/superadmin/health/</code></td><td>Health (público) — verifica <code>evolution_available</code></td></tr>
  </tbody>
</table>

<h3>5.1 GET /api/whatsapp/config/ — resposta (exemplo)</h3>
<pre>{
  "whatsapp_ativo": true,
  "whatsapp_provider": "meta",
  "whatsapp_phone_id": "123456789012345",
  "whatsapp_token_set": true,
  "whatsapp_numero": "(11) 99999-9999",
  "enviar_confirmacao": true,
  "enviar_lembrete_24h": true,
  "enviar_lembrete_2h": true,
  "enviar_cobranca": true,
  "connection_status": "disconnected"
}</pre>

<h3>5.2 PATCH /api/whatsapp/config/ — corpo (exemplo)</h3>
<pre>{
  "whatsapp_provider": "meta",
  "whatsapp_phone_id": "123456789012345",
  "whatsapp_token": "EAAxxxxxxxx...",
  "whatsapp_numero": "5511999999999",
  "whatsapp_ativo": true,
  "enviar_confirmacao": true
}</pre>

<div class="warn">
  O token <strong>não é devolvido</strong> no GET — apenas <code>whatsapp_token_set: true</code>. Para trocar o token, envie <code>whatsapp_token</code> novamente no PATCH.
</div>

<h2>6. Como o LWK envia mensagens (Meta Graph API)</h2>
<p>Internamente o backend chama a Meta em:</p>
<pre>POST <?= $e($c['meta_api_url']) ?>/{PHONE_NUMBER_ID}/messages
Authorization: Bearer {TOKEN}
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "5511999999999",
  "type": "text",
  "text": { "body": "Sua mensagem aqui" }
}</pre>

<p>Documentos (PDF proposta, contrato, termo):</p>
<pre>{
  "messaging_product": "whatsapp",
  "to": "5511999999999",
  "type": "document",
  "document": {
    "link": "https://url-publica-https/documento.pdf",
    "filename": "proposta.pdf",
    "caption": "Segue sua proposta"
  }
}</pre>

<p>Telefone <code>to</code>: código do país + DDD + número, <strong>sem +</strong> (ex.: Brasil <code>5511987654321</code>).</p>

<h2>7. Plano e LGPD</h2>
<ul>
  <li>O plano da loja precisa incluir <strong>integração WhatsApp</strong> (<code>tem_whatsapp_integration</code>).</li>
  <li>Na clínica, pacientes podem ter opt-out (<code>allow_whatsapp</code>) — mensagens não são enviadas se desmarcado.</li>
  <li>Todos os envios ficam em <strong>WhatsAppLog</strong> (auditoria).</li>
</ul>

<h2>8. Problemas comuns</h2>
<table class="field-table">
  <thead><tr><th>Erro / sintoma</th><th>Solução</th></tr></thead>
  <tbody>
    <tr>
      <td><code>not in allowed list</code></td>
      <td>App em modo teste — adicione o número do destinatário em API Setup → To na Meta.</td>
    </tr>
    <tr>
      <td>Phone ID ou token inválido</td>
      <td>Verifique cópia sem espaços; gere novo token permanente na Meta.</td>
    </tr>
    <tr>
      <td>WhatsApp ativo mas não envia</td>
      <td>Confirme Phone ID + token salvos; status ✅ no painel; plano com WhatsApp habilitado.</td>
    </tr>
    <tr>
      <td>Template required</td>
      <td>Fora da janela de 24h a Meta exige template aprovado — crie em WhatsApp → Message templates.</td>
    </tr>
    <tr>
      <td>Plano não inclui WhatsApp</td>
      <td>Contate suporte LWK para habilitar no plano da loja.</td>
    </tr>
  </tbody>
</table>

<h2>9. Meta Cloud API vs WhatsApp Web (Evolution)</h2>
<table class="field-table">
  <thead><tr><th></th><th>Meta Cloud API (este manual)</th><th>WhatsApp Web (Evolution)</th></tr></thead>
  <tbody>
    <tr><td>Oficial</td><td>✅ Sim</td><td>❌ Não (risco de ban)</td></tr>
    <tr><td>Configuração</td><td>Phone ID + token</td><td>QR Code no celular</td></tr>
    <tr><td>Estabilidade</td><td>Alta (produção)</td><td>Média — sessão pode cair</td></tr>
    <tr><td>Confirmação por botão</td><td>Templates / link web</td><td>Botões nativos via webhook</td></tr>
  </tbody>
</table>

<h2>10. Checklist rápido</h2>
<ol>
  <li>App Meta criado com produto WhatsApp</li>
  <li>Phone Number ID copiado</li>
  <li>Token permanente gerado</li>
  <li>Números de teste cadastrados (se app em desenvolvimento)</li>
  <li>LWK: Meta Cloud API selecionado + campos preenchidos + WhatsApp ativo</li>
  <li>Teste: confirmar agendamento ou enviar mensagem de teste</li>
</ol>

<div class="footer">
  LWK Sistemas · Manual Meta Cloud API · <?= $e($c['generated_at']) ?><br />
  API <?= $e(parse_url($api, PHP_URL_HOST) ?: $api) ?> · Frontend <?= $e(parse_url($front, PHP_URL_HOST) ?: $front) ?>
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
  h1 { color: #1d4ed8; font-size: 21pt; margin: 0 0 4px; }
  h2 { color: #1e40af; font-size: 13pt; margin: 20px 0 8px; border-bottom: 2px solid #93c5fd; padding-bottom: 4px; page-break-after: avoid; }
  h3 { color: #374151; font-size: 11pt; margin: 12px 0 6px; }
  .subtitle { color: #6b7280; font-size: 10pt; margin-bottom: 16px; }
  .cover-box { background: linear-gradient(135deg, #eff6ff, #dbeafe); border: 1px solid #60a5fa; border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; }
  .cover-box p { margin: 4px 0; }
  .tip { background: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 14px; margin: 10px 0; font-size: 10pt; }
  .warn { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 10px 14px; margin: 10px 0; font-size: 10pt; }
  ol, ul { margin: 6px 0 10px; padding-left: 22px; }
  li { margin-bottom: 4px; }
  code { font-family: Consolas, monospace; background: #f3f4f6; padding: 1px 5px; border-radius: 4px; font-size: 9.5pt; word-break: break-all; }
  pre { background: #1e3a8a; color: #dbeafe; padding: 10px 12px; border-radius: 8px; font-size: 9pt; overflow-x: auto; white-space: pre-wrap; page-break-inside: avoid; }
  .field-table { width: 100%; border-collapse: collapse; margin: 10px 0 14px; font-size: 9.5pt; }
  .field-table th, .field-table td { border: 1px solid #d1d5db; padding: 7px 9px; text-align: left; vertical-align: top; }
  .field-table th { background: #dbeafe; }
  .step { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px 12px; margin: 8px 0; }
  .step-num { display: inline-block; background: #2563eb; color: #fff; width: 22px; height: 22px; border-radius: 50%; text-align: center; line-height: 22px; font-size: 10pt; font-weight: bold; margin-right: 8px; }
  .footer { margin-top: 24px; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 9pt; color: #9ca3af; text-align: center; }
</style>
CSS;
    }
}
