# Fase 3: Cliente ISSNet - Implementação Completa

## Data: 09/04/2026
## Status: ✅ Implementado (Aguardando Deploy e Testes)

## Resumo

Implementada a Fase 3 completa: Cliente ISSNet para emissão direta de NFS-e na Prefeitura de Ribeirão Preto, incluindo serviço unificado e modelo de dados.

## Arquivos Criados

### 1. Módulo nfse_integration/
```
backend/nfse_integration/
├── __init__.py                    # Inicialização do módulo
├── apps.py                        # Configuração do app Django
├── models.py                      # Modelo NFSe para armazenar notas emitidas
├── issnet_client.py               # Cliente SOAP para ISSNet
├── service.py                     # Serviço unificado (escolhe provedor)
├── requirements.txt               # Dependências necessárias
└── migrations/
    ├── __init__.py
    └── 0001_initial.py            # Migration do modelo NFSe
```

## 1. Cliente ISSNet (`issnet_client.py`)

### Funcionalidades
- ✅ Conexão com webservice SOAP ISSNet
- ✅ Carregamento de certificado digital A1 (.pfx)
- ✅ Construção de XML RPS no padrão Ribeirão Preto
- ✅ Assinatura digital de XML com certificado
- ✅ Envio de lote RPS para prefeitura
- ✅ Consulta de NFS-e emitida
- ✅ Cancelamento de NFS-e

### Métodos Principais

#### `__init__()`
```python
ISSNetClient(
    usuario='usuario_issnet',
    senha='senha_issnet',
    certificado_path='/path/to/cert.pfx',
    senha_certificado='senha_cert',
    ambiente='producao'  # ou 'homologacao'
)
```

#### `emitir_nfse()`
```python
resultado = client.emitir_nfse(
    prestador_cnpj='12345678000190',
    prestador_inscricao_municipal='123456',
    prestador_razao_social='Minha Loja LTDA',
    tomador_cpf_cnpj='12345678901',
    tomador_nome='João Silva',
    tomador_endereco={
        'logradouro': 'Rua Exemplo',
        'numero': '123',
        'bairro': 'Centro',
        'cidade': 'Ribeirão Preto',
        'uf': 'SP',
        'cep': '14000000'
    },
    servico_codigo='1401',
    servico_descricao='Desenvolvimento de software',
    valor_servicos=Decimal('150.00'),
    aliquota_iss=Decimal('2.00'),
    numero_rps=1,
)

# Retorna:
{
    'success': True,
    'numero_nf': '12345',
    'codigo_verificacao': 'ABC123',
    'data_emissao': datetime(...),
    'xml_nfse': '<xml>...</xml>'
}
```

#### `consultar_nfse()`
```python
resultado = client.consultar_nfse('12345')
```

#### `cancelar_nfse()`
```python
resultado = client.cancelar_nfse('12345', 'Erro na emissão')
```

### Construção de XML RPS

O método `_construir_xml_rps()` gera XML no padrão ISSNet com:
- Identificação do RPS (número, série, tipo)
- Data de emissão
- Natureza da operação
- Regime especial de tributação
- Optante pelo Simples Nacional
- Dados do prestador (CNPJ, inscrição municipal)
- Dados do tomador (CPF/CNPJ, nome, endereço)
- Dados do serviço (código, descrição, valores)
- Cálculo automático de ISS

### Assinatura Digital

O método `_assinar_xml()` assina o XML usando:
- Biblioteca `signxml`
- Certificado digital A1 (.pfx)
- Algoritmo RSA-SHA1
- Método enveloped

## 2. Serviço Unificado (`service.py`)

### Classe NFSeService

Serviço que escolhe o provedor baseado na configuração da loja (`CRMConfig`).

#### Inicialização
```python
from nfse_integration.service import NFSeService

service = NFSeService(loja)
```

#### Emissão de NFS-e
```python
resultado = service.emitir_nfse(
    tomador_cpf_cnpj='12345678901',
    tomador_nome='João Silva',
    tomador_email='joao@example.com',
    tomador_endereco={...},
    servico_descricao='Desenvolvimento de software',
    valor_servicos=Decimal('150.00'),
    enviar_email=True,
)
```

