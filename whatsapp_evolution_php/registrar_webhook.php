<?php
/**
 * Registra webhook MESSAGES_UPSERT na instância Evolution da loja.
 *
 * Uso:
 *   cp config.example.php config.php   # preencher evolution_api_key
 *   php registrar_webhook.php
 *   php registrar_webhook.php lwk_loja_15
 */

declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';

use LWK\WhatsAppEvolution\EvolutionClient;

$configPath = __DIR__ . '/config.php';
if (!file_exists($configPath)) {
    fwrite(STDERR, "Crie config.php a partir de config.example.php\n");
    exit(1);
}

/** @var array<string, mixed> $config */
$config = require $configPath;

$client = new EvolutionClient($config);
$instance = $argv[1]
    ?? ($config['instance_name'] ?? $client->instanceName((int) ($config['empresa_id_exemplo'] ?? $config['loja_id'] ?? 1)));

try {
    $result = $client->setWebhook($instance);
    echo "Webhook registrado para {$instance}\n";
    echo 'URL: ' . $client->webhookUrl() . "\n";
    echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
} catch (Throwable $e) {
    fwrite(STDERR, 'Erro: ' . $e->getMessage() . "\n");
    exit(1);
}
