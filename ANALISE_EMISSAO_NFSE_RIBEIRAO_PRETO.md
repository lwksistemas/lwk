# Análise: Emissão de NFS-e Direta - Ribeirão Preto

## Situação Atual

O sistema LWK atualmente emite notas fiscais através do Asaas, que atua como intermediário:
- **Arquivo**: `backend/asaas_integration/invoice_service.py`
- **Fluxo**: Sistema → Asaas API → Prefeitura de Ribeirão Preto
- **Limitação**: Dependência do Asaas para emissão de NF

## Objetivo

Implementar emissão direta de NFS-e pela API da Prefeitura de Ribeirão Preto, sem intermediários.

## Pesquisa Realizada

### Sistema ISSNet - Ribeirão Preto

Ribeirão Preto utiliza o sistema **ISSNet** para emissão de NFS-e:

1. **Repositório encontrado**: 
   - https://github.com/Focus599Dev/sped-nfse-issnet
   - API de comunicação com webservice ISSNet específico para Ribeirão Preto

2. **Características do ISSNet**:
   - Webservice SOAP (WSDL)
   - Padrão municipal próprio (não é ABRASF)
   - Requer certificado digital A1 ou A3
   - Autenticação via usuário/senha + certificado

### API Nacional NFS-e (Alternativa)

Desde 2023, existe a **API Nacional NFS-e** (nfse.gov.br):
- Padrão unificado para todo Brasil
- Obrigatório para MEI desde 01/09/2023
- Gradualmente sendo adotado por municípios
- Ribeirão Preto ainda não migrou completamente

## Requisitos para Implementação Direta

### 1. Certificado Digital

- **Obrigatório**: Certificado A1 (arquivo .pfx) ou A3 (token/cartão)
- **Tipo**: e-CNPJ da empresa LWK Sistemas
- **Custo**: R$ 200-400/ano (A1) ou R$ 400-600/ano (A3)
- **Validade**: 1 ano (A1) ou 3 anos (A3)

### 2. Credenciamento na Prefeitura

- Cadastro no portal da Prefeitura de Ribeirão Preto
- Solicitação de acesso ao webservice
- Configuração de usuário e senha
- Homologação do sistema

### 3. Infraestrutura Técnica

- Biblioteca para comunicação SOAP/XML
- Parser XML para requisições/respostas
- Validação de schema XSD
- Armazenamento seguro do certificado
- Logs de auditoria

## Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────┐
│                    LWK Sistema (Django)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Módulo NFS-e (novo)                                  │  │
│  │  - backend/nfse_integration/                          │  │
│  │    ├── client.py (SOAP client)                        │  │
│  │    ├── models.py (Config, NFSe, Lote)                │  │
│  │    ├── service.py (Lógica de negócio)                │  │
│  │    └── xml_builder.py (Construção XML)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Configurações por Loja                               │  │
│  │  - Provedor NF: Asaas | ISSNet | Nacional            │  │
│  │  - Certificado Digital (upload seguro)                │  │
│  │  - Credenciais webservice                             │  │
│  │  - Código de serviço municipal                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌───────────────────┐              ┌──────────────────────┐
│   Asaas API       │              │  ISSNet Webservice   │
│   (atual)         │              │  (Ribeirão Preto)    │
└───────────────────┘              └──────────────────────┘
```

## Implementação Sugerida

### Fase 1: Configuração por Loja (Prioritário)

Adicionar em **Configurações da Loja** (CRM Vendas):

```python
# backend/crm_vendas/models.py

class ConfiguracaoLoja(models.Model):
    # ... campos existentes ...
    
    # Emissão de NFS-e
    PROVEDOR_NF_CHOICES = [
        ('asaas', 'Asaas (Intermediário)'),
        ('issnet', 'ISSNet - Ribeirão Preto (Direto)'),
        ('nacional', 'API Nacional NFS-e (Direto)'),
    ]
    
    provedor_nf = models.CharField(
        max_length=20,
        choices=PROVEDOR_NF_CHOICES,
        default='asaas',
        verbose_name='Provedor de Nota Fiscal'
    )
    
    # Configurações ISSNet
    issnet_usuario = models.CharField(max_length=100, blank=True)
    issnet_senha = models.CharField(max_length=100, blank=True)
    issnet_certificado = models.FileField(
        upload_to='certificados/',
        blank=True,
        null=True,
        help_text='Certificado Digital A1 (.pfx)'
    )
    issnet_senha_certificado = models.CharField(max_length=100, blank=True)
    
    # Código de serviço municipal
    codigo_servico_municipal = models.CharField(
        max_length=10,
        default='1401',
        help_text='Código do serviço na lista municipal'
    )
    descricao_servico = models.TextField(
        default='Desenvolvimento e licenciamento de software',
        help_text='Descrição do serviço prestado'
    )
