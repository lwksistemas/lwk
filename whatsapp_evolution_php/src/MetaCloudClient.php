<?php

declare(strict_types=1);

namespace LWK\WhatsAppEvolution;

/**
 * Cliente HTTP para WhatsApp Business — Meta Cloud API (Graph API).
 * Espelha backend/whatsapp/services.py (send_whatsapp, send_whatsapp_document).
 */
final class MetaCloudClient
{
    public function __construct(
        private string $apiUrl = 'https://graph.facebook.com/v19.0',
        private int $timeoutSeconds = 30,
    ) {
    }

    /**
     * @return array{ok: bool, data?: array<string, mixed>, error?: string}
     */
    public function sendText(string $phoneId, string $token, string $to, string $body): array
    {
        $phone = self::normalizePhone($to);
        if ($phone === null) {
            return ['ok' => false, 'error' => 'Telefone inválido ou incompleto.'];
        }

        return $this->postMessage($phoneId, $token, [
            'messaging_product' => 'whatsapp',
            'to' => $phone,
            'type' => 'text',
            'text' => ['body' => mb_substr($body, 0, 4096)],
        ]);
    }

    /**
     * @return array{ok: bool, data?: array<string, mixed>, error?: string}
     */
    public function sendDocument(
        string $phoneId,
        string $token,
        string $to,
        string $documentUrl,
        string $filename,
        ?string $caption = null,
    ): array {
        $phone = self::normalizePhone($to);
        if ($phone === null) {
            return ['ok' => false, 'error' => 'Telefone inválido ou incompleto.'];
        }

        $doc = [
            'link' => $documentUrl,
            'filename' => $filename,
        ];
        if ($caption !== null && $caption !== '') {
            $doc['caption'] = mb_substr($caption, 0, 1024);
        }

        return $this->postMessage($phoneId, $token, [
            'messaging_product' => 'whatsapp',
            'to' => $phone,
            'type' => 'document',
            'document' => $doc,
        ]);
    }

    /**
     * @param array<string, mixed> $payload
     * @return array{ok: bool, data?: array<string, mixed>, error?: string}
     */
    private function postMessage(string $phoneId, string $token, array $payload): array
    {
        $url = rtrim($this->apiUrl, '/') . '/' . rawurlencode($phoneId) . '/messages';
        $ch = curl_init($url);
        if ($ch === false) {
            return ['ok' => false, 'error' => 'Falha ao iniciar cURL.'];
        }

        $json = json_encode($payload, JSON_UNESCAPED_UNICODE);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $json,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $this->timeoutSeconds,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $token,
                'Content-Type: application/json',
            ],
        ]);

        $raw = curl_exec($ch);
        $httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlErr = curl_error($ch);
        curl_close($ch);

        if ($raw === false) {
            return ['ok' => false, 'error' => 'Erro de conexão: ' . $curlErr];
        }

        /** @var array<string, mixed> $data */
        $data = json_decode($raw, true) ?: [];
        $ok = $httpCode >= 200 && $httpCode < 300 && !empty($data['messages']);

        if ($ok) {
            return ['ok' => true, 'data' => $data];
        }

        $err = is_array($data['error'] ?? null) ? $data['error'] : [];
        $msg = trim((string) ($err['message'] ?? $err['error_user_msg'] ?? ''));
        if ($msg !== '' && stripos($msg, 'not in allowed list') !== false) {
            $msg = 'Número não está na lista de teste da Meta. Adicione em developers.facebook.com → WhatsApp → API Setup → To.';
        }
        if ($msg === '') {
            $code = $err['code'] ?? null;
            $msg = $code ? "Erro da API Meta (código {$code})" : 'Resposta inesperada da API Meta.';
        }

        return ['ok' => false, 'error' => $msg, 'data' => $data];
    }

  public static function normalizePhone(?string $telefone): ?string
    {
        if ($telefone === null || $telefone === '') {
            return null;
        }
        $digits = preg_replace('/\D/', '', $telefone) ?? '';
        if (strlen($digits) < 10) {
            return null;
        }
        if (strlen($digits) >= 12) {
            $out = substr($digits, 0, 15);
            if (str_starts_with($out, '55') && strlen($out) > 12 && $out[2] === '0') {
                $out = '55' . ltrim(substr($out, 2), '0');
            }
            return $out;
        }
        if (strlen($digits) === 11) {
            $ddd = (int) substr($digits, 0, 2);
            if ($ddd >= 11 && $ddd <= 99 && $digits[2] === '9') {
                return '55' . $digits;
            }
            if (str_starts_with($digits, '1')) {
                return $digits;
            }
            $br = ltrim($digits, '0');
            return strlen($br) < 10 ? null : '55' . $br;
        }
        if (strlen($digits) === 10) {
            $br = ltrim($digits, '0');
            return '55' . ($br !== '' ? $br : $digits);
        }
        return substr($digits, 0, 15);
    }
}
