# Feature: Sistema de Templates de Propostas (v1025)

**Data**: 18/03/2026  
**Versão**: v1025 (Backend v1130, Frontend Deploy Vercel)  
**Status**: ✅ COMPLETO E OPERACIONAL

---

## 🎯 OBJETIVO

Permitir que o usuário salve múltiplas propostas padrão diferentes e escolha qual usar ao criar uma nova proposta.

### Problema Anterior

- ✅ Sistema permitia salvar UMA proposta padrão
- ❌ Não era possível ter múltiplos templates (ex: Proposta Básica, Proposta Premium, Proposta Corporativa)
- ❌ Usuário tinha que reescrever o conteúdo toda vez que queria usar um template diferente

---

## ✅ SOLUÇÃO IMPLEMENTADA (BACKEND)

### Novo Modelo: `PropostaTemplate`

Criado modelo para armazenar múltiplos templates de propostas:

```python
class PropostaTemplate(LojaIsolationMixin, models.Model):
    """Template de proposta para reutilização."""
    nome = models.CharField(max_length=255)  # Ex: "Proposta Padrão", "Proposta Premium"
    conteudo = models.TextField()  # Conteúdo do template
    is_padrao = models.BooleanField(default=False)  # Template padrão
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Funcionalidades

1. **Criar múltiplos templates**: Cada loja pode ter vários templates
2. **Marcar template padrão**: Um template pode ser marcado como padrão (usado ao criar novas propostas)
3. **Ativar/desativar templates**: Templates inativos não aparecem na lista
4. **Isolamento por loja**: Cada loja vê apenas seus próprios templates

### Endpoint da API

**Base URL**: `/crm-vendas/proposta-templates/`

#### Listar Templates

```http
GET /crm-vendas/proposta-templates/
```

**Resposta**:
```json
[
  {
    "id": 1,
    "nome": "Proposta Padrão",
    "conteudo": "Prezado cliente...",
    "is_padrao": true,
    "ativo": true,
    "created_at": "2026-03-18T12:00:00Z",
    "updated_at": "2026-03-18T12:00:00Z"
  },
  {
    "id": 2,
    "nome": "Proposta Premium",
    "conteudo": "Prezado cliente VIP...",
    "is_padrao": false,
    "ativo": true,
    "created_at": "2026-03-18T12:05:00Z",
    "updated_at": "2026-03-18T12:05:00Z"
  }
]
```

#### Criar Template

```http
POST /crm-vendas/proposta-templates/
Content-Type: application/json

{
  "nome": "Proposta Corporativa",
  "conteudo": "Prezada empresa...",
  "is_padrao": false,
  "ativo": true
}
```

#### Atualizar Template

```http
PUT /crm-vendas/proposta-templates/{id}/
Content-Type: application/json

{
  "nome": "Proposta Corporativa Atualizada",
  "conteudo": "Novo conteúdo...",
  "is_padrao": false,
  "ativo": true
}
```

#### Marcar como Padrão

```http
POST /crm-vendas/proposta-templates/{id}/marcar_padrao/
```

**Comportamento**: Marca este template como padrão e desmarca todos os outros automaticamente.

#### Excluir Template

```http
DELETE /crm-vendas/proposta-templates/{id}/
```

---

## 📋 ARQUIVOS CRIADOS/MODIFICADOS

### Backend

**Novos arquivos**:
- `backend/crm_vendas/migrations/0021_add_proposta_template.py` - Migration para criar tabela

**Arquivos modificados**:
- `backend/crm_vendas/models.py` - Adicionado modelo `PropostaTemplate`
- `backend/crm_vendas/serializers.py` - Adicionado `PropostaTemplateSerializer`
- `backend/crm_vendas/views.py` - Adicionado `PropostaTemplateViewSet`
- `backend/crm_vendas/urls.py` - Adicionada rota `/proposta-templates/`

### Frontend

**Novos arquivos**:
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/proposta-templates/page.tsx` - Página de gerenciamento

