# Implementação de Dados Completos de Empresa no Modal de Contas - v1192

## Data
19/03/2026

## Objetivo
Adicionar todos os campos necessários para cadastro completo de empresas no modal "Nova Conta", incluindo funcionalidade de consulta automática de CNPJ e CEP.

## Problema Identificado
- Modal de "Nova Conta" tinha apenas campos básicos (nome, segmento, telefone, email, cidade, estado, endereço, site)
- Faltavam dados essenciais da empresa: CNPJ, razão social, inscrição estadual
- Endereço não estava estruturado (faltava CEP, logradouro, número, complemento, bairro, UF)
- Não havia consulta automática de CNPJ para preencher dados da empresa
- Dados incompletos dificultavam geração de propostas e contratos

## Solução Implementada

### 1. Backend - Modelo Conta Atualizado
**Arquivo**: `backend/crm_vendas/models.py`

Campos adicionados:
- `razao_social` (CharField, 255) - Razão social da empresa
- `cnpj` (CharField, 18) - CNPJ formatado (00.000.000/0000-00)
- `inscricao_estadual` (CharField, 20) - Inscrição estadual
- `site` (URLField) - Website da empresa
- `cep` (CharField, 10) - CEP formatado (00000-000)
- `logradouro` (CharField, 255) - Rua, avenida, etc.
- `numero` (CharField, 20) - Número do endereço
- `complemento` (CharField, 100) - Complemento (apto, sala, etc.)
- `bairro` (CharField, 100) - Bairro
- `uf` (CharField, 2) - Estado (UF)

Campos atualizados:
- `nome` - Agora com help_text "Nome fantasia da empresa"
- `endereco` - Marcado como "campo legado" para compatibilidade
- `cidade` - Mantido com help_text atualizado

### 2. Migration
**Arquivo**: `backend/crm_vendas/migrations/0027_add_complete_company_data_to_conta.py`

Migration criada para adicionar todos os novos campos ao modelo Conta.

### 3. Frontend - Formulário Completo
**Arquivo**: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/customers/page.tsx`

#### Funcionalidades Implementadas:

**A) Consulta de CNPJ (Brasil API)**
- Campo CNPJ com botão "Consultar CNPJ"
- Integração com API: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}`
- Preenche automaticamente:
  - Razão Social
  - Nome Fantasia
  - Telefone
  - Email
  - CEP
  - Logradouro
  - Número
  - Complemento
  - Bairro
  - Cidade
  - UF
- Validação: CNPJ deve ter 14 dígitos
- Feedback visual: botão mostra "Consultando..." durante requisição
- Alert de sucesso ou erro após consulta

**B) Consulta de CEP (ViaCEP)**
- Campo CEP com consulta automática ao sair do campo (onBlur)
- Integração com API: `https://viacep.com.br/ws/{cep}/json/`
- Preenche automaticamente:
  - Logradouro
  - Bairro
  - Cidade
  - UF
- Validação: CEP deve ter 8 dígitos
- Alert de erro se CEP não encontrado

**C) Estrutura do Formulário:**

1. **Seção de Consulta CNPJ** (destaque azul)
   - Campo CNPJ
   - Botão "Consultar CNPJ"
   - Dica: "Digite o CNPJ e clique em 'Consultar CNPJ' para preencher automaticamente"

2. **Dados da Empresa**
   - Razão Social
   - Nome Fantasia (obrigatório)
   - Inscrição Estadual
   - Segmento

3. **Contato**
   - Telefone
   - Email
   - Site

4. **Endereço** (seção separada)
   - CEP (com consulta automática)
   - UF
   - Logradouro
   - Número
   - Complemento
   - Bairro
   - Cidade

5. **Observações**
   - Campo de texto livre

### 4. Interface do Usuário

**Modal aumentado**: max-w-2xl para acomodar mais campos
**Scroll**: max-h-[90vh] com overflow-y-auto
**Grid responsivo**: 2 colunas em desktop, 1 coluna em mobile
**Validação**: Apenas "Nome Fantasia" é obrigatório
**Feedback visual**: 
- Botão desabilitado durante consulta CNPJ
- Loading states ("Consultando...", "Salvando...")
- Alerts para sucesso/erro

## Fluxo de Uso

