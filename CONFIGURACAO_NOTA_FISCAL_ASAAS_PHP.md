# Configuração Completa - Emissão de Nota Fiscal via Asaas (PHP)

## 📋 Índice
1. Variáveis de Ambiente
2. Configuração no Painel Asaas
3. Classe Cliente Asaas (PHP)
4. Serviço de Emissão de NF
5. Endpoints de API
6. Exemplos de Uso
7. Webhook para Emissão Automática
8. Troubleshooting

---

## 1️⃣ VARIÁVEIS DE AMBIENTE

Configure estas variáveis no seu servidor PHP (arquivo `.env` ou configuração do servidor):

```bash
# Configuração Asaas
ASAAS_API_KEY=sua_chave_api_aqui
ASAAS_SANDBOX=false

# Configuração do Serviço Municipal (Ribeirão Preto-SP)
ASAAS_INVOICE_SERVICE_ID=262124
ASAAS_INVOICE_SERVICE_CODE=1401
ASAAS_INVOICE_SERVICE_NAME="Reparação e manutenção de computadores e de equipamentos periféricos"

# Email para notificações
DEFAULT_FROM_EMAIL=noreply@seudominio.com.br
```

---

## 2️⃣ CONFIGURAÇÃO NO PAINEL ASAAS

Acesse: https://www.asaas.com/config/nfse

### Configurações Obrigatórias:

1. **Município:** Ribeirão Preto-SP
2. **Código de Serviço:** 14.01 (4 dígitos: 1401)
3. **Descrição:** Reparação e manutenção de computadores
4. **ID do Serviço (interno Asaas):** 262124
5. **Alíquota ISS:** 2% (mínimo exigido pela prefeitura)
6. **Número RPS:** Sequencial (configurado no painel)

### Impostos:
- ISS: 2%
- COFINS: 0%
- CSLL: 0%
- INSS: 0%
- IR: 0%
- PIS: 0%
- Retenção ISS: Não

---


## 3️⃣ CLASSE CLIENTE ASAAS (PHP)

### Arquivo: `AsaasClient.php`

```php
<?php

/**
 * Cliente para integração com API do Asaas
 * Gerencia cobranças, clientes e notas fiscais
 */
class AsaasClient {
    
    private $apiKey;
    private $sandbox;
    private $baseUrl;
    
    public function __construct($apiKey = null, $sandbox = null) {
        $this->apiKey = $apiKey ?? getenv('ASAAS_API_KEY');
        
        // Auto-detectar sandbox se não especificado
        if ($sandbox === null) {
            $this->sandbox = strpos($this->apiKey, 'hmlg') !== false;
        } else {
            $this->sandbox = $sandbox;
        }
        
        $this->baseUrl = $this->sandbox 
            ? 'https://sandbox.asaas.com/api/v3'
            : 'https://api.asaas.com/v3';
    }
    
    /**
     * Faz requisição para API do Asaas
     */
    private function makeRequest($method, $endpoint, $data = null) {
        $url = $this->baseUrl . '/' . $endpoint;
        
        $headers = [
            'access_token: ' . $this->apiKey,
            'Content-Type: application/json',
            'User-Agent: Sistema PHP/1.0'
        ];
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        
        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            if ($data) {
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            }
        } elseif ($method === 'PUT') {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
            if ($data) {
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            }
        } elseif ($method === 'DELETE') {
            curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'DELETE');
        } elseif ($method === 'GET' && $data) {
            $url .= '?' . http_build_query($data);
            curl_setopt($ch, CURLOPT_URL, $url);
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            throw new Exception("Erro na requisição cURL: " . $error);
        }
        
        if ($httpCode >= 400) {
            error_log("Erro na API Asaas: HTTP $httpCode - $response");
            throw new Exception("Erro na API Asaas: HTTP $httpCode");
        }
        
        return json_decode($response, true);
    }
    
    /**
     * Cria um cliente no Asaas
     */
    public function createCustomer($customerData) {
        return $this->makeRequest('POST', 'customers', $customerData);
    }
    
    /**
     * Busca um cliente no Asaas
     */
    public function getCustomer($customerId) {
        return $this->makeRequest('GET', "customers/$customerId");
    }
    
    /**
     * Cria uma cobrança no Asaas
     */
    public function createPayment($paymentData) {
        return $this->makeRequest('POST', 'payments', $paymentData);
    }
    
    /**
     * Busca uma cobrança no Asaas
     */
    public function getPayment($paymentId) {
        return $this->makeRequest('GET', "payments/$paymentId");
    }
    
    /**
     * Busca dados do QR Code PIX
     */
    public function getPixQrCode($paymentId) {
        return $this->makeRequest('GET', "payments/$paymentId/pixQrCode");
    }
    
    /**
     * Agenda uma nota fiscal vinculada a uma cobrança
     * 
     * @param string $paymentId ID da cobrança no Asaas
     * @param string $serviceDescription Descrição do serviço
     * @param float $value Valor da nota fiscal
     * @param string $effectiveDate Data de competência (YYYY-MM-DD)
     * @param string|null $municipalServiceCode Código do serviço municipal
     * @param string|null $municipalServiceName Nome do serviço municipal
     * @param string|null $municipalServiceId ID interno do serviço no Asaas
     * @param string|null $observations Observações adicionais
     * @return array Dados da nota fiscal agendada
     */
    public function createInvoice(
        $paymentId,
        $serviceDescription,
        $value,
        $effectiveDate,
        $municipalServiceCode = null,
        $municipalServiceName = null,
        $municipalServiceId = null,
        $observations = null
    ) {
        $data = [
            'payment' => $paymentId,
            'serviceDescription' => $serviceDescription,
            'value' => floatval($value),
            'effectiveDate' => $effectiveDate,
        ];
        
        // Campos municipais (TODOS são necessários para funcionar)
        if ($municipalServiceId) {
            $data['municipalServiceId'] = $municipalServiceId;
        }
        if ($municipalServiceCode) {
            $data['municipalServiceCode'] = $municipalServiceCode;
        }
        if ($municipalServiceName) {
            $data['municipalServiceName'] = $municipalServiceName;
        }
        if ($observations) {
            $data['observations'] = $observations;
        }
        
        // Configurar impostos (ISS 2% conforme prefeitura)
        $data['taxes'] = [
            'retainIss' => false,
            'iss' => 2.0,      // 2%
            'cofins' => 0.0,
            'csll' => 0.0,
            'inss' => 0.0,
            'ir' => 0.0,
            'pis' => 0.0,
        ];
        
        return $this->makeRequest('POST', 'invoices', $data);
    }
    
    /**
     * Emite (autoriza) uma nota fiscal já agendada
     */
    public function authorizeInvoice($invoiceId) {
        return $this->makeRequest('POST', "invoices/$invoiceId/authorize", []);
    }
    
    /**
     * Busca uma nota fiscal (para obter link do PDF)
     */
    public function getInvoice($invoiceId) {
        return $this->makeRequest('GET', "invoices/$invoiceId");
    }
    
    /**
     * Lista notas fiscais de um pagamento
     */
    public function listInvoicesByPayment($paymentId) {
        return $this->makeRequest('GET', 'invoices', ['payment' => $paymentId]);
    }
    
    /**
     * Cancela uma nota fiscal
     */
    public function cancelInvoice($invoiceId) {
        return $this->makeRequest('DELETE', "invoices/$invoiceId");
    }
}
```

---


## 4️⃣ SERVIÇO DE EMISSÃO DE NOTA FISCAL

### Arquivo: `InvoiceService.php`

