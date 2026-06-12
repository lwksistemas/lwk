<?php
/**
 * Visualizar manual HTML no navegador:
 *   php -S localhost:8080 manual.php
 * ou abra via servidor web apontando para whatsapp_evolution_php/
 */

declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';

use LWK\WhatsAppEvolution\ManualRenderer;

$config = file_exists(__DIR__ . '/config.php')
    ? require __DIR__ . '/config.php'
    : require __DIR__ . '/config.example.php';

header('Content-Type: text/html; charset=UTF-8');
echo (new ManualRenderer($config))->renderHtml();
