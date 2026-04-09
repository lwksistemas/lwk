# Implementação Interface de Configuração NFS-e - Fase 2

## Data: 09/04/2026
## Deploy: Heroku v1542 | Vercel (automático via GitHub)

## Resumo

Implementada a interface frontend completa para configuração de emissão de NFS-e por loja, permitindo que cada loja escolha como deseja emitir suas notas fiscais.

## Arquivos Modificados

### 1. Frontend Context
**Arquivo**: `frontend/contexts/CRMConfigContext.tsx`

Adicionados campos de NFS-e na interface `CRMConfig`:
```typescript
interface CRMConfig {
  // ... campos existentes ...
  
  // Configurações de NFS-e
  provedor_nf: 'asaas' | 'issnet' | 'nacional' | 'manual';
  provedor_nf_display?: string;
  issnet_usuario: string;
  issnet_senha?: string;
  issnet_certificado: string | null;
  issnet_senha_certificado?: string;
  codigo_servico_municipal: string;
  descricao_servico_padrao: string;
  aliquota_iss: string;
  emitir_nf_automaticamente: boolean;
}
```

### 2. Página de Configuração de NFS-e
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/nota-fiscal/page.tsx`

Nova página completa com:

#### Seção 1: Escolha do Provedor
- **Asaas (Padrão)**: Emissão através do intermediário Asaas
- **ISSNet - Ribeirão Preto**: Emissão direta na prefeitura
- **API Nacional NFS-e**: Em breve (desabilitado)
- **Manual**: Sem integração automática

#### Seção 2: Credenciais ISSNet (condicional)
Aparece apenas quando provedor = 'issnet':
- Campo: Usuário ISSNet
- Campo: Senha ISSNet (write-only)
- Upload: Certificado Digital A1 (.pfx)
- Campo: Senha do Certificado (write-only)
- Info box com requisitos

#### Seção 3: Configurações Gerais
- Código do Serviço Municipal (ex: 1401)
- Alíquota ISS (%)
- Descrição Padrão do Serviço (textarea)
- Checkbox: Emitir NF automaticamente

#### Funcionalidades
- ✅ Validação de arquivo .pfx
- ✅ Upload multipart/form-data
- ✅ Mensagens de sucesso/erro
- ✅ Campos condicionais por provedor
- ✅ Senhas não são exibidas após salvar
- ✅ Design responsivo (mobile-first)
- ✅ Dark mode completo

### 3. Página Principal de Configurações
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/page.tsx`

Adicionado novo card:
```typescript
{
  titulo: 'Nota Fiscal (NFS-e)',
  descricao: 'Configure como as notas fiscais serão emitidas',
  href: `${base}/nota-fiscal`,
  icon: FileText,
  itens: ['Provedor de NF', 'Certificado digital', 'Emissão automática'],
}
```

## Fluxo de Uso

### 1. Acessar Configurações
```
URL: https://lwksistemas.com.br/loja/{cnpj}/crm-vendas/configuracoes
```

### 2. Clicar em "Nota Fiscal (NFS-e)"

### 3. Escolher Provedor
- **Asaas**: Nenhuma configuração adicional necessária
- **ISSNet**: Preencher credenciais e fazer upload do certificado
- **Manual**: Nenhuma configuração adicional necessária

### 4. Configurar Dados Gerais
- Código do serviço (padrão: 1401)
- Alíquota ISS (padrão: 2.00%)
- Descrição do serviço
- Emissão automática (padrão: ativado)

### 5. Salvar
- Dados enviados via PATCH `/api/crm-vendas/config/`
- Certificado enviado via multipart/form-data
- Senhas armazenadas de forma segura (write-only)

## API Endpoints Utilizados

### GET - Carregar Configurações
```http
GET /api/crm-vendas/config/
Authorization: Bearer {token}
```

