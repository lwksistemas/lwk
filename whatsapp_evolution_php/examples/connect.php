<?php

declare(strict_types=1);

/**
 * API JSON — conectar WhatsApp Web (QR) por empresa.
 * Copie para public/api/whatsapp/connect.php
 */

header('Content-Type: application/json; charset=utf-8');

[$config, $pdo] = require __DIR__ . '/bootstrap.php';

use LWK\WhatsAppEvolution\EvolutionClient;

$empresaId = (int) ($_GET['empresa_id'] ?? $_POST['empresa_id'] ?? 0);
if ($empresaId <= 0) {
    http_response_code(400);
    echo json_encode(['error' => 'empresa_id obrigatório']);
    exit;
}

$client = new EvolutionClient($config);
$instance = $client->instanceName($empresaId);

$cfg = loadOrCreateConfig($pdo, $empresaId, $instance);

if (($_GET['status'] ?? '') === '1' || ($_GET['qr'] ?? '') === '1') {
    respondStatus($pdo, $client, $empresaId, $instance, $cfg);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Use POST para iniciar conexão']);
    exit;
}

try {
    $client->setWebhook($instance);
    try {
        $client->createInstance($instance);
    } catch (\Throwable) {
        // Instância já existe — segue para connect
    }

    $connect = $client->connectInstance($instance);
    $qr = EvolutionClient::extractQrBase64($connect);

    updateConfig($pdo, $empresaId, [
        'evolution_instance_name' => $instance,
        'connection_status' => $qr ? 'qr_pending' : 'disconnected',
        'whatsapp_ativo' => 1,
        'provider' => 'evolution',
    ]);

    echo json_encode([
        'ok' => true,
        'instance' => $instance,
        'connection_status' => $qr ? 'qr_pending' : 'disconnected',
        'qr_base64' => $qr,
    ]);
} catch (\Throwable $e) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => $e->getMessage()]);
}

function respondStatus(PDO $pdo, EvolutionClient $client, int $empresaId, string $instance, array $cfg): void
{
    try {
        $info = $client->getConnectionInfo($instance);
        if ($info['state'] === 'connected') {
            updateConfig($pdo, $empresaId, [
                'connection_status' => 'connected',
                'connected_phone' => substr($info['phone'], 0, 32),
                'connected_at' => date('Y-m-d H:i:s'),
            ]);
        } elseif ($info['qr_base64']) {
            updateConfig($pdo, $empresaId, ['connection_status' => 'qr_pending']);
        }

        echo json_encode([
            'ok' => true,
            'instance' => $instance,
            'connection_status' => $info['state'],
            'connected_phone' => $cfg['connected_phone'] ?? '',
            'qr_base64' => $info['qr_base64'],
        ]);
    } catch (\Throwable $e) {
        http_response_code(502);
        echo json_encode(['ok' => false, 'error' => $e->getMessage()]);
    }
}

function loadOrCreateConfig(PDO $pdo, int $empresaId, string $instance): array
{
    $stmt = $pdo->prepare('SELECT * FROM whatsapp_config WHERE empresa_id = ? LIMIT 1');
    $stmt->execute([$empresaId]);
    $row = $stmt->fetch();
    if ($row) {
        return $row;
    }

    $stmt = $pdo->prepare(
        'INSERT INTO whatsapp_config (empresa_id, evolution_instance_name, provider) VALUES (?,?,?)'
    );
    $stmt->execute([$empresaId, $instance, 'evolution']);

    $stmt = $pdo->prepare('SELECT * FROM whatsapp_config WHERE empresa_id = ? LIMIT 1');
    $stmt->execute([$empresaId]);

    return (array) $stmt->fetch();
}

/** @param array<string, mixed> $fields */
function updateConfig(PDO $pdo, int $empresaId, array $fields): void
{
    if ($fields === []) {
        return;
    }
    $sets = [];
    $values = [];
    foreach ($fields as $col => $val) {
        $sets[] = "{$col} = ?";
        $values[] = $val;
    }
    $values[] = $empresaId;
    $sql = 'UPDATE whatsapp_config SET ' . implode(', ', $sets) . ', updated_at = NOW() WHERE empresa_id = ?';
    $pdo->prepare($sql)->execute($values);
}
