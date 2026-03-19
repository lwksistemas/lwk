# Implementação da Página de Contatos no CRM - v1191

## Data
19/03/2026

## Objetivo
Criar interface completa para gerenciar contatos (pessoas) vinculados a contas (empresas) no CRM de Vendas.

## Problema Identificado
- Backend já tinha o modelo `Contato` e API implementados
- Frontend não tinha interface para gerenciar contatos
- Módulo "contatos" não estava ativo nas configurações

## Solução Implementada

### 1. Frontend - Página de Contatos
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/contatos/page.tsx`

Funcionalidades implementadas:
- Listagem de contatos com informações da conta vinculada
- Criar novo contato (obrigatório vincular a uma conta)
- Editar contato existente
- Visualizar detalhes do contato
- Excluir contato
- Modal de visualização via query param `?ver=ID`
- Design seguindo padrão Salesforce Lightning

Campos do formulário:
- Nome (obrigatório)
- Conta (obrigatório - select com contas cadastradas)
- Cargo
- Telefone
- Email
- Observações

### 2. Sidebar - Link para Contatos
**Arquivo**: `frontend/components/crm-vendas/SidebarCrm.tsx`

Adicionado link para página de Contatos:
- Aparece apenas se módulo "contatos" estiver ativo
- Ícone: User
- Posicionado após "Contas" e antes de "Calendário"

### 3. Backend - Comandos de Manutenção

#### Comando: add_crmconfig_table
**Arquivo**: `backend/crm_vendas/management/commands/add_crmconfig_table.py`

Função: Criar tabela `crm_vendas_config` em todos os schemas de lojas
- Verifica se tabela já existe antes de criar
- Cria índices necessários
- Executa no schema correto de cada loja

#### Comando: ativar_modulo_contatos
**Arquivo**: `backend/crm_vendas/management/commands/ativar_modulo_contatos.py`

Função: Ativar módulo "contatos" em todas as lojas
- Busca ou cria configuração CRM para cada loja
- Ativa módulo "contatos" nos `modulos_ativos`
- Faz parse correto do JSON retornado do banco
- Cria config com valores padrão se não existir

### 4. Modelo Backend (já existia)
**Arquivo**: `backend/crm_vendas/models.py`

Modelo `Contato`:
- nome (CharField)
- email (EmailField, opcional)
- telefone (CharField, opcional)
- cargo (CharField, opcional)
- conta (ForeignKey para Conta, obrigatório)
- observacoes (TextField, opcional)
- created_at, updated_at (DateTimeField)

API: `/api/crm-vendas/contatos/`
- GET: Listar contatos
- POST: Criar contato
- GET /{id}/: Detalhes do contato
- PUT /{id}/: Atualizar contato
- DELETE /{id}/: Excluir contato

## Fluxo Correto do CRM

1. **Lead** (potencial cliente) → qualificar
2. **Conta** (empresa/organização) → criar quando lead qualificado
3. **Contato** (pessoa na empresa) → vincular à conta
4. **Oportunidade** (negócio) → vincular ao lead que tem conta
5. **Proposta/Contrato** → vincular à oportunidade

## Comandos Executados

```bash
# Deploy frontend
cd frontend && vercel --prod --yes

# Deploy backend
git push heroku master

# Criar tabela crm_vendas_config (se necessário)
heroku run "cd backend && python manage.py add_crmconfig_table"

# Ativar módulo contatos
heroku run "cd backend && python manage.py ativar_modulo_contatos"
```

## Resultado

✅ Página de Contatos criada e funcionando
✅ Link adicionado ao sidebar
✅ Módulo "contatos" ativado em todas as lojas
✅ Tabela crm_vendas_config criada em todos os schemas
✅ Deploy v1191 concluído

## Próximos Passos

- Testar criação de contatos vinculados a contas
- Verificar se contatos aparecem corretamente na listagem
- Validar edição e exclusão de contatos
- Confirmar que modal de visualização funciona via query param

## Observações

- Módulo "contatos" já estava nos módulos padrão do CRMConfig
- Backend já estava completo, apenas frontend precisava ser criado
- Comandos de manutenção criados para facilitar ativação em novas lojas