### PATCH - Salvar Configurações
```http
PATCH /api/crm-vendas/config/
Authorization: Bearer {token}
Content-Type: multipart/form-data

{
  "provedor_nf": "issnet",
  "issnet_usuario": "usuario_teste",
  "issnet_senha": "senha_secreta",
  "issnet_certificado": [arquivo.pfx],
  "issnet_senha_certificado": "senha_cert",
  "codigo_servico_municipal": "1401",
  "descricao_servico_padrao": "Desenvolvimento de software",
  "aliquota_iss": "2.50",
  "emitir_nf_automaticamente": true
}
```

## Validações Implementadas

### Frontend
- ✅ Arquivo deve ter extensão .pfx
- ✅ Campos obrigatórios por provedor
- ✅ Alíquota ISS entre 0 e 100
- ✅ Mensagens de erro amigáveis

### Backend (já implementado)
- ✅ Senhas como write_only no serializer
- ✅ Upload seguro de certificados
- ✅ Validação de campos obrigatórios

## Segurança

### Implementado
- ✅ Senhas nunca são retornadas pela API
- ✅ Certificados armazenados em pasta protegida
- ✅ Upload apenas de arquivos .pfx
- ✅ Autenticação obrigatória (Bearer token)

### Próximas Melhorias
- ⏳ Criptografia de senhas no banco
- ⏳ Alerta de vencimento de certificado
- ⏳ Rotação automática de credenciais
- ⏳ Logs de auditoria de alterações

## Testes Realizados

### Build
```bash
npm run build
✅ Compilação sem erros TypeScript
✅ Todas as páginas geradas corretamente
```

### Deploy
```bash
✅ Heroku v1542 - Backend atualizado
✅ Vercel (automático) - Frontend atualizado
✅ Migration 0044 já aplicada em produção
```

## Próximos Passos

### Fase 3: Implementação ISSNet (Backend)
1. Criar módulo `backend/nfse_integration/`
2. Implementar cliente SOAP para ISSNet
3. Construtor de XML RPS
4. Assinatura digital com certificado
5. Testes em ambiente de homologação

### Fase 4: Serviço Unificado
1. Criar `NFSeService` que escolhe provedor
2. Integrar com fluxo de pagamento
3. Dashboard de notas emitidas
4. Logs e auditoria

### Fase 5: API Nacional NFS-e
1. Habilitar opção "API Nacional"
2. Implementar cliente para API Nacional
3. Suporte para múltiplos municípios

## URLs de Acesso

### Produção
- **Frontend**: https://lwksistemas.com.br/loja/{cnpj}/crm-vendas/configuracoes/nota-fiscal
- **Backend API**: https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/config/

### Loja de Teste
- **CNPJ**: 41449198000172
- **URL**: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes/nota-fiscal

## Documentação Relacionada

- [Análise Completa](./ANALISE_EMISSAO_NFSE_RIBEIRAO_PRETO.md)
- [Configuração Backend](./CONFIGURACAO_NFSE_LOJA.md)
- [Migration 0044](./backend/crm_vendas/migrations/0044_add_nfse_config.py)

## Commit

```bash
git commit -m "feat: adicionar interface de configuração de NFS-e

- Atualizar CRMConfigContext com campos de NFS-e
- Criar página de configuração de nota fiscal
- Adicionar opções: Asaas, ISSNet, API Nacional, Manual
- Upload de certificado digital .pfx
- Configurações gerais: código serviço, alíquota ISS, descrição
- Adicionar link na página principal de configurações"
```

## Status

✅ **Fase 1 - Backend**: Concluída (v1541)
✅ **Fase 2 - Frontend**: Concluída (v1542)
⏳ **Fase 3 - Cliente ISSNet**: Aguardando
⏳ **Fase 4 - Serviço Unificado**: Aguardando
⏳ **Fase 5 - API Nacional**: Aguardando

---

**Implementado por**: Kiro AI Assistant
**Data**: 09/04/2026
**Versão Backend**: Heroku v1542
**Versão Frontend**: Vercel (deploy automático)