**Arquivos modificados**:
- `frontend/components/crm-vendas/PropostaFormContent.tsx` - Adicionado seletor de templates
- `frontend/components/crm-vendas/modals/ModalPropostaForm.tsx` - Props de templates
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/propostas/page.tsx` - Carrega templates

### Documentação

**Novos arquivos**:
- `FEATURE_TEMPLATES_PROPOSTAS_v1025.md` - Documentação completa
- `CORRECAO_ERRO_BUILD_TEMPLATES_v1025.md` - Correção de erro de build
- `GUIA_USO_TEMPLATES_PROPOSTAS.md` - Guia de uso para usuários
- `criar_template_proposta.py` - Script Python para criar templates via API

---

## 🚀 DEPLOY

### Backend (Heroku)

```bash
cd /caminho/do/projeto
git add backend/crm_vendas/
git commit -m "feat(crm): adiciona sistema de templates de propostas (v1025)"
git push heroku master
```

**Versão implantada**: ✅ v1128 (18/03/2026 12:05)

### Frontend (Vercel)

✅ **IMPLEMENTADO E DEPLOYADO** (18/03/2026)

**Deploy URL**: https://lwksistemas.com.br  
**Inspect**: https://vercel.com/lwks-projects-48afd555/frontend/9gphujiZ8BQjFDe2nNuYZ2YTaxiV

**Correção aplicada**: Erro de build TypeScript corrigido (propriedade `title` em ícones Lucide)

---

## ✅ FUNCIONALIDADES IMPLEMENTADAS (FRONTEND)

### 1. Página de Gerenciamento de Templates

**URL**: `/loja/[slug]/crm-vendas/proposta-templates`

**Funcionalidades**:
- ✅ Lista de templates existentes em cards visuais
- ✅ Botão "Novo Template"
- ✅ Ações: Editar, Excluir, Marcar como Padrão (estrela)
- ✅ Indicador visual do template padrão (⭐)
- ✅ Status ativo/inativo
- ✅ Modal de criação/edição
- ✅ Modal de confirmação de exclusão
- ✅ Loading states e tratamento de erros

### 2. Seletor de Template ao Criar Proposta

**Localização**: Modal/página de criação de proposta

**Funcionalidades**:
- ✅ Dropdown com templates disponíveis
- ✅ Indicação de template padrão no dropdown
- ✅ Ao selecionar template, preenche campo de conteúdo automaticamente
- ✅ Template padrão carregado automaticamente em novas propostas
- ✅ Permite editar conteúdo após selecionar template

### 3. Botão "Salvar como Proposta PADRAO"

**Funcionalidade legada mantida**:
- ✅ Botão para salvar conteúdo em `CRMConfig.proposta_conteudo_padrao`
- ✅ Compatibilidade com sistema anterior
- ⚠️ Recomenda-se usar sistema de templates ao invés deste botão

---

## 💡 EXEMPLO DE USO

### Cenário: Empresa com 3 Tipos de Propostas

1. **Criar Templates**:
   - "Proposta Básica" (padrão) - Para clientes pequenos
   - "Proposta Premium" - Para clientes médios
   - "Proposta Corporativa" - Para grandes empresas

2. **Ao Criar Nova Proposta**:
   - Selecionar oportunidade
   - Escolher template no dropdown
   - Conteúdo é preenchido automaticamente
   - Editar se necessário
   - Salvar

3. **Vantagens**:
   - ⚡ Criação rápida de propostas
   - 📝 Padronização de conteúdo
   - 🎯 Templates específicos para cada tipo de cliente
   - ♻️ Reutilização de conteúdo aprovado

---

## 🔒 SEGURANÇA E ISOLAMENTO

### Isolamento por Loja

- ✅ Cada loja vê apenas seus próprios templates
- ✅ Filtro por `loja_id` aplicado automaticamente
- ✅ Impossível acessar templates de outras lojas

### Permissões

- ✅ Apenas usuários autenticados podem acessar
- ✅ Vendedores e proprietários têm acesso total aos templates
- ✅ Templates são compartilhados entre todos os usuários da loja

### Validação

- ✅ Apenas um template pode ser marcado como padrão por loja
- ✅ Ao marcar template como padrão, outros são desmarcados automaticamente
- ✅ Nome e conteúdo são obrigatórios

---

## 📊 ESTRUTURA DO BANCO DE DADOS

### Tabela: `crm_vendas_proposta_template`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | BigInt | ID único do template |
| loja_id | Integer | ID da loja (tenant) |
| nome | Varchar(255) | Nome do template |
| conteudo | Text | Conteúdo do template |
| is_padrao | Boolean | Se é o template padrão |
| ativo | Boolean | Se está ativo |
| created_at | DateTime | Data de criação |
| updated_at | DateTime | Data de atualização |

### Índices

- `crm_pt_loja_ativo_idx`: (loja_id, ativo)
- `crm_pt_loja_padrao_idx`: (loja_id, is_padrao)

---

## 🔗 REFERÊNCIAS

- Correção anterior: `CORRECAO_DEMORA_CRIAR_OPORTUNIDADE_v1024.md`
- Modelo Proposta: `backend/crm_vendas/models.py` (linha 366)
- Página de propostas: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/propostas/page.tsx`

---

## 📝 NOTAS TÉCNICAS

### Migração de Dados

Se a loja já tem uma proposta padrão salva em `CRMConfig.proposta_conteudo_padrao`, será necessário criar um script de migração para:

1. Ler o conteúdo de `CRMConfig.proposta_conteudo_padrao`
2. Criar um `PropostaTemplate` com nome "Proposta Padrão"
3. Marcar como `is_padrao=True`
4. (Opcional) Remover campo `proposta_conteudo_padrao` de `CRMConfig`

### Compatibilidade

O sistema atual de proposta padrão (`CRMConfig.proposta_conteudo_padrao`) ainda funciona. O novo sistema de templates é uma adição, não uma substituição.

### Performance

- ✅ Índices criados para otimizar queries por loja e status
- ✅ Filtro de templates ativos aplicado por padrão
- ✅ Queryset otimizado com filtro por `loja_id`