```php
<?php

/**
 * Serviço de emissão de Nota Fiscal via API Asaas
 */
class InvoiceService {
    
    private $asaasClient;
    
    public function __construct() {
        $this->asaasClient = new AsaasClient();
    }
    
    /**
     * Obtém configuração municipal das variáveis de ambiente
     */
    private function getMunicipalConfig() {
        $serviceId = getenv('ASAAS_INVOICE_SERVICE_ID') ?: '';
        $code = getenv('ASAAS_INVOICE_SERVICE_CODE') ?: '';
        $name = getenv('ASAAS_INVOICE_SERVICE_NAME') ?: '';
        
        // Se service_id está configurado, usar TODOS os campos
        if ($serviceId) {
            $defaultCode = $code ?: '1401';
            $defaultName = $name ?: 'Reparação e manutenção de computadores e de equipamentos periféricos';
            
            error_log("Configuração municipal NF: municipalServiceId=$serviceId, code=$defaultCode, name=$defaultName");
            
            return [
                'municipal_service_code' => $defaultCode,
                'municipal_service_name' => $defaultName,
                'municipal_service_id' => $serviceId,
            ];
        }
        
        // Fallback: usar code e name
        if ($code) {
            // Remover pontuação do código
            $code = preg_replace('/[^0-9]/', '', $code);
        }
        
        return [
            'municipal_service_code' => $code ?: null,
            'municipal_service_name' => $name ?: null,
            'municipal_service_id' => null,
        ];
    }
    
    /**
     * Emite nota fiscal para um pagamento
     * 
     * @param string $asaasPaymentId ID da cobrança no Asaas
     * @param array $clienteData Dados do cliente (nome, email)
     * @param float $value Valor da nota fiscal
     * @param string $description Descrição do serviço
     * @param bool $sendEmail Se deve enviar email ao cliente
     * @return array Resultado da emissão
     */
    public function emitirNotaFiscal(
        $asaasPaymentId,
        $clienteData,
        $value,
        $description,
        $sendEmail = true
    ) {
        $result = [
            'success' => false,
            'invoice_id' => null,
            'error' => null,
            'email_sent' => false
        ];
        
        try {
            // 1. Obter configuração municipal
            $municipal = $this->getMunicipalConfig();
            $effectiveDate = date('Y-m-d');
            $serviceDescription = $description ?: 'Assinatura de Sistema';
            
            error_log("Emitindo NF para payment: $asaasPaymentId");
            
            // 2. Agendar nota fiscal
            $invoice = $this->asaasClient->createInvoice(
                $asaasPaymentId,
                $serviceDescription,
                $value,
                $effectiveDate,
                $municipal['municipal_service_code'],
                $municipal['municipal_service_name'],
                $municipal['municipal_service_id']
            );
            
            $invoiceId = $invoice['id'] ?? null;
            
            if (!$invoiceId) {
                $result['error'] = 'Resposta da API sem id da nota fiscal';
                error_log("Erro: Resposta sem invoice_id");
                return $result;
            }
            
            error_log("NF agendada: invoice_id=$invoiceId");
            
            // 3. Autorizar (emitir) nota fiscal
            $this->asaasClient->authorizeInvoice($invoiceId);
            
            $result['success'] = true;
            $result['invoice_id'] = $invoiceId;
            
            error_log("NF emitida com sucesso: invoice_id=$invoiceId");
            
            // 4. Enviar email ao cliente (opcional)
            if ($sendEmail && isset($clienteData['email'])) {
                try {
                    $this->enviarEmailNotaFiscal(
                        $clienteData['email'],
                        $clienteData['nome'] ?? 'Cliente',
                        $invoiceId,
                        $value,
                        $serviceDescription
                    );
                    $result['email_sent'] = true;
                    error_log("Email da NF enviado para: " . $clienteData['email']);
                } catch (Exception $e) {
                    error_log("Erro ao enviar email da NF: " . $e->getMessage());
                    $result['error'] = 'NF emitida, mas falha no envio do email';
                }
            }
            
        } catch (Exception $e) {
            error_log("Erro ao emitir NF: " . $e->getMessage());
            $result['error'] = $e->getMessage();
        }
        
        return $result;
    }
    
    /**
     * Envia email com a nota fiscal
     */
    private function enviarEmailNotaFiscal($toEmail, $clienteNome, $invoiceId, $value, $description) {
        $subject = 'Nota Fiscal – Assinatura';
        
        $body = "Olá $clienteNome,\n\n";
        $body .= "A nota fiscal referente à sua assinatura foi emitida.\n\n";
        $body .= "Identificador da NF: $invoiceId\n";
        $body .= "Descrição: $description\n";
        $body .= "Valor: R$ " . number_format($value, 2, ',', '.') . "\n\n";
        $body .= "Você pode acessar a nota fiscal através do painel Asaas ou solicitar o reenvio.\n\n";
        $body .= "Em caso de dúvidas, entre em contato com o suporte.";
        
        $fromEmail = getenv('DEFAULT_FROM_EMAIL') ?: 'noreply@seudominio.com.br';
        
        $headers = [
            'From: ' . $fromEmail,
            'Reply-To: ' . $fromEmail,
            'Content-Type: text/plain; charset=UTF-8'
        ];
        
        $success = mail($toEmail, $subject, $body, implode("\r\n", $headers));
        
        if (!$success) {
            throw new Exception("Falha ao enviar email");
        }
    }
    
    /**
     * Busca nota fiscal de um pagamento
     * 
     * @param string $paymentId ID do pagamento no Asaas
     * @return array|null Dados da nota fiscal ou null se não encontrada
     */
    public function buscarNotaFiscalPorPagamento($paymentId) {
        try {
            // Buscar notas fiscais do pagamento
            $response = $this->asaasClient->listInvoicesByPayment($paymentId);
            $invoices = $response['data'] ?? [];
            
            if (empty($invoices)) {
                return null;
            }
            
            // Buscar nota autorizada
            foreach ($invoices as $invoice) {
                if ($invoice['status'] === 'AUTHORIZED') {
                    return $invoice;
                }
            }
            
            // Se não encontrou autorizada, retornar a primeira
            return $invoices[0];
            
        } catch (Exception $e) {
            error_log("Erro ao buscar nota fiscal: " . $e->getMessage());
            return null;
        }
    }
}
```

---


## 5️⃣ ENDPOINTS DE API (PHP)

### Arquivo: `api_nota_fiscal.php`

