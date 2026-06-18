<?php

declare(strict_types=1);

namespace App\WhatsApp;

use LWK\WhatsAppEvolution\MetaCloudClient;
use PDO;

/** Serviço de envio WhatsApp por empresa (Meta Cloud API). */
final class MetaWhatsAppService
{
    public function __construct(
        private PDO $pdo,
        private array $config,
    ) {
    }

    /** @return array{ok: bool, error?: string, message_id?: string} */
    public function sendText(int $empresaId, string $telefone, string $mensagem): array
    {
        $cfg = $this->getConfig($empresaId);
        if (!$cfg || !(int) $cfg['whatsapp_ativo']) {
            return ['ok' => false, 'error' => 'WhatsApp não está ativo para esta empresa.'];
        }

        $phoneId = trim((string) ($cfg['whatsapp_phone_id'] ?? ''));
        $token = trim((string) ($cfg['whatsapp_token'] ?? ''));
        if ($phoneId === '' || $token === '') {
            return ['ok' => false, 'error' => 'Informe Phone Number ID e token na configuração.'];
        }

        $client = new MetaCloudClient((string) ($this->config['meta_api_url'] ?? 'https://graph.facebook.com/v19.0'));
        $phone = MetaCloudClient::normalizePhone($telefone) ?? '';
        $result = $client->sendText($phoneId, $token, $phone, $mensagem);

        if ($result['ok']) {
            $this->log($empresaId, $phone, $mensagem, 'enviado', $result['data'] ?? []);
            $msgId = $result['data']['messages'][0]['id'] ?? null;
            return ['ok' => true, 'message_id' => is_string($msgId) ? $msgId : null];
        }

        $this->log($empresaId, $phone, $mensagem, 'falhou', $result['data'] ?? ['error' => $result['error'] ?? '']);
        return ['ok' => false, 'error' => $result['error'] ?? 'Erro ao enviar.'];
    }

    /** @return array{ok: bool, error?: string} */
    public function sendDocument(
        int $empresaId,
        string $telefone,
        string $documentUrl,
        string $filename,
        ?string $caption = null,
    ): array {
        $cfg = $this->getConfig($empresaId);
        if (!$cfg || !(int) $cfg['whatsapp_ativo']) {
            return ['ok' => false, 'error' => 'WhatsApp não está ativo.'];
        }

        $phoneId = trim((string) ($cfg['whatsapp_phone_id'] ?? ''));
        $token = trim((string) ($cfg['whatsapp_token'] ?? ''));
        $client = new MetaCloudClient((string) ($this->config['meta_api_url'] ?? 'https://graph.facebook.com/v19.0'));
        $phone = MetaCloudClient::normalizePhone($telefone) ?? '';
        $result = $client->sendDocument($phoneId, $token, $phone, $documentUrl, $filename, $caption);

        $label = '[documento] ' . $filename;
        if ($result['ok']) {
            $this->log($empresaId, $phone, $label, 'enviado', $result['data'] ?? []);
            return ['ok' => true];
        }
        $this->log($empresaId, $phone, $label, 'falhou', $result['data'] ?? []);
        return ['ok' => false, 'error' => $result['error'] ?? 'Erro ao enviar documento.'];
    }

    public function sendLinkAssinatura(
        int $empresaId,
        string $telefone,
        string $nomeDestinatario,
        string $tituloDocumento,
        string $linkCompleto,
    ): array {
        $msg = "Olá {$nomeDestinatario}!\n\n"
            . "Você recebeu *{$tituloDocumento}* para assinatura digital.\n\n"
            . "Leia e assine pelo link:\n{$linkCompleto}\n\n"
            . 'Link válido por 7 dias.';
        return $this->sendText($empresaId, $telefone, $msg);
    }

    private function getConfig(int $empresaId): ?array
    {
        $stmt = $this->pdo->prepare(
            'SELECT * FROM whatsapp_config WHERE empresa_id = ? AND provider = \'meta\' LIMIT 1'
        );
        $stmt->execute([$empresaId]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row ?: null;
    }

    /** @param array<string, mixed> $response */
    private function log(int $empresaId, string $telefone, string $mensagem, string $status, array $response): void
    {
        $stmt = $this->pdo->prepare(
            'INSERT INTO whatsapp_log (empresa_id, telefone, mensagem, status, response_json) VALUES (?,?,?,?,?)'
        );
        $stmt->execute([
            $empresaId,
            substr($telefone, 0, 20),
            mb_substr($mensagem, 0, 500),
            $status,
            json_encode($response, JSON_UNESCAPED_UNICODE),
        ]);
    }
}