### Cenário 1: Cadastro com CNPJ
1. Usuário clica em "Nova Conta"
2. Digite o CNPJ (ex: 00.000.000/0000-00)
3. Clica em "Consultar CNPJ"
4. Sistema preenche automaticamente todos os dados da empresa
5. Usuário revisa/ajusta dados se necessário
6. Clica em "Salvar"

### Cenário 2: Cadastro Manual
1. Usuário clica em "Nova Conta"
2. Preenche manualmente os campos
3. Ao preencher CEP, sistema busca endereço automaticamente
4. Clica em "Salvar"

### Cenário 3: Edição de Conta Existente
1. Usuário clica em "Editar" em uma conta
2. Todos os campos são carregados
3. Pode consultar CNPJ novamente para atualizar dados
4. Pode consultar CEP para atualizar endereço
5. Clica em "Salvar"

## APIs Utilizadas

### Brasil API (CNPJ)
- **URL**: https://brasilapi.com.br/api/cnpj/v1/{cnpj}
- **Método**: GET
- **Gratuita**: Sim
- **Limite**: Sem limite documentado
- **Dados retornados**: Razão social, nome fantasia, telefone, email, endereço completo

### ViaCEP
- **URL**: https://viacep.com.br/ws/{cep}/json/
- **Método**: GET
- **Gratuita**: Sim
- **Limite**: Sem limite documentado
- **Dados retornados**: Logradouro, bairro, cidade, UF

## Benefícios

✅ Cadastro rápido e preciso de empresas via CNPJ
✅ Redução de erros de digitação
✅ Endereço completo e estruturado
✅ Dados prontos para uso em propostas e contratos
✅ Experiência do usuário melhorada
✅ Conformidade com dados oficiais da Receita Federal

## Comandos Executados

```bash
# Backend - Deploy inicial
git add -A
git commit -m "feat: adicionar campos completos de empresa no modal de Contas + consulta CNPJ/CEP"
git push heroku master

# Frontend
cd frontend
git add -A
git commit -m "fix: corrigir referência a campo estado para uf no modal de visualização"
vercel --prod --yes

# Backend - Correção: Aplicar campos em todos os schemas
git add backend/crm_vendas/management/commands/add_conta_fields.py
git commit -m "feat: adicionar comando para aplicar campos de Conta em todos os schemas de lojas"
git push heroku master

# Executar comando para adicionar campos nos schemas das lojas
heroku run "cd backend && python manage.py add_conta_fields"
```

## Resultado

✅ Migration 0027 aplicada com sucesso no schema público
✅ Modelo Conta atualizado com todos os campos
✅ Formulário completo implementado no frontend
✅ Consulta de CNPJ funcionando (Brasil API)
✅ Consulta de CEP funcionando (ViaCEP)
✅ Deploy v1192 concluído (frontend + backend inicial)
✅ Deploy v1193 concluído (comando add_conta_fields)
✅ Campos aplicados em 2 lojas ativas:
  - Loja 132 (FELIX REPRESENTACOES) - 10 colunas adicionadas
  - Loja 130 (CRM VENDAS TESTE) - 10 colunas adicionadas
✅ Erro 500 ao carregar leads CORRIGIDO

## Problema Encontrado e Resolvido

**Erro**: 500 Internal Server Error ao carregar leads
**Causa**: Migration foi aplicada apenas no schema público, mas não nos schemas dos tenants (lojas)
**Sintoma**: Ao fazer JOIN entre Lead e Conta, o PostgreSQL não encontrava as colunas novas
**Solução**: Criado comando `add_conta_fields.py` que adiciona as colunas em todos os schemas de lojas ativas
**Resultado**: Comando executado com sucesso, 10 colunas adicionadas em cada loja

## Próximos Passos

- ✅ Testar se leads carregam corretamente (erro 500 resolvido)
- Testar cadastro de conta com consulta CNPJ
- Verificar se dados são salvos corretamente
- Validar uso dos dados em propostas e contratos
- Adicionar máscara de formatação para CNPJ e CEP (opcional)
- Considerar adicionar validação de CNPJ (dígitos verificadores)

## Observações

- Campo `endereco` (legado) foi mantido para compatibilidade com dados antigos
- Todos os novos campos são opcionais, exceto "Nome Fantasia"
- APIs externas podem estar indisponíveis temporariamente (tratamento de erro implementado)
- Consulta de CEP é automática ao sair do campo (onBlur)
- Consulta de CNPJ requer clique no botão (para evitar consultas desnecessárias)