```php
<?php

require_once 'AsaasClient.php';
require_once 'InvoiceService.php';

// Configurar headers para API REST
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Tratar OPTIONS (CORS preflight)
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Função auxiliar para retornar JSON
function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

// Roteamento simples
$requestUri = $_SERVER['REQUEST_URI'];
$requestMethod = $_SERVER['REQUEST_METHOD'];

// Extrair ação e ID da URL
// Exemplo: /api/nota-fiscal/baixar/123
preg_match('#/api/nota-fiscal/([^/]+)(?:/(\d+))?#', $requestUri, $matches);
$action = $matches[1] ?? null;
$id = $matches[2] ?? null;

// Instanciar serviço
$invoiceService = new InvoiceService();

/**
 * ENDPOINT: Baixar Nota Fiscal
 * GET /api/nota-fiscal/baixar/{payment_id}
 */
if ($action === 'baixar' && $requestMethod === 'GET' && $id) {
    try {
        // Buscar nota fiscal do pagamento
        $invoice = $invoiceService->buscarNotaFiscalPorPagamento($id);
        
        if (!$invoice) {
            jsonResponse([
                'success' => false,
                'error' => 'Nenhuma nota fiscal encontrada para este pagamento. A nota fiscal é emitida automaticamente após a confirmação do pagamento.'
            ], 404);
        }
        
        $invoiceId = $invoice['id'];
        $status = $invoice['status'];
        
        // Verificar se está autorizada
        if ($status !== 'AUTHORIZED') {
            jsonResponse([
                'success' => false,
                'error' => "Nota fiscal ainda não foi autorizada. Status atual: $status"
            ], 400);
        }
        
        // Buscar URL do PDF
        $pdfUrl = $invoice['pdfUrl'] ?? $invoice['invoicePdfUrl'] ?? $invoice['invoiceUrl'] ?? null;
        
        if (!$pdfUrl) {
            jsonResponse([
                'success' => false,
                'error' => 'URL do PDF da nota fiscal não disponível. Aguarde alguns minutos após a emissão.'
            ], 404);
        }
        
        // Retornar URL do PDF
        jsonResponse([
            'success' => true,
            'pdf_url' => $pdfUrl,
            'invoice_id' => $invoiceId,
            'status' => $status
        ]);
        
    } catch (Exception $e) {
        error_log("Erro ao baixar nota fiscal: " . $e->getMessage());
        jsonResponse([
            'success' => false,
            'error' => $e->getMessage()
        ], 500);
    }
}

/**
 * ENDPOINT: Reenviar Nota Fiscal
 * POST /api/nota-fiscal/reenviar/{payment_id}
 */
if ($action === 'reenviar' && $requestMethod === 'POST' && $id) {
    try {
        // Obter dados do cliente do corpo da requisição
        $input = json_decode(file_get_contents('php://input'), true);
        $clienteEmail = $input['email'] ?? null;
        $clienteNome = $input['nome'] ?? 'Cliente';
        
        if (!$clienteEmail) {
            jsonResponse([
                'success' => false,
                'error' => 'Email do cliente é obrigatório'
            ], 400);
        }
        
        // Buscar nota fiscal do pagamento
        $invoice = $invoiceService->buscarNotaFiscalPorPagamento($id);
        
        if (!$invoice) {
            jsonResponse([
                'success' => false,
                'error' => 'Nenhuma nota fiscal encontrada para este pagamento.'
            ], 404);
        }
        
        $invoiceId = $invoice['id'];
        $status = $invoice['status'];
        
        // Verificar se está autorizada
        if ($status !== 'AUTHORIZED') {
            jsonResponse([
                'success' => false,
                'error' => "Nota fiscal ainda não foi autorizada. Status atual: $status"
            ], 400);
        }
        
        // Buscar URL do PDF
        $pdfUrl = $invoice['pdfUrl'] ?? $invoice['invoicePdfUrl'] ?? $invoice['invoiceUrl'] ?? null;
        $value = $invoice['value'] ?? 0;
        $description = $invoice['serviceDescription'] ?? 'Assinatura';
        
        // Enviar email
        $subject = 'Nota Fiscal – Assinatura';
        
        $body = "Olá $clienteNome,\n\n";
        $body .= "A nota fiscal referente à sua assinatura foi emitida.\n\n";
        $body .= "Identificador da NF: $invoiceId\n";
        $body .= "Valor: R$ " . number_format($value, 2, ',', '.') . "\n\n";
        
        if ($pdfUrl) {
            $body .= "Acesse a nota fiscal em: $pdfUrl\n\n";
        }
        
        $body .= "Em caso de dúvidas, entre em contato com o suporte.";
        
        $fromEmail = getenv('DEFAULT_FROM_EMAIL') ?: 'noreply@seudominio.com.br';
        
        $headers = [
            'From: ' . $fromEmail,
            'Reply-To: ' . $fromEmail,
            'Content-Type: text/plain; charset=UTF-8'
        ];
        
        $emailSent = mail($clienteEmail, $subject, $body, implode("\r\n", $headers));
        
        if (!$emailSent) {
            jsonResponse([
                'success' => false,
                'error' => 'Erro ao enviar email'
            ], 500);
        }
        
        jsonResponse([
            'success' => true,
            'message' => "Nota fiscal reenviada para $clienteEmail"
        ]);
        
    } catch (Exception $e) {
        error_log("Erro ao reenviar nota fiscal: " . $e->getMessage());
        jsonResponse([
            'success' => false,
            'error' => $e->getMessage()
        ], 500);
    }
}

/**
 * ENDPOINT: Emitir Nota Fiscal Manualmente
 * POST /api/nota-fiscal/emitir
 */
if ($action === 'emitir' && $requestMethod === 'POST') {
    try {
        // Obter dados do corpo da requisição
        $input = json_decode(file_get_contents('php://input'), true);
        
        $paymentId = $input['payment_id'] ?? null;
        $clienteNome = $input['cliente_nome'] ?? 'Cliente';
        $clienteEmail = $input['cliente_email'] ?? null;
        $value = $input['value'] ?? null;
        $description = $input['description'] ?? 'Assinatura';
        
        // Validar dados obrigatórios
        if (!$paymentId || !$value) {
            jsonResponse([
                'success' => false,
                'error' => 'payment_id e value são obrigatórios'
            ], 400);
        }
        
        // Emitir nota fiscal
        $result = $invoiceService->emitirNotaFiscal(
            $paymentId,
            [
                'nome' => $clienteNome,
                'email' => $clienteEmail
            ],
            $value,
            $description,
            !empty($clienteEmail)
        );
        
        if ($result['success']) {
            jsonResponse($result);
        } else {
            jsonResponse($result, 500);
        }
        
    } catch (Exception $e) {
        error_log("Erro ao emitir nota fiscal: " . $e->getMessage());
        jsonResponse([
            'success' => false,
            'error' => $e->getMessage()
        ], 500);
    }
}

// Rota não encontrada
jsonResponse([
    'error' => 'Endpoint não encontrado'
], 404);
```

---


## 6️⃣ EXEMPLOS DE USO

### Exemplo 1: Emitir Nota Fiscal Manualmente

```php
<?php

require_once 'InvoiceService.php';

// Dados do pagamento e cliente
$paymentId = 'pay_abc123';  // ID da cobrança no Asaas
$clienteData = [
    'nome' => 'João Silva',
    'email' => 'joao@example.com'
];
$value = 99.90;
$description = 'Assinatura Plano Premium - Janeiro/2026';

// Emitir nota fiscal
$invoiceService = new InvoiceService();
$result = $invoiceService->emitirNotaFiscal(
    $paymentId,
    $clienteData,
    $value,
    $description,
    true  // Enviar email
);

if ($result['success']) {
    echo "✅ Nota fiscal emitida com sucesso!\n";
    echo "Invoice ID: " . $result['invoice_id'] . "\n";
    echo "Email enviado: " . ($result['email_sent'] ? 'Sim' : 'Não') . "\n";
} else {
    echo "❌ Erro ao emitir nota fiscal: " . $result['error'] . "\n";
}
```

### Exemplo 2: Buscar e Baixar Nota Fiscal

```php
<?php

require_once 'InvoiceService.php';

$paymentId = 'pay_abc123';

$invoiceService = new InvoiceService();
$invoice = $invoiceService->buscarNotaFiscalPorPagamento($paymentId);

if ($invoice) {
    echo "✅ Nota fiscal encontrada!\n";
    echo "Invoice ID: " . $invoice['id'] . "\n";
    echo "Status: " . $invoice['status'] . "\n";
    echo "Valor: R$ " . number_format($invoice['value'], 2, ',', '.') . "\n";
    
    // URL do PDF
    $pdfUrl = $invoice['pdfUrl'] ?? $invoice['invoicePdfUrl'] ?? null;
    if ($pdfUrl) {
        echo "PDF: $pdfUrl\n";
    }
} else {
    echo "❌ Nota fiscal não encontrada\n";
}
```

### Exemplo 3: Criar Cobrança e Emitir NF Automaticamente