```

### Fase 2: Cliente ISSNet (Biblioteca Python)

```python
# backend/nfse_integration/issnet_client.py

from zeep import Client
from zeep.wsse.signature import Signature
from cryptography.hazmat.primitives.serialization import pkcs12
import xml.etree.ElementTree as ET

class ISSNetClient:
    """Cliente para webservice ISSNet de Ribeirão Preto"""
    
    def __init__(self, usuario, senha, certificado_path, senha_cert):
        self.usuario = usuario
        self.senha = senha
        self.wsdl_url = 'https://issdigital.ribeirao preto.sp.gov.br/WsNFe2/LoteRps.jws?wsdl'
        
        # Carregar certificado
        with open(certificado_path, 'rb') as f:
            pfx_data = f.read()
        
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data,
            senha_cert.encode()
        )
        
        # Configurar cliente SOAP com certificado
        self.client = Client(
            self.wsdl_url,
            wsse=Signature(private_key, certificate)
        )
    
    def enviar_lote_rps(self, xml_lote):
        """Envia lote de RPS para processamento"""
        response = self.client.service.RecepcionarLoteRps(
            xml_lote,
            self.usuario,
            self.senha
        )
        return response
    
    def consultar_nfse(self, numero_nf):
        """Consulta NFS-e emitida"""
        response = self.client.service.ConsultarNfsePorRps(
            numero_nf,
            self.usuario,
            self.senha
        )
        return response
    
    def cancelar_nfse(self, numero_nf, motivo):
        """Cancela NFS-e"""
        response = self.client.service.CancelarNfse(
            numero_nf,
            motivo,
            self.usuario,
            self.senha
        )
        return response
```

### Fase 3: Serviço de Emissão

```python
# backend/nfse_integration/service.py

def emitir_nfse_loja(loja, valor, descricao):
    """
    Emite NFS-e baseado na configuração da loja
    """
    config = loja.configuracao
    
    if config.provedor_nf == 'asaas':
        # Usar serviço atual
        from asaas_integration.invoice_service import emitir_nf_para_pagamento
        return emitir_nf_para_pagamento(...)
    
    elif config.provedor_nf == 'issnet':
        # Usar ISSNet direto
        client = ISSNetClient(
            usuario=config.issnet_usuario,
            senha=config.issnet_senha,
            certificado_path=config.issnet_certificado.path,
            senha_cert=config.issnet_senha_certificado
        )
        
        # Construir XML RPS
        xml_rps = construir_xml_rps(loja, valor, descricao)
        
        # Enviar para prefeitura
        response = client.enviar_lote_rps(xml_rps)
        
        return {
            'success': True,
            'numero_nf': response.numero,
            'codigo_verificacao': response.codigo_verificacao
        }
```

## Vantagens da Implementação Direta

1. **Independência**: Não depende do Asaas
2. **Custo**: Sem taxa por nota emitida
3. **Controle**: Total controle sobre o processo
4. **Flexibilidade**: Pode emitir NF para qualquer operação da loja

## Desvantagens

1. **Complexidade**: Maior complexidade técnica
2. **Manutenção**: Precisa acompanhar mudanças na API municipal
3. **Certificado**: Custo e renovação anual do certificado
4. **Homologação**: Processo de credenciamento na prefeitura

## Recomendação

### Curto Prazo (Imediato)

1. **Adicionar configuração por loja** para escolher provedor de NF
2. **Manter Asaas como padrão** para lojas existentes
3. **Permitir que lojas escolham** emitir direto se tiverem certificado

### Médio Prazo (1-3 meses)

1. **Implementar cliente ISSNet** para Ribeirão Preto
2. **Criar interface de configuração** no painel da loja
3. **Testar em ambiente de homologação**

### Longo Prazo (3-6 meses)

1. **Suportar API Nacional NFS-e** (padrão futuro)
2. **Adicionar suporte para outros municípios**
3. **Dashboard de notas fiscais** emitidas

## Próximos Passos

1. ✅ Adicionar campo de configuração no modelo da loja
2. ✅ Criar interface em Configurações para escolher provedor
3. ⏳ Obter credenciais de teste do ISSNet Ribeirão Preto
4. ⏳ Implementar cliente SOAP básico
5. ⏳ Testar emissão em ambiente de homologação

## Bibliotecas Python Necessárias

```txt
zeep==4.2.1  # Cliente SOAP/WSDL
lxml==5.1.0  # Parser XML
cryptography==42.0.0  # Manipulação de certificados
signxml==3.2.2  # Assinatura digital XML
```

## Referências

- [Repositório sped-nfse-issnet](https://github.com/Focus599Dev/sped-nfse-issnet)
- [API Nacional NFS-e](https://www.nfse.gov.br/)
- [Documentação Certificado Digital](https://www.gov.br/iti/pt-br/assuntos/certificado-digital)
