<?php

declare(strict_types=1);

namespace App\WhatsApp;

use LWK\WhatsAppEvolution\EvolutionClient;
use PDO;

/** Serviço de envio WhatsApp por empresa (Evolution). */
final class WhatsAppService
{
    public function __construct(
        private PDO $pdo,
        private array $config,
    ) {
    }

    public function instanceName(int $empresaId): string
    {
        $stmt = $this->pdo->prepare(
            'SELECT evolution_instance_name FROM whatsapp_config WHERE empresa_id = ? LIMIT 1'
        );
        $stmt->execute([$empresaId]);
        $name = (string) ($stmt->fetchColumn() ?: '');
        return $name !== '' ? $name : (new EvolutionClient($this->config))->instanceName($empresaId);
    }

    /** @return array{ok: bool, error?: string} */
    public function sendText(int $empresaId, string $telefone, string $mensagem, ?int $userId = null): array
    {
        $cfg = $this->getConfig($empresaId);
        if (!$cfg || !(int) $cfg['whatsapp_ativo']) {
            return ['ok' => false, 'error' => 'WhatsApp não está ativo para esta empresa.'];
        }
        if (($cfg['connection_status'] ?? '') !== 'connected') {
            return ['ok' => false, 'error' => 'WhatsApp Web não conectado. Escaneie o QR Code.'];
        }

        $phone = preg_replace('/\D/', '', $telefone) ?? '';
        if (strlen($phone) < 10) {
            return ['ok' => false, 'error' => 'Telefone inválido.'];
        }
        if (!str_starts_with($phone, '55') && strlen($phone) <= 11) {
            $phone = '55' . ltrim($phone, '0');
        }

        try {
            $client = new EvolutionClient($this->config);
            $data = $client->sendText($this->instanceName($empresaId), $phone, $mensagem);
            $this->log($empresaId, $phone, $mensagem, 'enviado', $data);
            return ['ok' => true];
        } catch (\Throwable $e) {
            $this->log($empresaId, $phone, $mensagem, 'falhou', ['error' => $e->getMessage()]);
            return ['ok' => false, 'error' => $e->getMessage()];
        }
    }

    /** Envia link de assinatura digital (proposta, contrato, termo). */
    public function sendLinkAssinatura(
        int $empresaId,
        string $telefone,
        string $nomeDestinatario,
        string $tituloDocumento,
        string $token,
        string $pathAssinatura = '/assinar/',
    ): array {
        $base = rtrim((string) ($this->config['app_url'] ?? 'https://seusite.com.br'), '/');
        $link = $base . rtrim($pathAssinatura, '/') . '/' . rawurlencode($token);
        $msg = "Olá {$nomeDestinatario}!\n\n"
            . "Você recebeu *{$tituloDocumento}* para assinatura digital.\n\n"
            . "Leia e assine pelo link:\n{$link}\n\n"
            . "Link válido por 7 dias.";
        return $this->sendText($empresaId, $telefone, $msg);
    }

    private function getConfig(int $empresaId): ?array
    {
        $stmt = $this->pdo->prepare('SELECT * FROM whatsapp_config WHERE empresa_id = ? LIMIT 1');
        $stmt->execute([$empresaId]);
        $row = $stmt->fetch();
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