```php
<?php

require_once 'AsaasClient.php';
require_once 'InvoiceService.php';

// 1. Criar cliente
$asaasClient = new AsaasClient();

$customerData = [
    'name' => 'Maria Santos',
    'email' => 'maria@example.com',
    'cpfCnpj' => '12345678901',
    'phone' => '16999999999',
    'address' => 'Rua Exemplo',
    'addressNumber' => '123',
    'province' => 'Centro',
    'city' => 'Ribeirão Preto',
    'state' => 'SP',
    'postalCode' => '14000000'
];

$customer = $asaasClient->createCustomer($customerData);
$customerId = $customer['id'];

echo "✅ Cliente criado: $customerId\n";

// 2. Criar cobrança
$paymentData = [
    'customer' => $customerId,
    'billingType' => 'BOLETO',
    'value' => 99.90,
    'dueDate' => date('Y-m-d', strtotime('+7 days')),
    'description' => 'Assinatura Plano Premium - Janeiro/2026'
];

$payment = $asaasClient->createPayment($paymentData);
$paymentId = $payment['id'];

echo "✅ Cobrança criada: $paymentId\n";
echo "Boleto: " . $payment['bankSlipUrl'] . "\n";

// 3. Simular pagamento (em produção, isso vem via webhook)
// Aguardar confirmação do pagamento...

// 4. Emitir nota fiscal após pagamento confirmado
$invoiceService = new InvoiceService();
$result = $invoiceService->emitirNotaFiscal(
    $paymentId,
    [
        'nome' => $customerData['name'],
        'email' => $customerData['email']
    ],
    99.90,
    'Assinatura Plano Premium - Janeiro/2026',
    true
);

if ($result['success']) {
    echo "✅ Nota fiscal emitida: " . $result['invoice_id'] . "\n";
} else {
    echo "❌ Erro ao emitir NF: " . $result['error'] . "\n";
}
```

---


## 7️⃣ WEBHOOK PARA EMISSÃO AUTOMÁTICA

### Arquivo: `webhook_asaas.php`

```php
<?php

/**
 * Webhook do Asaas para processar notificações de pagamento
 * Configure este endpoint no painel Asaas: https://www.asaas.com/config/webhooks
 * 
 * URL do webhook: https://seudominio.com.br/webhook_asaas.php
 * 
 * Eventos para configurar:
 * - PAYMENT_RECEIVED
 * - PAYMENT_CONFIRMED
 */

require_once 'InvoiceService.php';

// Log de entrada
error_log("=== Webhook Asaas recebido ===");
error_log("Method: " . $_SERVER['REQUEST_METHOD']);
error_log("Headers: " . json_encode(getallheaders()));

// Ler corpo da requisição
$input = file_get_contents('php://input');
error_log("Body: " . $input);

// Decodificar JSON
$data = json_decode($input, true);

if (!$data) {
    error_log("Erro: JSON inválido");
    http_response_code(400);
    exit;
}

// Extrair dados do webhook
$event = $data['event'] ?? null;
$paymentData = $data['payment'] ?? null;

if (!$event || !$paymentData) {
    error_log("Erro: Dados incompletos no webhook");
    http_response_code(400);
    exit;
}

$paymentId = $paymentData['id'] ?? null;
$status = $paymentData['status'] ?? null;
$value = $paymentData['value'] ?? 0;
$description = $paymentData['description'] ?? 'Assinatura';
$customerEmail = $paymentData['customer'] ?? null;

error_log("Event: $event");
error_log("Payment ID: $paymentId");
error_log("Status: $status");

// Processar apenas pagamentos confirmados
if (in_array($event, ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED'])) {
    
    try {
        // 1. Atualizar status do pagamento no banco de dados
        // (Implemente aqui a lógica de atualização do seu banco)
        
        // Exemplo:
        // $db = new PDO('mysql:host=localhost;dbname=seu_banco', 'usuario', 'senha');
        // $stmt = $db->prepare("UPDATE pagamentos SET status = 'pago', data_pagamento = NOW() WHERE asaas_payment_id = ?");
        // $stmt->execute([$paymentId]);
        
        error_log("✅ Status do pagamento atualizado no banco");
        
        // 2. Buscar dados do cliente no banco
        // (Implemente aqui a lógica de busca do cliente)
        
        // Exemplo:
        // $stmt = $db->prepare("SELECT nome, email FROM clientes WHERE asaas_payment_id = ?");
        // $stmt->execute([$paymentId]);
        // $cliente = $stmt->fetch(PDO::FETCH_ASSOC);
        
        // Para este exemplo, vamos usar dados do webhook
        $clienteData = [
            'nome' => $paymentData['customerName'] ?? 'Cliente',
            'email' => $customerEmail
        ];
        
        // 3. Emitir nota fiscal automaticamente
        $invoiceService = new InvoiceService();
        $result = $invoiceService->emitirNotaFiscal(
            $paymentId,
            $clienteData,
            $value,
            $description,
            true  // Enviar email
        );
        
        if ($result['success']) {
            error_log("✅ Nota fiscal emitida automaticamente: " . $result['invoice_id']);
            error_log("Email enviado: " . ($result['email_sent'] ? 'Sim' : 'Não'));
        } else {
            error_log("❌ Erro ao emitir nota fiscal: " . $result['error']);
        }
        
    } catch (Exception $e) {
        error_log("❌ Erro ao processar webhook: " . $e->getMessage());
    }
}

// Retornar 200 OK para o Asaas
http_response_code(200);
echo json_encode(['success' => true]);
```

### Configurar Webhook no Asaas:

1. Acesse: https://www.asaas.com/config/webhooks
2. Adicione novo webhook
3. URL: `https://seudominio.com.br/webhook_asaas.php`
4. Eventos:
   - ✅ PAYMENT_RECEIVED
   - ✅ PAYMENT_CONFIRMED
5. Salvar

---


## 8️⃣ INTEGRAÇÃO COM BANCO DE DADOS

### Arquivo: `database.php`

```php
<?php

/**
 * Exemplo de estrutura de banco de dados para gerenciar pagamentos e notas fiscais
 */

// Tabela: clientes
$sqlClientes = "
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    cpf_cnpj VARCHAR(20) NOT NULL,
    telefone VARCHAR(20),
    asaas_customer_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_asaas_customer (asaas_customer_id),
    INDEX idx_cpf_cnpj (cpf_cnpj)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
";

// Tabela: pagamentos
$sqlPagamentos = "
CREATE TABLE IF NOT EXISTS pagamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    asaas_payment_id VARCHAR(50) NOT NULL,
    valor DECIMAL(10,2) NOT NULL,
    descricao TEXT,
    status VARCHAR(20) DEFAULT 'pendente',
    data_vencimento DATE NOT NULL,
    data_pagamento DATETIME,
    boleto_url TEXT,
    pix_qr_code TEXT,
    pix_copy_paste TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    INDEX idx_asaas_payment (asaas_payment_id),
    INDEX idx_status (status),
    INDEX idx_vencimento (data_vencimento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
";

// Tabela: notas_fiscais
$sqlNotasFiscais = "
CREATE TABLE IF NOT EXISTS notas_fiscais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pagamento_id INT NOT NULL,
    asaas_invoice_id VARCHAR(50) NOT NULL,
    numero_nf VARCHAR(50),
    valor DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'agendada',
    pdf_url TEXT,
    data_emissao DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (pagamento_id) REFERENCES pagamentos(id),
    INDEX idx_asaas_invoice (asaas_invoice_id),
    INDEX idx_pagamento (pagamento_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
";

/**
 * Classe para gerenciar banco de dados
 */
class Database {
    
    private $pdo;
    
    public function __construct() {
        $host = getenv('DB_HOST') ?: 'localhost';
        $dbname = getenv('DB_NAME') ?: 'seu_banco';
        $user = getenv('DB_USER') ?: 'root';
        $pass = getenv('DB_PASS') ?: '';
        
        $dsn = "mysql:host=$host;dbname=$dbname;charset=utf8mb4";
        $this->pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
        ]);
    }
    
    /**
     * Salva nota fiscal no banco
     */
    public function salvarNotaFiscal($pagamentoId, $invoiceId, $valor, $status = 'agendada') {
        $sql = "INSERT INTO notas_fiscais (pagamento_id, asaas_invoice_id, valor, status) 
                VALUES (?, ?, ?, ?)";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$pagamentoId, $invoiceId, $valor, $status]);
        return $this->pdo->lastInsertId();
    }
    
    /**
     * Atualiza status da nota fiscal
     */
    public function atualizarStatusNotaFiscal($invoiceId, $status, $pdfUrl = null, $numeroNf = null) {
        $sql = "UPDATE notas_fiscais 
                SET status = ?, pdf_url = ?, numero_nf = ?, data_emissao = NOW()
                WHERE asaas_invoice_id = ?";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$status, $pdfUrl, $numeroNf, $invoiceId]);
    }
    
    /**
     * Busca nota fiscal por pagamento
     */
    public function buscarNotaFiscalPorPagamento($pagamentoId) {
        $sql = "SELECT * FROM notas_fiscais WHERE pagamento_id = ? ORDER BY created_at DESC LIMIT 1";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$pagamentoId]);
        return $stmt->fetch();
    }
    
    /**
     * Atualiza status do pagamento
     */
    public function atualizarStatusPagamento($asaasPaymentId, $status, $dataPagamento = null) {
        $sql = "UPDATE pagamentos SET status = ?, data_pagamento = ? WHERE asaas_payment_id = ?";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$status, $dataPagamento, $asaasPaymentId]);
    }
    
    /**
     * Busca pagamento por ID do Asaas
     */
    public function buscarPagamentoPorAsaasId($asaasPaymentId) {
        $sql = "SELECT p.*, c.nome as cliente_nome, c.email as cliente_email 
                FROM pagamentos p 
                JOIN clientes c ON p.cliente_id = c.id 
                WHERE p.asaas_payment_id = ?";
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([$asaasPaymentId]);
        return $stmt->fetch();
    }
}
```

