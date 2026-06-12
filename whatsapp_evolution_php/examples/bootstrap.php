<?php

declare(strict_types=1);

/** Carrega config + PDO MySQL + autoload Composer. */

require_once dirname(__DIR__) . '/vendor/autoload.php';

$configFile = dirname(__DIR__) . '/config.php';
if (!file_exists($configFile)) {
    $configFile = dirname(__DIR__) . '/config.example.php';
}
$config = require $configFile;

$dsn = sprintf(
    'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
    $config['db_host'] ?? '127.0.0.1',
    $config['db_port'] ?? '3306',
    $config['db_name'] ?? 'meu_sistema',
);

$pdo = new PDO(
    $dsn,
    (string) ($config['db_user'] ?? 'root'),
    (string) ($config['db_pass'] ?? ''),
    [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ],
);

return [$config, $pdo];
