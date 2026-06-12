<?php
/**
 * Gera PDF do manual WhatsApp Evolution — PHP + MySQL (standalone).
 *
 *   composer install
 *   php gerar_manual_mysql.php
 *   php gerar_manual_mysql.php ../docs/manual-whatsapp-evolution-php-mysql.pdf
 */

declare(strict_types=1);

require_once __DIR__ . '/vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;
use LWK\WhatsAppEvolution\ManualPhpMysqlRenderer;

$config = file_exists(__DIR__ . '/config.php')
    ? require __DIR__ . '/config.php'
    : require __DIR__ . '/config.example.php';

$output = $argv[1] ?? __DIR__ . '/output/manual-whatsapp-evolution-php-mysql.pdf';
$dir = dirname($output);
if (!is_dir($dir)) {
    mkdir($dir, 0755, true);
}

$html = (new ManualPhpMysqlRenderer($config))->renderHtml();

$htmlPath = preg_replace('/\.pdf$/i', '.html', $output);
file_put_contents($htmlPath, $html);
echo "HTML gerado: {$htmlPath}\n";

$options = new Options();
$options->set('isRemoteEnabled', false);
$options->set('defaultFont', 'DejaVu Sans');

$dompdf = new Dompdf($options);
$dompdf->loadHtml($html);
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();
file_put_contents($output, $dompdf->output());

echo "PDF gerado: {$output}\n";
echo 'Tamanho: ' . number_format(filesize($output) / 1024, 1) . " KB\n";
