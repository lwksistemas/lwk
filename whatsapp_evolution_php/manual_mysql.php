<?php

declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';

use LWK\WhatsAppEvolution\ManualPhpMysqlRenderer;

$config = file_exists(__DIR__ . '/config.php')
    ? require __DIR__ . '/config.php'
    : require __DIR__ . '/config.example.php';

header('Content-Type: text/html; charset=utf-8');
echo (new ManualPhpMysqlRenderer($config))->renderHtml();