---


## 9️⃣ WEBHOOK COMPLETO COM BANCO DE DADOS

### Arquivo: `webhook_asaas_completo.php`

```php
<?php

/**
 * Webhook completo do Asaas com integração ao banco de dados
 * Processa pagamentos e emite nota fiscal automaticamente
 */

require_once 'InvoiceService.php';
require_once 'database.php';

// Log de entrada
error_log("=== Webhook Asaas recebido ===");

// Ler corpo da requisição
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data) {
    error_log("Erro: JSON inválido");
    http_response_code(400);
    exit;
}

// Extrair dados
$event = $data['event'] ?? null;
$paymentData = $data['payment'] ?? null;

if (!$event || !$paymentData) {
    error_log("Erro: Dados incompletos");
    http_response_code(400);
    exit;
}

$paymentId = $paymentData['id'];
$status = $paymentData['status'];
$value = $paymentData['value'];
$description = $paymentData['description'] ?? 'Assinatura';

error_log("Event: $event | Payment: $paymentId | Status: $status");

try {
    $db = new Database();
    
    // Buscar pagamento no banco
    $pagamento = $db->buscarPagamentoPorAsaasId($paymentId);
    
    if (!$pagamento) {
        error_log("⚠️ Pagamento não encontrado no banco: $paymentId");
        http_response_code(200);
        exit;
    }
    
    // Processar apenas pagamentos confirmados
    if (in_array($event, ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED'])) {
        
        // 1. Atualizar status do pagamento
        $db->atualizarStatusPagamento($paymentId, 'pago', date('Y-m-d H:i:s'));
        error_log("✅ Status do pagamento atualizado para 'pago'");
        
        // 2. Verificar se já existe nota fiscal
        $nfExistente = $db->buscarNotaFiscalPorPagamento($pagamento['id']);
        
        if ($nfExistente) {
            error_log("ℹ️ Nota fiscal já existe para este pagamento");
            http_response_code(200);
            exit;
        }
        
        // 3. Emitir nota fiscal automaticamente
        $invoiceService = new InvoiceService();
        
        $clienteData = [
            'nome' => $pagamento['cliente_nome'],
            'email' => $pagamento['cliente_email']
        ];
        
        $result = $invoiceService->emitirNotaFiscal(
            $paymentId,
            $clienteData,
            $value,
            $description,
            true  // Enviar email
        );
        
        if ($result['success']) {
            // Salvar nota fiscal no banco
            $db->salvarNotaFiscal(
                $pagamento['id'],
                $result['invoice_id'],
                $value,
                'emitida'
            );
            
            error_log("✅ Nota fiscal emitida e salva: " . $result['invoice_id']);
            error_log("📧 Email enviado: " . ($result['email_sent'] ? 'Sim' : 'Não'));
        } else {
            error_log("❌ Erro ao emitir nota fiscal: " . $result['error']);
        }
    }
    
    // Retornar 200 OK
    http_response_code(200);
    echo json_encode(['success' => true]);
    
} catch (Exception $e) {
    error_log("❌ Erro ao processar webhook: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
```

---


## 🔟 FRONTEND - BOTÕES DE NOTA FISCAL (HTML/JavaScript)

### Arquivo: `financeiro.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financeiro - Notas Fiscais</title>
    <style>
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin: 4px;
            transition: all 0.3s;
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-indigo {
            background-color: #4f46e5;
            color: white;
        }
        .btn-indigo:hover:not(:disabled) {
            background-color: #4338ca;
        }
        .btn-teal {
            background-color: #14b8a6;
            color: white;
        }
        .btn-teal:hover:not(:disabled) {
            background-color: #0d9488;
        }
    </style>
