<?php

declare(strict_types=1);

/**
 * Webhook Evolution — MESSAGES_UPSERT
 * Copie para public/api/whatsapp/evolution/webhook.php
 */

header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    echo json_encode(['status' => 'ok', 'service' => 'evolution-webhook-php']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

[$config, $pdo] = require __DIR__ . '/bootstrap.php';

$raw = file_get_contents('php://input') ?: '';
/** @var array<string, mixed> $payload */
$payload = json_decode($raw, true) ?? [];

// Evolution v2 envia event + data; normalize
$event = (string) ($payload['event'] ?? $payload['type'] ?? '');
$data = $payload['data'] ?? $payload;

if ($event !== '' && stripos($event, 'messages.upsert') === false && stripos($event, 'MESSAGES_UPSERT') === false) {
    echo json_encode(['status' => 'ignored', 'event' => $event]);
    exit;
}

// Extrair instância e mensagem (estrutura Baileys/Evolution varia)
$instance = (string) ($payload['instance'] ?? $data['instance'] ?? '');
$message = is_array($data['message'] ?? null) ? $data['message'] : ($data['messages'][0]['message'] ?? []);
$key = is_array($data['key'] ?? null) ? $data['key'] : ($data['messages'][0]['key'] ?? []);

$fromMe = (bool) ($key['fromMe'] ?? false);
if ($fromMe) {
    echo json_encode(['status' => 'ignored', 'reason' => 'fromMe']);
    exit;
}

$remoteJid = (string) ($key['remoteJid'] ?? '');
$text = extractMessageText($message);

// Botões: selectedButtonId ou texto
$buttonId = (string) (
    $message['buttonsResponseMessage']['selectedButtonId']
    ?? $message['templateButtonReplyMessage']['selectedId']
    ?? ''
);

if ($buttonId === '' && $text === '') {
    echo json_encode(['status' => 'ignored', 'reason' => 'no_text']);
    exit;
}

$empresaId = empresaIdFromInstance($pdo, $instance);
if ($empresaId <= 0) {
    http_response_code(404);
    echo json_encode(['error' => 'Empresa não encontrada para instância ' . $instance]);
    exit;
}

// Exemplo: confirmar/cancelar agenda — ids ag_confirm_{id} / ag_cancel_{id}
$acao = $buttonId !== '' ? $buttonId : strtolower(trim($text));
if (preg_match('/^ag_confirm_(\d+)$/', $acao, $m)) {
    processarConfirmacaoAgenda($pdo, $empresaId, (int) $m[1], 'confirmado');
} elseif (preg_match('/^ag_cancel_(\d+)$/', $acao, $m)) {
    processarConfirmacaoAgenda($pdo, $empresaId, (int) $m[1], 'cancelado');
} elseif (in_array($acao, ['confirmar', 'sim', 'ok'], true)) {
    // fallback texto — implemente lookup por telefone + agenda pendente
}

echo json_encode(['status' => 'ok']);

function extractMessageText(array $message): string
{
    return trim((string) (
        $message['conversation']
        ?? $message['extendedTextMessage']['text']
        ?? $message['buttonsResponseMessage']['selectedDisplayText']
        ?? ''
    ));
}

function empresaIdFromInstance(PDO $pdo, string $instance): int
{
    if ($instance === '') {
        return 0;
    }
    $stmt = $pdo->prepare(
        'SELECT empresa_id FROM whatsapp_config WHERE evolution_instance_name = ? LIMIT 1'
    );
    $stmt->execute([$instance]);
    $id = $stmt->fetchColumn();
    if ($id) {
        return (int) $id;
    }
    if (preg_match('/_(\d+)$/', $instance, $m)) {
        return (int) $m[1];
    }
    return 0;
}

function processarConfirmacaoAgenda(PDO $pdo, int $empresaId, int $agendaId, string $status): void
{
    // Adapte à sua tabela de agendamentos
    $stmt = $pdo->prepare(
        'UPDATE agendamentos SET status = ?, updated_at = NOW() WHERE id = ? AND empresa_id = ?'
    );
    $stmt->execute([$status, $agendaId, $empresaId]);
}