### Fluxo de Emissão

```
1. NFSeService.emitir_nfse()
   ↓
2. Verifica config.provedor_nf
   ↓
3. Se 'issnet':
   - Valida configurações (usuário, senha, certificado)
   - Gera número RPS automático
   - Cria ISSNetClient
   - Emite NFS-e
   - Salva no banco (modelo NFSe)
   - Envia email para tomador
   ↓
4. Retorna resultado
```

### Provedores Suportados

| Provedor | Status | Método |
|----------|--------|--------|
| Asaas | ⏳ Não implementado | `_emitir_via_asaas()` |
| ISSNet | ✅ Implementado | `_emitir_via_issnet()` |
| API Nacional | ⏳ Não implementado | - |
| Manual | ✅ Implementado | Retorna erro orientando emissão manual |

## 3. Modelo NFSe (`models.py`)

### Campos Principais

```python
class NFSe(LojaIsolationMixin, models.Model):
    # Identificação
    numero_nf = CharField(max_length=50)           # Número da NFS-e
    numero_rps = IntegerField(default=0)           # Número do RPS
    codigo_verificacao = CharField(max_length=50)  # Código de verificação
    
    # Datas
    data_emissao = DateTimeField()
    data_cancelamento = DateTimeField(null=True)
    
    # Valores
    valor = DecimalField(max_digits=10, decimal_places=2)
    valor_iss = DecimalField(max_digits=10, decimal_places=2)
    aliquota_iss = DecimalField(max_digits=5, decimal_places=2)
    
    # Tomador
    tomador_cpf_cnpj = CharField(max_length=18)
    tomador_nome = CharField(max_length=200)
    tomador_email = EmailField()
    
    # Serviço
    servico_codigo = CharField(max_length=10)
    servico_descricao = TextField()
    
    # Provedor e Status
    provedor = CharField(choices=[...])
    status = CharField(choices=[...])
    
    # XMLs
    xml_rps = TextField()
    xml_nfse = TextField()
    
    # URLs
    pdf_url = URLField()
    xml_url = URLField()
```

### Métodos

- `get_valor_liquido()`: Retorna valor - ISS
- `is_cancelada()`: Verifica se está cancelada
- `pode_cancelar()`: Verifica se pode ser cancelada

### Índices

- `loja_id + data_emissao` (DESC)
- `numero_nf`
- `numero_rps`
- `status`
- `tomador_cpf_cnpj`

### Unique Together

- `(loja_id, numero_nf)` - Garante que número de NF é único por loja

## 4. Dependências (`requirements.txt`)

```txt
zeep==4.2.1          # Cliente SOAP
lxml==5.1.0          # Manipulação de XML
signxml==3.2.2       # Assinatura digital de XML
cryptography==42.0.0 # Manipulação de certificados
```

## 5. Configuração Django

### settings.py
```python
INSTALLED_APPS = [
    # ... apps existentes ...
    'nfse_integration',  # ✅ Adicionado
]
```

## Exemplo de Uso Completo

### 1. Configurar Loja (via Interface)
```
URL: /loja/{slug}/crm-vendas/configuracoes/nota-fiscal

- Escolher provedor: ISSNet
- Preencher usuário ISSNet
- Preencher senha ISSNet
- Upload certificado .pfx
- Preencher senha do certificado
- Configurar código serviço: 1401
- Configurar alíquota ISS: 2.00%
- Salvar
```

