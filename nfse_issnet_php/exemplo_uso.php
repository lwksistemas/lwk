<?php
/**
 * Exemplo de uso — ISSNetClient
 * Emissão, Cancelamento, Consulta URL, Reenvio Email
 */

require_once __DIR__ . '/vendor/autoload.php'; // composer require robrichards/xmlseclibs
require_once __DIR__ . '/ISSNetClient.php';

use LWK\NFSe\ISSNetClient;

// ═══════════════════════════════════════════════════════════════════
// CONFIGURAÇÃO
// ═══════════════════════════════════════════════════════════════════

$client = new ISSNetClient(
    usuario: 'SEU_USUARIO_ISSNET',
    senha: 'SUA_SENHA_ISSNET',
    certificadoPath: '/caminho/para/certificado.pfx',
    senhaCertificado: 'SENHA_DO_PFX',
    ambiente: 'producao' // ou 'homologacao'
);

// ═══════════════════════════════════════════════════════════════════
// 1. EMISSÃO DE NFS-e
// ═══════════════════════════════════════════════════════════════════

$resultado = $client->emitirNfse([
    'prestador_cnpj' => '24758458000172',
    'prestador_inscricao_municipal' => '123456',
    'tomador_cpf_cnpj' => '12345678901',
    'tomador_nome' => 'João da Silva',
    'tomador_logradouro' => 'Rua Exemplo',
    'tomador_numero' => '123',
    'tomador_bairro' => 'Centro',
    'tomador_uf' => 'SP',
    'tomador_cep' => '14000000',
    'descricao_servico' => 'Desenvolvimento de software - Maio/2026',
    'valor_servicos' => 1500.00,
    'aliquota_iss' => 2.00,
    'item_lista_servico' => '14.01',
    'codigo_tributacao' => '1401',
    'numero_rps' => 143,
    'serie_rps' => 'E',
]);

if ($resultado['success']) {
    echo "✅ NFS-e emitida! Número: {$resultado['numero_nf']}\n";
    echo "   Código Verificação: {$resultado['codigo_verificacao']}\n";
} else {
    echo "❌ Erro: {$resultado['error']}\n";
}

// ═══════════════════════════════════════════════════════════════════
// 2. CONSULTAR URL DA DANFE (PDF REAL)
// ═══════════════════════════════════════════════════════════════════

$url = $client->consultarUrlNfse(
    numeroNf: '142',
    cnpj: '24758458000172',
    im: '123456'
);

if ($url['success']) {
    echo "📄 URL DANFE: {$url['url']}\n";
} else {
    echo "❌ Erro ao consultar URL: {$url['error']}\n";
}

// ═══════════════════════════════════════════════════════════════════
// 3. CANCELAMENTO DE NFS-e
// ═══════════════════════════════════════════════════════════════════

$cancel = $client->cancelarNfse(
    numeroNf: '142',
    cnpj: '24758458000172',
    im: '123456',
    codigo: '1' // 1=Erro emissão, 2=Serviço não prestado, 3=Erro assinatura, 4=Duplicidade
);

if ($cancel['success']) {
    echo "✅ NFS-e cancelada!\n";
} else {
    echo "❌ Erro ao cancelar: {$cancel['error']}\n";
}

// ═══════════════════════════════════════════════════════════════════
// 4. REENVIO POR EMAIL (usando a URL da DANFE)
// ═══════════════════════════════════════════════════════════════════

function reenviarNfseEmail(string $email, string $urlDanfe, string $xmlNfse, array $dadosNota): bool
{
    $assunto = "Nota Fiscal de Serviço Nº {$dadosNota['numero_nf']} - {$dadosNota['prestador']}";
    
    $corpo = "Olá {$dadosNota['tomador_nome']}!\n\n"
        . "Segue a nota fiscal referente ao serviço prestado.\n\n"
        . "📋 DADOS DA NOTA FISCAL:\n"
        . "• Número: {$dadosNota['numero_nf']}\n"
        . "• Prestador: {$dadosNota['prestador']}\n"
        . "• Valor: R$ " . number_format($dadosNota['valor'], 2, ',', '.') . "\n"
        . "• Código de Verificação: {$dadosNota['codigo_verificacao']}\n\n";

    if ($urlDanfe) {
        $corpo .= "📄 VISUALIZAR NOTA FISCAL (DANFE):\n{$urlDanfe}\n\n";
    }

    $corpo .= "Atenciosamente,\n{$dadosNota['prestador']}";

    // Enviar com PHPMailer ou mail()
    $headers = "From: noreply@seudominio.com.br\r\n";
    $headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
    
    return mail($email, $assunto, $corpo, $headers);
}

// Exemplo de uso do reenvio:
if ($url['success']) {
    reenviarNfseEmail(
        email: 'cliente@exemplo.com',
        urlDanfe: $url['url'],
        xmlNfse: $resultado['xml'] ?? '',
        dadosNota: [
            'numero_nf' => '142',
            'prestador' => 'LWK Sistemas',
            'tomador_nome' => 'João da Silva',
            'valor' => 1500.00,
            'codigo_verificacao' => $resultado['codigo_verificacao'] ?? '',
        ]
    );
    echo "📧 Email reenviado com link da DANFE!\n";
}