</head>
<body>
    <h1>Gerenciar Notas Fiscais</h1>
    
    <div id="pagamentos-list">
        <!-- Lista de pagamentos será carregada aqui -->
    </div>
    
    <script>
        // Configuração da API
        const API_BASE_URL = '/api/nota-fiscal';
        
        /**
         * Baixa nota fiscal e abre em nova aba
         */
        async function baixarNotaFiscal(paymentId, btnElement) {
            try {
                btnElement.disabled = true;
                btnElement.textContent = '⏳ Baixando...';
                
                const response = await fetch(`${API_BASE_URL}/baixar/${paymentId}`);
                const data = await response.json();
                
                if (data.success && data.pdf_url) {
                    // Abrir PDF em nova aba
                    window.open(data.pdf_url, '_blank');
                } else {
                    alert(data.error || 'Nota fiscal não encontrada');
                }
            } catch (error) {
                console.error('Erro ao baixar nota fiscal:', error);
                alert('Erro ao baixar nota fiscal');
            } finally {
                btnElement.disabled = false;
                btnElement.textContent = '🧾 Baixar NF';
            }
        }
        
        /**
         * Reenvia nota fiscal por email
         */
        async function reenviarNotaFiscal(paymentId, clienteEmail, clienteNome, btnElement) {
            try {
                btnElement.disabled = true;
                btnElement.textContent = '⏳ Enviando...';
                
                const response = await fetch(`${API_BASE_URL}/reenviar/${paymentId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: clienteEmail,
                        nome: clienteNome
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(data.message || 'Nota fiscal reenviada com sucesso!');
                } else {
                    alert(data.error || 'Erro ao reenviar nota fiscal');
                }
            } catch (error) {
                console.error('Erro ao reenviar nota fiscal:', error);
                alert('Erro ao reenviar nota fiscal');
            } finally {
                btnElement.disabled = false;
                btnElement.textContent = '📧 Reenviar NF';
            }
        }
        
        /**
         * Renderiza lista de pagamentos
         */
        function renderizarPagamentos(pagamentos) {
            const container = document.getElementById('pagamentos-list');
            
            pagamentos.forEach(pagamento => {
                const div = document.createElement('div');
                div.style.border = '1px solid #ddd';
                div.style.padding = '16px';
                div.style.marginBottom = '16px';
                div.style.borderRadius = '8px';
                
                const isPago = pagamento.status === 'pago';
                
                div.innerHTML = `
                    <h3>${pagamento.cliente_nome}</h3>
                    <p>Valor: R$ ${parseFloat(pagamento.valor).toFixed(2)}</p>
                    <p>Status: <strong>${pagamento.status}</strong></p>
                    <p>Vencimento: ${pagamento.data_vencimento}</p>
                    
                    <div style="margin-top: 12px;">
                        <button 
                            class="btn btn-indigo" 
                            onclick="baixarNotaFiscal('${pagamento.asaas_payment_id}', this)"
                            ${!isPago ? 'disabled' : ''}
                            title="${!isPago ? 'Nota fiscal disponível apenas para pagamentos confirmados' : 'Baixar nota fiscal'}"
                        >
                            🧾 Baixar NF
                        </button>
                        
                        <button 
                            class="btn btn-teal" 
                            onclick="reenviarNotaFiscal('${pagamento.asaas_payment_id}', '${pagamento.cliente_email}', '${pagamento.cliente_nome}', this)"
                            ${!isPago ? 'disabled' : ''}
                            title="${!isPago ? 'Nota fiscal disponível apenas para pagamentos confirmados' : 'Reenviar nota fiscal por email'}"
                        >
                            📧 Reenviar NF
                        </button>
                    </div>
                `;
                
                container.appendChild(div);
            });
        }
        
        /**
         * Carrega pagamentos do banco
         */
        async function carregarPagamentos() {
            try {
                const response = await fetch('/api/pagamentos');
                const data = await response.json();
                
                if (data.success) {
                    renderizarPagamentos(data.pagamentos);
                }
            } catch (error) {
                console.error('Erro ao carregar pagamentos:', error);
            }
        }
        
        // Carregar pagamentos ao abrir a página
        document.addEventListener('DOMContentLoaded', carregarPagamentos);
    </script>
</body>
</html>
```

---


## 1️⃣1️⃣ FLUXO COMPLETO DE EMISSÃO

### Diagrama do Fluxo:

```
1. Cliente paga boleto/PIX
   ↓
2. Asaas detecta pagamento
   ↓
3. Asaas envia webhook para seu servidor
   ↓
4. webhook_asaas.php recebe notificação
   ↓
5. Atualiza status do pagamento no banco (status = 'pago')
   ↓
6. InvoiceService.emitirNotaFiscal() é chamado
   ↓
7. AsaasClient.createInvoice() agenda a NF
   ↓
8. AsaasClient.authorizeInvoice() emite a NF
   ↓
9. Sistema envia email ao cliente com link do PDF
   ↓
10. Nota fiscal salva no banco (tabela notas_fiscais)
```

### Código do Fluxo Completo:

```php
<?php

/**
 * Exemplo completo: Criar cobrança e processar pagamento com NF
 */

require_once 'AsaasClient.php';
require_once 'InvoiceService.php';
require_once 'database.php';

// Inicializar serviços
$asaasClient = new AsaasClient();
$invoiceService = new InvoiceService();
$db = new Database();

// PASSO 1: Criar cliente no Asaas
$customerData = [
    'name' => 'João Silva',
    'email' => 'joao@example.com',
    'cpfCnpj' => '12345678901',
    'phone' => '16999999999',
    'address' => 'Rua Exemplo',
    'addressNumber' => '123',
    'city' => 'Ribeirão Preto',
    'state' => 'SP',
    'postalCode' => '14000000'
];

$customer = $asaasClient->createCustomer($customerData);
$customerId = $customer['id'];

echo "✅ Cliente criado: $customerId\n";

// PASSO 2: Salvar cliente no banco
// (Implemente aqui)

// PASSO 3: Criar cobrança
$paymentData = [
    'customer' => $customerId,
    'billingType' => 'BOLETO',
    'value' => 99.90,
    'dueDate' => date('Y-m-d', strtotime('+7 days')),
    'description' => 'Assinatura Plano Premium - Janeiro/2026'
];

$payment = $asaasClient->createPayment($paymentData);
$paymentId = $payment['id'];
$boletoUrl = $payment['bankSlipUrl'];

echo "✅ Cobrança criada: $paymentId\n";
echo "Boleto: $boletoUrl\n";

// PASSO 4: Salvar pagamento no banco
// (Implemente aqui)

// PASSO 5: Cliente paga o boleto
// (Aguardar webhook do Asaas)

// PASSO 6: Webhook recebe notificação de pagamento confirmado
// (Ver webhook_asaas_completo.php)

// PASSO 7: Sistema emite nota fiscal automaticamente
// (Executado pelo webhook)

// PASSO 8: Cliente recebe email com nota fiscal
// (Enviado automaticamente pelo InvoiceService)

echo "\n✅ Fluxo completo configurado!\n";
echo "Aguardando pagamento para emissão automática da nota fiscal...\n";
```

---


## 1️⃣2️⃣ EXEMPLOS DE REQUISIÇÕES E RESPOSTAS DA API ASAAS

### Criar Invoice (Agendar NF)

**Request:**
```http
POST https://api.asaas.com/v3/invoices
Content-Type: application/json
access_token: sua_chave_api

{
  "payment": "pay_abc123",
  "serviceDescription": "Assinatura Plano Premium - Janeiro/2026",
  "value": 99.90,
  "effectiveDate": "2026-04-02",
  "municipalServiceId": "262124",
  "municipalServiceCode": "1401",
  "municipalServiceName": "Reparação e manutenção de computadores e de equipamentos periféricos",
  "taxes": {
    "retainIss": false,
    "iss": 2.0,
    "cofins": 0.0,
    "csll": 0.0,
    "inss": 0.0,
    "ir": 0.0,
    "pis": 0.0
  }
}
```

**Response:**
```json
{
  "id": "inv_xyz789",
  "status": "SCHEDULED",
  "payment": "pay_abc123",
  "value": 99.90,
  "effectiveDate": "2026-04-02",
  "municipalServiceId": "262124",
  "municipalServiceCode": "1401",
  "municipalServiceName": "Reparação e manutenção de computadores e de equipamentos periféricos"
}
```

### Autorizar Invoice (Emitir NF)

**Request:**
```http
POST https://api.asaas.com/v3/invoices/inv_xyz789/authorize
Content-Type: application/json
access_token: sua_chave_api

{}
```

**Response:**
```json
{
  "id": "inv_xyz789",
  "status": "AUTHORIZED",
  "pdfUrl": "https://www.asaas.com/b/pdf/kwmtvk6drnshcfum",
  "invoiceNumber": "21",
  "value": 99.90,
  "effectiveDate": "2026-04-02"
}
```

### Buscar Invoice (Obter PDF)

**Request:**
```http
GET https://api.asaas.com/v3/invoices/inv_xyz789
access_token: sua_chave_api
```

**Response:**
```json
{
  "id": "inv_xyz789",
  "status": "AUTHORIZED",
  "pdfUrl": "https://www.asaas.com/b/pdf/kwmtvk6drnshcfum",
  "invoiceNumber": "21",
  "value": 99.90,
  "effectiveDate": "2026-04-02",
  "payment": "pay_abc123",
  "serviceDescription": "Assinatura Plano Premium - Janeiro/2026"
}
```

### Listar Invoices por Payment

**Request:**
```http
GET https://api.asaas.com/v3/invoices?payment=pay_abc123
access_token: sua_chave_api
```

**Response:**
```json
{
  "data": [
    {
      "id": "inv_xyz789",
      "status": "AUTHORIZED",
      "pdfUrl": "https://www.asaas.com/b/pdf/kwmtvk6drnshcfum",
      "value": 99.90
    }
  ],
  "totalCount": 1
}
```

---


## 1️⃣3️⃣ TROUBLESHOOTING

### Erro: "Nota fiscal não encontrada"

**Causa:** Nota fiscal ainda não foi emitida ou pagamento não foi confirmado.

**Solução:**
```php
// Verificar status do pagamento
$asaasClient = new AsaasClient();
$payment = $asaasClient->getPayment($paymentId);

echo "Status do pagamento: " . $payment['status'] . "\n";

// Status deve ser: RECEIVED, CONFIRMED ou RECEIVED_IN_CASH
if (!in_array($payment['status'], ['RECEIVED', 'CONFIRMED', 'RECEIVED_IN_CASH'])) {
    echo "⚠️ Pagamento ainda não foi confirmado\n";
}
```

### Erro: "URL do PDF não disponível"

**Causa:** Nota fiscal foi emitida mas PDF ainda não foi gerado pelo Asaas.

**Solução:**
```php
// Aguardar alguns minutos e tentar novamente
sleep(60);  // Aguardar 1 minuto

$invoice = $asaasClient->getInvoice($invoiceId);
$pdfUrl = $invoice['pdfUrl'] ?? null;

if ($pdfUrl) {
    echo "✅ PDF disponível: $pdfUrl\n";
} else {
    echo "⚠️ PDF ainda não disponível, aguarde mais alguns minutos\n";
}
```

### Erro: "Código de serviço inválido"

**Causa:** Código municipal não está cadastrado no painel Asaas.

**Solução:**
1. Acessar: https://www.asaas.com/config/nfse
2. Verificar se código 14.01 (1401) está cadastrado
3. Verificar se ID do serviço é 262124
4. Atualizar variáveis de ambiente:

```bash
# No arquivo .env
ASAAS_INVOICE_SERVICE_ID=262124
ASAAS_INVOICE_SERVICE_CODE=1401
ASAAS_INVOICE_SERVICE_NAME="Reparação e manutenção de computadores e de equipamentos periféricos"
```

### Erro: "Webhook não está funcionando"

**Causa:** URL do webhook não está configurada ou não é acessível.

**Solução:**
```php
// Testar webhook localmente
// Criar arquivo: test_webhook.php

<?php

require_once 'webhook_asaas_completo.php';

// Simular dados do webhook
$webhookData = [
    'event' => 'PAYMENT_RECEIVED',
    'payment' => [
        'id' => 'pay_abc123',
        'status' => 'RECEIVED',
        'value' => 99.90,
        'description' => 'Teste',
        'customer' => 'cus_xyz789'
    ]
];

// Simular requisição
$_SERVER['REQUEST_METHOD'] = 'POST';
file_put_contents('php://input', json_encode($webhookData));

// Executar webhook
include 'webhook_asaas_completo.php';
```

### Erro: "Permissão negada na API"

**Causa:** Chave API não tem permissão para emitir notas fiscais.

**Solução:**
1. Acessar: https://www.asaas.com/config/api
2. Verificar se a chave tem permissão: `INVOICE:WRITE`
3. Se não tiver, criar nova chave com permissões corretas
4. Atualizar variável de ambiente:

```bash
ASAAS_API_KEY=nova_chave_com_permissao_invoice
```

### Debug: Verificar Logs

```php
<?php

// Habilitar logs detalhados
error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('log_errors', 1);
ini_set('error_log', '/var/log/php_errors.log');

// Adicionar logs em pontos críticos
error_log("=== Iniciando emissão de NF ===");
error_log("Payment ID: $paymentId");
error_log("Valor: $value");

// Após cada chamada da API
error_log("Resposta da API: " . json_encode($response));
```

---


## 1️⃣4️⃣ ESTRUTURA DE ARQUIVOS DO PROJETO

```
seu-projeto-php/
│
├── config/
│   └── .env                          # Variáveis de ambiente
│
├── src/
│   ├── AsaasClient.php              # Cliente da API Asaas
│   ├── InvoiceService.php           # Serviço de emissão de NF
│   └── Database.php                 # Gerenciamento do banco
│
├── api/
│   ├── nota_fiscal.php              # Endpoints de NF
│   └── pagamentos.php               # Endpoints de pagamentos
│
├── webhook/
│   └── asaas.php                    # Webhook do Asaas
│
├── public/
│   └── financeiro.html              # Interface de gerenciamento
│
└── scripts/
    ├── criar_tabelas.php            # Script para criar tabelas
    └── testar_emissao_nf.php        # Script de teste
```

---

## 1️⃣5️⃣ SCRIPT DE INSTALAÇÃO

### Arquivo: `install.php`

```php
<?php

/**
 * Script de instalação do sistema de nota fiscal
 * Execute: php install.php
 */

echo "=== Instalação do Sistema de Nota Fiscal Asaas ===\n\n";

// 1. Verificar extensões PHP necessárias
echo "1. Verificando extensões PHP...\n";

$extensoes = ['curl', 'json', 'pdo', 'pdo_mysql'];
$faltando = [];

foreach ($extensoes as $ext) {
    if (!extension_loaded($ext)) {
        $faltando[] = $ext;
        echo "   ❌ $ext - NÃO INSTALADA\n";
    } else {
        echo "   ✅ $ext\n";
    }
}

if (!empty($faltando)) {
    echo "\n⚠️ Instale as extensões faltantes:\n";
    echo "   sudo apt-get install php-" . implode(' php-', $faltando) . "\n\n";
    exit(1);
}

// 2. Verificar arquivo .env
echo "\n2. Verificando arquivo .env...\n";

if (!file_exists('.env')) {
    echo "   ⚠️ Arquivo .env não encontrado\n";
    echo "   Criando arquivo .env de exemplo...\n";
    
    $envContent = <<<ENV
# Configuração Asaas
ASAAS_API_KEY=sua_chave_api_aqui
ASAAS_SANDBOX=false

# Configuração do Serviço Municipal (Ribeirão Preto-SP)
ASAAS_INVOICE_SERVICE_ID=262124
ASAAS_INVOICE_SERVICE_CODE=1401
ASAAS_INVOICE_SERVICE_NAME="Reparação e manutenção de computadores e de equipamentos periféricos"

# Banco de Dados
DB_HOST=localhost
DB_NAME=seu_banco
DB_USER=root
DB_PASS=

# Email
DEFAULT_FROM_EMAIL=noreply@seudominio.com.br
ENV;
    
    file_put_contents('.env', $envContent);
    echo "   ✅ Arquivo .env criado\n";
    echo "   ⚠️ IMPORTANTE: Edite o arquivo .env com suas configurações reais!\n";
} else {
    echo "   ✅ Arquivo .env encontrado\n";
}

// 3. Criar tabelas no banco
echo "\n3. Criando tabelas no banco de dados...\n";

try {
    require_once 'database.php';
    $db = new Database();
    
    // Executar SQLs de criação de tabelas
    // (Implemente aqui)
    
    echo "   ✅ Tabelas criadas com sucesso\n";
} catch (Exception $e) {
    echo "   ❌ Erro ao criar tabelas: " . $e->getMessage() . "\n";
}

// 4. Testar conexão com Asaas
echo "\n4. Testando conexão com Asaas...\n";

try {
    require_once 'AsaasClient.php';
    $asaasClient = new AsaasClient();
    
    // Tentar listar clientes (teste simples)
    $response = $asaasClient->listCustomers(1, 0);
    
    echo "   ✅ Conexão com Asaas OK\n";
    echo "   Ambiente: " . ($asaasClient->sandbox ? 'SANDBOX' : 'PRODUÇÃO') . "\n";
} catch (Exception $e) {
    echo "   ❌ Erro ao conectar com Asaas: " . $e->getMessage() . "\n";
    echo "   Verifique sua chave API no arquivo .env\n";
}

echo "\n=== Instalação concluída ===\n";
echo "\nPróximos passos:\n";
echo "1. Edite o arquivo .env com suas configurações\n";
echo "2. Configure o webhook no painel Asaas\n";
echo "3. Teste a emissão de nota fiscal: php scripts/testar_emissao_nf.php\n";
```

---

## 1️⃣6️⃣ SCRIPT DE TESTE

### Arquivo: `scripts/testar_emissao_nf.php`

```php
<?php

/**
 * Script para testar emissão de nota fiscal
 * Execute: php scripts/testar_emissao_nf.php
 */

require_once __DIR__ . '/../src/AsaasClient.php';
require_once __DIR__ . '/../src/InvoiceService.php';

echo "=== Teste de Emissão de Nota Fiscal ===\n\n";

// Configurar dados de teste
$paymentId = readline("Digite o ID do pagamento (payment_id): ");
$clienteNome = readline("Digite o nome do cliente: ");
$clienteEmail = readline("Digite o email do cliente: ");
$valor = floatval(readline("Digite o valor (ex: 99.90): "));

echo "\n--- Dados do teste ---\n";
echo "Payment ID: $paymentId\n";
echo "Cliente: $clienteNome\n";
echo "Email: $clienteEmail\n";
echo "Valor: R$ " . number_format($valor, 2, ',', '.') . "\n\n";

$confirmar = readline("Confirmar emissão? (s/n): ");

if (strtolower($confirmar) !== 's') {
    echo "❌ Teste cancelado\n";
    exit;
}

// Emitir nota fiscal
try {
    $invoiceService = new InvoiceService();
    
    $result = $invoiceService->emitirNotaFiscal(
        $paymentId,
        [
            'nome' => $clienteNome,
            'email' => $clienteEmail
        ],
        $valor,
        "Teste de emissão - " . date('d/m/Y H:i:s'),
        true
    );
    
    if ($result['success']) {
        echo "\n✅ Nota fiscal emitida com sucesso!\n";
        echo "Invoice ID: " . $result['invoice_id'] . "\n";
        echo "Email enviado: " . ($result['email_sent'] ? 'Sim' : 'Não') . "\n";
        
        // Buscar URL do PDF
        $asaasClient = new AsaasClient();
        $invoice = $asaasClient->getInvoice($result['invoice_id']);
        $pdfUrl = $invoice['pdfUrl'] ?? null;
        
        if ($pdfUrl) {
            echo "PDF: $pdfUrl\n";
        }
    } else {
        echo "\n❌ Erro ao emitir nota fiscal\n";
        echo "Erro: " . $result['error'] . "\n";
    }
    
} catch (Exception $e) {
    echo "\n❌ Exceção: " . $e->getMessage() . "\n";
}
```

---


## 1️⃣7️⃣ CONFIGURAÇÃO DO SERVIDOR WEB

### Apache (.htaccess)

```apache
# Arquivo: .htaccess

RewriteEngine On

# Redirecionar API de nota fiscal
RewriteRule ^api/nota-fiscal/baixar/([0-9]+)$ api_nota_fiscal.php?action=baixar&id=$1 [L,QSA]
RewriteRule ^api/nota-fiscal/reenviar/([0-9]+)$ api_nota_fiscal.php?action=reenviar&id=$1 [L,QSA]
RewriteRule ^api/nota-fiscal/emitir$ api_nota_fiscal.php?action=emitir [L,QSA]

# Webhook
RewriteRule ^webhook/asaas$ webhook_asaas.php [L,QSA]

# Habilitar CORS
Header set Access-Control-Allow-Origin "*"
Header set Access-Control-Allow-Methods "GET, POST, OPTIONS"
Header set Access-Control-Allow-Headers "Content-Type, Authorization"
```

### Nginx (nginx.conf)

```nginx
server {
    listen 80;
    server_name seudominio.com.br;
    root /var/www/html;
    index index.php index.html;

    # API de nota fiscal
    location ~ ^/api/nota-fiscal/baixar/([0-9]+)$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root/api_nota_fiscal.php;
        fastcgi_param QUERY_STRING action=baixar&id=$1;
        include fastcgi_params;
    }

    location ~ ^/api/nota-fiscal/reenviar/([0-9]+)$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root/api_nota_fiscal.php;
        fastcgi_param QUERY_STRING action=reenviar&id=$1;
        include fastcgi_params;
    }

    location /api/nota-fiscal/emitir {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root/api_nota_fiscal.php;
        fastcgi_param QUERY_STRING action=emitir;
        include fastcgi_params;
    }

    # Webhook
    location /webhook/asaas {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root/webhook_asaas.php;
        include fastcgi_params;
    }

    # PHP
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    # CORS
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
}
```

---

## 1️⃣8️⃣ CHECKLIST DE CONFIGURAÇÃO

### Configuração Inicial:
- [ ] PHP 7.4+ instalado
- [ ] Extensões PHP: curl, json, pdo, pdo_mysql
- [ ] Banco de dados MySQL/MariaDB configurado
- [ ] Arquivo .env criado e configurado
- [ ] Variáveis ASAAS_* configuradas

### Configuração Asaas:
- [ ] Conta Asaas criada
- [ ] Chave API gerada com permissão INVOICE:WRITE
- [ ] Código de serviço cadastrado no painel (14.01)
- [ ] ID do serviço configurado (262124)
- [ ] Alíquota ISS configurada (2%)
- [ ] Webhook configurado no painel

### Código:
- [ ] AsaasClient.php criado
- [ ] InvoiceService.php criado
- [ ] Database.php criado
- [ ] api_nota_fiscal.php criado
- [ ] webhook_asaas.php criado
- [ ] Tabelas do banco criadas

### Testes:
- [ ] Teste de conexão com Asaas OK
- [ ] Teste de criação de cliente OK
- [ ] Teste de criação de cobrança OK
- [ ] Teste de emissão de NF OK
- [ ] Teste de webhook OK
- [ ] Teste de envio de email OK

### Produção:
- [ ] SSL/HTTPS configurado
- [ ] Webhook acessível publicamente
- [ ] Logs configurados
- [ ] Backup do banco configurado
- [ ] Monitoramento ativo

---

## 1️⃣9️⃣ COMANDOS ÚTEIS

### Testar conexão com Asaas:
```bash
php -r "require 'AsaasClient.php'; \$c = new AsaasClient(); var_dump(\$c->listCustomers(1, 0));"
```

### Criar tabelas do banco:
```bash
php scripts/criar_tabelas.php
```

### Testar emissão de NF:
```bash
php scripts/testar_emissao_nf.php
```

### Ver logs do PHP:
```bash
tail -f /var/log/php_errors.log
```

### Testar webhook localmente:
```bash
curl -X POST http://localhost/webhook/asaas \
  -H "Content-Type: application/json" \
  -d '{
    "event": "PAYMENT_RECEIVED",
    "payment": {
      "id": "pay_test123",
      "status": "RECEIVED",
      "value": 99.90
    }
  }'
```

---

## 2️⃣0️⃣ RECURSOS ADICIONAIS

### Documentação Oficial Asaas:
- API Geral: https://docs.asaas.com/reference/comecar
- Notas Fiscais: https://docs.asaas.com/reference/criar-nota-fiscal
- Webhooks: https://docs.asaas.com/reference/webhooks

### Suporte:
- Email: suporte@asaas.com
- Telefone: (16) 3515-2020
- Chat: https://www.asaas.com

### Painel Asaas:
- Produção: https://www.asaas.com
- Sandbox: https://sandbox.asaas.com

---

**Documento gerado em:** 02/04/2026  
**Versão:** 1.0  
**Linguagem:** PHP 7.4+  
**Autor:** LWK Sistemas

---

## 📝 NOTAS IMPORTANTES

1. **Segurança:**
   - NUNCA exponha sua chave API publicamente
   - Use HTTPS em produção
   - Valide todos os dados de entrada
   - Proteja o endpoint do webhook

2. **Performance:**
   - Use cache para configurações municipais
   - Implemente fila para processamento de webhooks
   - Configure timeout adequado nas requisições cURL

3. **Manutenção:**
   - Monitore logs regularmente
   - Faça backup do banco de dados
   - Mantenha a documentação atualizada
   - Teste em sandbox antes de produção

4. **Compliance:**
   - Guarde notas fiscais por 5 anos (legislação)
   - Mantenha registro de todas as emissões
   - Implemente auditoria de acessos
   - Siga LGPD para dados de clientes
