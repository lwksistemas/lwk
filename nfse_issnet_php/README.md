# NFS-e ISSNet — Código PHP (ABRASF 2.04)

## Requisitos

- PHP 8.1+
- Extensões: `openssl`, `curl`, `dom`
- Dependência: `composer require robrichards/xmlseclibs`
- Certificado digital A1 (.pfx)

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `ISSNetClient.php` | Classe principal com todas as operações |
| `exemplo_uso.php` | Exemplos de emissão, cancelamento, consulta URL e reenvio |

## Operações

### 1. Emissão (`emitirNfse`)
- Monta XML `EnviarLoteRpsEnvio` (ABRASF 2.04)
- Dupla assinatura RSA-SHA1 (Rps + raiz)
- Envia via SOAP + mTLS
- Fallback: `RecepcionarLoteRpsSincrono` se Fault genérico

### 2. Cancelamento (`cancelarNfse`)
- Monta XML `CancelarNfseEnvio` com `Pedido Id="Pedido1"`
- Assinatura no elemento Pedido
- Códigos: 1=Erro emissão, 2=Não prestado, 3=Erro assinatura, 4=Duplicidade

### 3. Consulta URL DANFE (`consultarUrlNfse`)
- Monta XML `ConsultarUrlNfseEnvio`
- Assinatura enveloped na raiz (URI vazia)
- Retorna URL do portal da prefeitura (PDF real)

### 4. Reenvio por Email
- Usa a URL obtida em `consultarUrlNfse`
- Envia email com link da DANFE + XML anexado

## Instalação

```bash
composer require robrichards/xmlseclibs
```

## Configuração

```php
$client = new ISSNetClient(
    usuario: 'SEU_USUARIO',
    senha: 'SUA_SENHA',
    certificadoPath: '/caminho/certificado.pfx',
    senhaCertificado: 'SENHA_PFX',
    ambiente: 'producao'
);
```
