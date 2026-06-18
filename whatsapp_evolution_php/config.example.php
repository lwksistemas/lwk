<?php
/**
 * Copie para config.php e ajuste (não commite secrets).
 *
 * @return array<string, mixed>
 */
return [
    // Seu sistema (PHP + MySQL standalone)
    'app_name' => 'Meu Sistema',
    'app_url' => 'https://seusite.com.br',
    'db_host' => '127.0.0.1',
    'db_port' => '3306',
    'db_name' => 'meu_sistema',
    'db_user' => 'root',
    'db_pass' => '',
    'instance_prefix' => 'empresa_',

    // Evolution API (Railway / Docker)
    'evolution_api_url' => 'https://evolution-api-production-09bf.up.railway.app',
    'evolution_api_key' => 'SUA_AUTHENTICATION_API_KEY',

    // Webhook do SEU backend PHP (não Django)
    'webhook_url' => 'https://seusite.com.br/api/whatsapp/evolution/webhook.php',

    'meta_api_url' => 'https://graph.facebook.com/v19.0',

    // Referência LWK (opcional)
    'api_base_url' => 'https://api.lwksistemas.com.br',
    'frontend_url' => 'https://lwksistemas.com.br',

    // Empresa exemplo
    'empresa_id_exemplo' => 1,
    'loja_id' => 1,
    'loja_slug' => 'minha-empresa',
    'instance_name' => 'empresa_1',

    'evolution_docker_image' => 'evoapicloud/evolution-api:v2.3.7',
];
