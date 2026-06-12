<?php

declare(strict_types=1);

/**
 * Tela admin — configuração WhatsApp (PHP puro).
 * Copie para public/admin/config_whatsapp.php
 *
 * Requer sessão/login do seu sistema; aqui usa empresa_id via GET para demo.
 */

[$config, $pdo] = require __DIR__ . '/bootstrap.php';

$empresaId = (int) ($_GET['empresa_id'] ?? 1);
$msg = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $stmt = $pdo->prepare(
        'INSERT INTO whatsapp_config (empresa_id, whatsapp_ativo, enviar_proposta_whatsapp,
         enviar_contrato_whatsapp, enviar_termo_consentimento_whatsapp, enviar_confirmacao, provider)
         VALUES (?,?,?,?,?,?,?)
         ON DUPLICATE KEY UPDATE
         whatsapp_ativo=VALUES(whatsapp_ativo),
         enviar_proposta_whatsapp=VALUES(enviar_proposta_whatsapp),
         enviar_contrato_whatsapp=VALUES(enviar_contrato_whatsapp),
         enviar_termo_consentimento_whatsapp=VALUES(enviar_termo_consentimento_whatsapp),
         enviar_confirmacao=VALUES(enviar_confirmacao),
         updated_at=NOW()'
    );
    $stmt->execute([
        $empresaId,
        isset($_POST['whatsapp_ativo']) ? 1 : 0,
        isset($_POST['enviar_proposta_whatsapp']) ? 1 : 0,
        isset($_POST['enviar_contrato_whatsapp']) ? 1 : 0,
        isset($_POST['enviar_termo_consentimento_whatsapp']) ? 1 : 0,
        isset($_POST['enviar_confirmacao']) ? 1 : 0,
        'evolution',
    ]);
    $msg = 'Configurações salvas.';
}

$stmt = $pdo->prepare('SELECT * FROM whatsapp_config WHERE empresa_id = ? LIMIT 1');
$stmt->execute([$empresaId]);
$cfg = $stmt->fetch() ?: [
    'whatsapp_ativo' => 0,
    'connection_status' => 'disconnected',
    'connected_phone' => '',
    'enviar_proposta_whatsapp' => 1,
    'enviar_contrato_whatsapp' => 1,
    'enviar_termo_consentimento_whatsapp' => 1,
    'enviar_confirmacao' => 1,
];

$status = (string) ($cfg['connection_status'] ?? 'disconnected');
$connected = $status === 'connected';
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>WhatsApp — Configuração</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; color: #111; }
    h1 { font-size: 1.4rem; color: #0d9488; }
    .card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 1rem 1.2rem; margin: 1rem 0; }
    label { display: block; margin: 0.5rem 0; }
    .btn { background: #0d9488; color: #fff; border: 0; padding: 0.6rem 1rem; border-radius: 8px; cursor: pointer; }
    .btn:disabled { opacity: 0.5; }
    .ok { color: #059669; }
    .warn { background: #fef3c7; padding: 0.6rem; border-radius: 6px; font-size: 0.9rem; }
    #qr { max-width: 280px; display: block; margin: 1rem auto; }
    .status { font-weight: 600; }
  </style>
</head>
<body>
  <h1>WhatsApp Web (Evolution)</h1>
  <p>Empresa #<?= htmlspecialchars((string) $empresaId, ENT_QUOTES, 'UTF-8') ?></p>

  <?php if ($msg): ?><p class="ok"><?= htmlspecialchars($msg, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

  <form method="post" class="card">
    <h2>Opções de envio</h2>
    <label><input type="checkbox" name="whatsapp_ativo" <?= !empty($cfg['whatsapp_ativo']) ? 'checked' : '' ?> /> WhatsApp ativo</label>
    <label><input type="checkbox" name="enviar_proposta_whatsapp" <?= !empty($cfg['enviar_proposta_whatsapp']) ? 'checked' : '' ?> /> Enviar proposta por WhatsApp</label>
    <label><input type="checkbox" name="enviar_contrato_whatsapp" <?= !empty($cfg['enviar_contrato_whatsapp']) ? 'checked' : '' ?> /> Enviar contrato por WhatsApp</label>
    <label><input type="checkbox" name="enviar_termo_consentimento_whatsapp" <?= !empty($cfg['enviar_termo_consentimento_whatsapp']) ? 'checked' : '' ?> /> Enviar termo de consentimento</label>
    <label><input type="checkbox" name="enviar_confirmacao" <?= !empty($cfg['enviar_confirmacao']) ? 'checked' : '' ?> /> Confirmação de agenda</label>
    <p><button type="submit" class="btn">Salvar</button></p>
  </form>

  <div class="card">
    <h2>Conexão</h2>
    <p class="status">Status: <?= htmlspecialchars($status, ENT_QUOTES, 'UTF-8') ?></p>
    <?php if ($connected && !empty($cfg['connected_phone'])): ?>
      <p>Conectado: <?= htmlspecialchars((string) $cfg['connected_phone'], ENT_QUOTES, 'UTF-8') ?></p>
    <?php else: ?>
      <div class="warn">WhatsApp Web não é oficial. Use por conta e risco.</div>
      <p><button type="button" class="btn" id="btnConnect">Conectar (QR Code)</button></p>
      <img id="qr" alt="QR Code" style="display:none" />
    <?php endif; ?>
  </div>

  <script>
    const empresaId = <?= (int) $empresaId ?>;
    const apiBase = '/api/whatsapp/connect.php';

    async function pollStatus() {
      const r = await fetch(`${apiBase}?empresa_id=${empresaId}&qr=1`);
      const j = await r.json();
      const img = document.getElementById('qr');
      if (j.qr_base64) {
        img.src = 'data:image/png;base64,' + j.qr_base64;
        img.style.display = 'block';
      }
      if (j.connection_status === 'connected') {
        location.reload();
        return;
      }
      setTimeout(pollStatus, 3000);
    }

    document.getElementById('btnConnect')?.addEventListener('click', async () => {
      const btn = document.getElementById('btnConnect');
      btn.disabled = true;
      const fd = new FormData();
      fd.append('empresa_id', empresaId);
      await fetch(apiBase + '?empresa_id=' + empresaId, { method: 'POST', body: fd });
      pollStatus();
    });
  </script>
</body>
</html>
