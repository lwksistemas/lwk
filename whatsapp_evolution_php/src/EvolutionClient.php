<?php

declare(strict_types=1);

namespace LWK\WhatsAppEvolution;

/**
 * Cliente HTTP mínimo Evolution API v2 (WhatsApp Web).
 * Espelha backend/whatsapp/evolution_client.py
 */
final class EvolutionClient
{
    /** @param array{evolution_api_url?: string, evolution_api_key?: string, webhook_url?: string} $config */
    public function __construct(private array $config)
    {
    }

    public function baseUrl(): string
    {
        return rtrim((string) ($this->config['evolution_api_url'] ?? ''), '/');
    }

    public function webhookUrl(): string
    {
        $url = (string) ($this->config['webhook_url'] ?? '');
        if ($url !== '') {
            return str_ends_with($url, '/') ? $url : $url . '/';
        }
        $api = rtrim((string) ($this->config['api_base_url'] ?? 'https://api.lwksistemas.com.br'), '/');
        return $api . '/api/whatsapp/evolution/webhook/';
    }

    public function instanceName(int $empresaId): string
    {
        $prefix = (string) ($this->config['instance_prefix'] ?? 'empresa_');

        return $prefix . $empresaId;
    }

    /** @deprecated Use instanceName() na instância com config */
    public static function defaultInstanceName(int $empresaId): string
    {
        return 'empresa_' . $empresaId;
    }

    /** @return array<string, mixed> */
    public function createInstance(string $instanceName): array
    {
        return $this->request('POST', '/instance/create', [
            'instanceName' => $instanceName,
            'integration' => 'WHATSAPP-BAILEYS',
            'qrcode' => true,
        ]);
    }

    /** @return array<string, mixed> */
    public function connectInstance(string $instanceName): array
    {
        return $this->request('GET', "/instance/connect/{$instanceName}");
    }

    /** @return array<string, mixed> */
    public function deleteInstance(string $instanceName): array
    {
        return $this->request('DELETE', "/instance/delete/{$instanceName}");
    }

    /** Extrai QR base64 da resposta Evolution (connect/create). */
    public static function extractQrBase64(array $data): ?string
    {
        $candidates = [
            $data['base64'] ?? null,
            $data['qrcode']['base64'] ?? null,
            $data['code'] ?? null,
            is_array($data['qrcode'] ?? null) ? ($data['qrcode']['base64'] ?? null) : null,
        ];
        foreach ($candidates as $value) {
            if (is_string($value) && $value !== '') {
                return str_starts_with($value, 'data:image')
                    ? (string) preg_replace('/^data:image\/[^;]+;base64,/', '', $value)
                    : $value;
            }
        }

        return null;
    }

    /** @return array{state: string, phone: string, qr_base64: ?string, raw: array<string, mixed>} */
    public function getConnectionInfo(string $instanceName): array
    {
        $data = $this->connectionState($instanceName);
        $instance = is_array($data['instance'] ?? null) ? $data['instance'] : $data;
        $stateRaw = (string) ($instance['state'] ?? $instance['status'] ?? $data['state'] ?? 'disconnected');
        $state = match (strtolower($stateRaw)) {
            'open', 'connected' => 'connected',
            'connecting', 'qr' => 'qr_pending',
            default => 'disconnected',
        };
        $phone = (string) ($instance['owner'] ?? $instance['wuid'] ?? '');

        return [
            'state' => $state,
            'phone' => $phone,
            'qr_base64' => self::extractQrBase64($data),
            'raw' => $data,
        ];
    }

    /** @return array<string, mixed> */
    public function setWebhook(string $instanceName): array
    {
        return $this->request('POST', "/webhook/set/{$instanceName}", [
            'webhook' => [
                'enabled' => true,
                'url' => $this->webhookUrl(),
                'webhookByEvents' => false,
                'webhookBase64' => false,
                'events' => ['MESSAGES_UPSERT'],
            ],
        ]);
    }

    /** @return array<string, mixed> */
    public function connectionState(string $instanceName): array
    {
        return $this->request('GET', "/instance/connectionState/{$instanceName}");
    }

    /** @return array<string, mixed> */
    public function sendText(string $instanceName, string $number, string $text): array
    {
        return $this->request('POST', "/message/sendText/{$instanceName}", [
            'number' => preg_replace('/\D/', '', $number),
            'text' => mb_substr($text, 0, 4096),
        ]);
    }

    /** @param array<string, mixed>|null $body @return array<string, mixed> */
    private function request(string $method, string $path, ?array $body = null): array
    {
        $url = $this->baseUrl() . $path;
        $key = (string) ($this->config['evolution_api_key'] ?? '');
        if ($this->baseUrl() === '' || $key === '') {
            throw new \RuntimeException('Configure evolution_api_url e evolution_api_key em config.php');
        }

        $ch = curl_init($url);
        if ($ch === false) {
            throw new \RuntimeException('curl_init falhou');
        }

        $headers = ['Content-Type: application/json', 'apikey: ' . $key];
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_TIMEOUT => 30,
        ]);

        if ($body !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body, JSON_THROW_ON_ERROR));
        }

        $raw = curl_exec($ch);
        $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err = curl_error($ch);
        curl_close($ch);

        if ($raw === false) {
            throw new \RuntimeException('Evolution API: ' . $err);
        }

        /** @var array<string, mixed> $data */
        $data = json_decode($raw, true) ?? ['raw' => $raw];
        if ($code >= 400) {
            $msg = is_string($data['message'] ?? null) ? $data['message'] : "HTTP {$code}";
            throw new \RuntimeException('Evolution API: ' . $msg);
        }

        return $data;
    }
}