### 2. Emitir NFS-e (via Código)
```python
from nfse_integration.service import NFSeService
from superadmin.models import Loja
from decimal import Decimal

# Obter loja
loja = Loja.objects.get(slug='minha-loja')

# Criar serviço
service = NFSeService(loja)

# Emitir NFS-e
resultado = service.emitir_nfse(
    tomador_cpf_cnpj='123.456.789-01',
    tomador_nome='João Silva',
    tomador_email='joao@example.com',
    tomador_endereco={
        'logradouro': 'Rua Exemplo',
        'numero': '123',
        'bairro': 'Centro',
        'cidade': 'Ribeirão Preto',
        'uf': 'SP',
        'cep': '14000-000'
    },
    servico_descricao='Desenvolvimento de sistema web',
    valor_servicos=Decimal('1500.00'),
    enviar_email=True,
)

if resultado['success']:
    print(f"NFS-e emitida: {resultado['numero_nf']}")
    print(f"Código verificação: {resultado['codigo_verificacao']}")
else:
    print(f"Erro: {resultado['error']}")
```

### 3. Consultar NFS-e
```python
resultado = service.consultar_nfse('12345')
```

### 4. Cancelar NFS-e
```python
resultado = service.cancelar_nfse('12345', 'Erro na emissão')
```

## Segurança

### Certificados
- ✅ Armazenados em `media/certificados_nfse/{ano}/{mes}/`
- ✅ Isolados por loja
- ✅ Senhas armazenadas de forma segura

### Validações
- ✅ Validação de configuração antes de emitir
- ✅ Validação de campos obrigatórios
- ✅ Tratamento de erros robusto
- ✅ Logs detalhados

## Próximos Passos

### Deploy e Testes
1. ⏳ Instalar dependências no Heroku
2. ⏳ Aplicar migration em produção
3. ⏳ Testar em ambiente de homologação ISSNet
4. ⏳ Obter credenciais de teste da prefeitura
5. ⏳ Emitir NFS-e de teste

### Melhorias Futuras
1. ⏳ Implementar emissão via Asaas para lojas
2. ⏳ Implementar API Nacional NFS-e
3. ⏳ Dashboard de notas emitidas
4. ⏳ Relatórios de faturamento
5. ⏳ Integração com contabilidade
6. ⏳ Envio automático de NF por email
7. ⏳ Geração de PDF da NF
8. ⏳ Alerta de vencimento de certificado

### Fase 4: Integração com CRM
1. ⏳ Botão "Emitir NF" em oportunidades fechadas
2. ⏳ Emissão automática ao fechar venda
3. ⏳ Histórico de NFs por cliente
4. ⏳ Dashboard de faturamento

## Arquitetura Final

```
┌─────────────────────────────────────────────────────────┐
│                    LWK Sistema                           │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  CRM Vendas                                         │ │
│  │  - Oportunidade fechada                             │ │
│  │  - Botão "Emitir NF"                                │ │
│  └────────────────┬───────────────────────────────────┘ │
│                   ↓                                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │  NFSeService                                        │ │
│  │  - Escolhe provedor (config da loja)               │ │
│  │  - Valida configurações                             │ │
│  │  - Gera número RPS                                  │ │
│  └────────────────┬───────────────────────────────────┘ │
│                   ↓                                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │  ISSNetClient                                       │ │
│  │  - Constrói XML RPS                                 │ │
│  │  - Assina com certificado da loja                   │ │
│  │  - Envia para webservice                            │ │
│  └────────────────┬───────────────────────────────────┘ │
│                   ↓                                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Modelo NFSe                                        │ │
│  │  - Salva NF emitida                                 │ │
│  │  - Histórico por loja                               │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
└─────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌───────────────────┐              ┌──────────────────────┐
│  ISSNet Webservice│              │  Email para Cliente  │
│  (Prefeitura RP)  │              │  com NF emitida      │
└───────────────────┘              └──────────────────────┘
```

## Documentação Relacionada

- [Separação de Emissão NFS-e](./SEPARACAO_EMISSAO_NFSE.md)
- [Implementação Interface NFS-e](./IMPLEMENTACAO_INTERFACE_NFSE.md)
- [Análise Emissão NFS-e Ribeirão Preto](./ANALISE_EMISSAO_NFSE_RIBEIRAO_PRETO.md)

---

**Implementado por**: Kiro AI Assistant  
**Data**: 09/04/2026  
**Status**: ✅ Fase 3 Concluída - Aguardando Deploy e Testes
