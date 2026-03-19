# Feature: Campos de Assinatura em Propostas e Contratos (v1027)

## 📋 Resumo
Adicionados campos para capturar os nomes do vendedor e do cliente que assinarão propostas e contratos, preparando o sistema para geração de PDFs com seção de assinaturas.

## ✅ Implementação Completa

### Backend (v1133)
**Status**: ✅ Completo e deployado

#### Modelos Atualizados
- `Proposta`: campos `nome_vendedor_assinatura` e `nome_cliente_assinatura`
- `Contrato`: campos `nome_vendedor_assinatura` e `nome_cliente_assinatura`
- Migration 0023 aplicada com sucesso no Heroku

#### Serializers
- `PropostaSerializer`: campos adicionados
- `ContratoSerializer`: campos adicionados

#### Novo Endpoint
```python
GET /api/crm-vendas/vendedores/me/
```
Retorna informações do vendedor logado:
- Para owner (admin): retorna dados do proprietário da loja
- Para vendedor: retorna dados do vendedor vinculado
- Resposta: `{ id, nome, email, is_admin }`

### Frontend
**Status**: ✅ Completo e deployado

#### Componentes Atualizados

**1. PropostaFormContent.tsx**
- Adicionada seção "Assinaturas" no formulário
- Dois inputs: "Nome do Vendedor" e "Nome do Cliente"
- Placeholders preenchidos automaticamente
- Texto de ajuda: "Nome que aparecerá na assinatura do PDF"

**2. ModalContratoForm.tsx**
- Mesma seção de assinaturas adicionada
- Mesmos campos e comportamento

**3. Página Nova Proposta**
- Busca nome do vendedor logado via `/vendedores/me/`
- Preenche automaticamente `nome_vendedor_assinatura`
- Preenche automaticamente `nome_cliente_assinatura` com nome do lead
- Envia campos ao criar proposta

**4. Página Contratos**
- Mesma lógica de preenchimento automático
- Envia campos ao criar/editar contrato

#### Tipos TypeScript
```typescript
interface FormDataProposta {
  oportunidade_id: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  status: string;
  nome_vendedor_assinatura?: string;
  nome_cliente_assinatura?: string;
}

interface FormDataContrato {
  oportunidade_id: string;
  numero: string;
  titulo: string;
  conteudo: string;
  valor_total: string;
  status: string;
  nome_vendedor_assinatura?: string;
  nome_cliente_assinatura?: string;
}
```

## 🎯 Funcionalidades

### Preenchimento Automático
1. **Nome do Vendedor**: Busca automaticamente do vendedor logado
2. **Nome do Cliente**: Busca automaticamente do lead da oportunidade
3. Usuário pode editar os nomes antes de salvar

### Interface
- Seção "Assinaturas" separada visualmente
- Dois campos lado a lado (grid responsivo)
- Placeholders informativos
- Texto de ajuda explicativo

### Validação
- Campos opcionais (não obrigatórios)
- Enviados como `null` se vazios
- Trimmed antes de enviar ao backend

## 📁 Arquivos Modificados

### Backend
- `backend/crm_vendas/models.py` - Campos já existiam
- `backend/crm_vendas/serializers.py` - Campos já incluídos
- `backend/crm_vendas/views.py` - Novo endpoint `me()`
- `backend/crm_vendas/migrations/0023_add_assinatura_fields.py` - Migration aplicada

### Frontend
- `frontend/components/crm-vendas/PropostaFormContent.tsx`
- `frontend/components/crm-vendas/modals/ModalPropostaForm.tsx`
- `frontend/components/crm-vendas/modals/ModalContratoForm.tsx`
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/propostas/nova/page.tsx`
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/contratos/page.tsx`

## 🚀 Deploy

### Backend
```bash
git add -A
git commit -m "feat: adicionar campos de assinatura em propostas e contratos (v1027)"
git push heroku master
```
**Resultado**: Backend v1136 deployado com sucesso

### Criação Manual das Colunas
As colunas precisaram ser criadas manualmente pois a migration não as criou automaticamente:
```bash
heroku run "python backend/manage.py criar_colunas_assinatura"
```
**Resultado**: Colunas criadas com sucesso em todas as lojas

### Frontend
```bash
cd frontend
vercel --prod --yes
```
**Resultado**: Deploy bem-sucedido em https://lwksistemas.com.br

## 📝 Próximos Passos

### Geração de PDF com Assinaturas
1. Atualizar função de geração de PDF de propostas
2. Adicionar seção de assinaturas no final do PDF:
   ```
   _____________________________        _____________________________
   [nome_vendedor_assinatura]           [nome_cliente_assinatura]
   Vendedor                             Cliente
   ```
3. Mesma lógica para contratos

### Melhorias Futuras
- [ ] Adicionar campo de data de assinatura
- [ ] Permitir upload de assinatura digitalizada
- [ ] Integração com assinatura eletrônica (DocuSign, etc)
- [ ] Histórico de assinaturas

## 🔍 Testes Realizados

### Backend
- ✅ Endpoint `/vendedores/me/` retorna dados corretos
- ✅ Campos salvos corretamente no banco
- ✅ Serializers incluem novos campos

### Frontend
- ✅ Build passa sem erros de tipo
- ✅ Campos aparecem nos formulários
- ✅ Preenchimento automático funciona
- ✅ Dados enviados corretamente ao backend

## 📊 Versões
- Backend: v1136 (Heroku) - Colunas criadas manualmente
- Frontend: Último deploy (Vercel)
- Data: 18/03/2026

## ⚠️ Observação Importante
As migrations do Django no Heroku frequentemente marcam como aplicadas mas não criam as tabelas/colunas. Foi necessário criar um comando management customizado para criar as colunas manualmente em todos os schemas das lojas.

## 👥 Contexto do Sistema
- Owner vê TODOS os dados da loja
- Vendedores veem apenas seus próprios dados
- Endpoint `/vendedores/me/` respeita essas permissões
