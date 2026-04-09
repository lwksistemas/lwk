# Configuração de NFS-e por Loja

## Implementação Fase 1 - Concluída ✅

Adicionada configuração de provedor de NFS-e nas configurações do CRM de cada loja.

## Arquivos Modificados

1. **backend/crm_vendas/models_config.py**
   - Adicionados campos de configuração de NFS-e
   - 9 novos campos no modelo `CRMConfig`

2. **backend/crm_vendas/serializers.py**
   - Atualizado `CRMConfigSerializer` para incluir novos campos
   - Senhas marcadas como `write_only` para segurança

3. **backend/crm_vendas/migrations/0044_add_nfse_config.py**
   - Migration criada para adicionar os campos no banco

## Novos Campos Disponíveis

### Provedor de NF
```python
provedor_nf = CharField(choices=[
    ('asaas', 'Asaas (Intermediário - Padrão)'),
    ('issnet', 'ISSNet - Ribeirão Preto (Direto)'),
    ('nacional', 'API Nacional NFS-e (Direto)'),
    ('manual', 'Emissão Manual (Sem integração)'),
])
```

### Configurações ISSNet (Ribeirão Preto)
- `issnet_usuario`: Usuário do webservice
- `issnet_senha`: Senha do webservice (write_only)
- `issnet_certificado`: Upload do certificado .pfx
- `issnet_senha_certificado`: Senha do certificado (write_only)

### Configurações Gerais
- `codigo_servico_municipal`: Código do serviço (ex: 1401)
- `descricao_servico_padrao`: Descrição padrão para NF
- `aliquota_iss`: Alíquota do ISS (%)
- `emitir_nf_automaticamente`: Boolean para emissão automática

## Como Usar

### 1. Aplicar Migration

```bash
# Localmente
python backend/manage.py makemigrations
python backend/manage.py migrate

# Produção (Heroku)
git add -A
git commit -m "feat: adicionar configuração de NFS-e por loja"
git push heroku master
```

### 2. Acessar Configurações da Loja

```
URL: https://lwksistemas.com.br/loja/{cnpj}/crm-vendas/configuracoes
```

### 3. API Endpoints

#### GET - Obter configurações
```http
GET /api/crm-vendas/config/
Authorization: Bearer {token}
```

Resposta:
```json
{
  "id": 1,
  "provedor_nf": "asaas",
  "provedor_nf_display": "Asaas (Intermediário - Padrão)",
  "codigo_servico_municipal": "1401",
  "descricao_servico_padrao": "Desenvolvimento e licenciamento de software sob demanda",
  "aliquota_iss": "2.00",
  "emitir_nf_automaticamente": true,
  "issnet_usuario": "",
  "issnet_certificado": null,
  ...
}
```

#### PUT/PATCH - Atualizar configurações
```http
PATCH /api/crm-vendas/config/
Authorization: Bearer {token}
Content-Type: application/json

{
  "provedor_nf": "issnet",
  "issnet_usuario": "usuario_teste",
  "issnet_senha": "senha_secreta",
  "codigo_servico_municipal": "1401",
  "aliquota_iss": "2.50"
}
```

#### POST - Upload de Certificado
```http
POST /api/crm-vendas/config/
Authorization: Bearer {token}
Content-Type: multipart/form-data

issnet_certificado: [arquivo.pfx]
issnet_senha_certificado: senha_do_certificado
```

## Próximos Passos

### Fase 2: Interface Frontend
- [ ] Criar componente de configuração de NFS-e
- [ ] Formulário para escolher provedor
- [ ] Upload de certificado digital
- [ ] Validação de campos obrigatórios por provedor

### Fase 3: Implementação ISSNet
- [ ] Criar módulo `backend/nfse_integration/`
- [ ] Cliente SOAP para ISSNet
- [ ] Construtor de XML RPS
- [ ] Assinatura digital com certificado

### Fase 4: Serviço Unificado
- [ ] Criar `NFSeService` que escolhe provedor
- [ ] Integrar com fluxo de pagamento
- [ ] Dashboard de notas emitidas
- [ ] Logs e auditoria

## Exemplo de Uso Futuro

```python
from nfse_integration.service import NFSeService

# Emitir NF baseado na configuração da loja
service = NFSeService(loja)
result = service.emitir_nfse(
    valor=150.00,
    descricao="Desenvolvimento de sistema",
    cliente_cpf_cnpj="12345678901",
    cliente_nome="João Silva"
)

if result['success']:
    print(f"NF emitida: {result['numero_nf']}")
    print(f"Código verificação: {result['codigo_verificacao']}")
else:
    print(f"Erro: {result['error']}")
```

## Segurança

- ✅ Senhas armazenadas como `write_only` no serializer
- ✅ Certificados armazenados em pasta protegida
- ⚠️ Considerar criptografia para senhas no banco (próxima fase)
- ⚠️ Implementar rotação de certificados (alerta de vencimento)

## Testes

```python
# Testar configuração padrão
from crm_vendas.models import CRMConfig

config = CRMConfig.get_or_create_for_loja(loja_id=1)
assert config.provedor_nf == 'asaas'
assert config.emitir_nf_automaticamente == True

# Testar mudança de provedor
config.provedor_nf = 'issnet'
config.issnet_usuario = 'teste'
config.save()
```

## Documentação Adicional

- [Análise Completa](./ANALISE_EMISSAO_NFSE_RIBEIRAO_PRETO.md)
- [Repositório ISSNet](https://github.com/Focus599Dev/sped-nfse-issnet)
- [API Nacional NFS-e](https://www.nfse.gov.br/)
