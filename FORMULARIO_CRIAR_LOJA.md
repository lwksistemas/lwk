# 📝 FORMULÁRIO DE CRIAÇÃO DE LOJA

## ✅ Implementado com 8 Campos Completos

**URL**: http://localhost:3000/superadmin/lojas  
**Botão**: "+ Nova Loja"

---

## 🎯 8 Campos Implementados

### 1️⃣ Cadastro da Loja (CPF ou CNPJ)
- **Campo**: CPF ou CNPJ
- **Formato**: Automático
  - CPF: `000.000.000-00`
  - CNPJ: `00.000.000/0000-00`
- **Validação**: Obrigatório
- **Máscara**: Aplicada automaticamente ao digitar

### 2️⃣ Escolher Tipo de Loja
- **Opções**:
  - 🟢 **E-commerce** (Verde) - Loja virtual para venda de produtos
  - 🔵 **Serviços** (Azul) - Prestação de serviços com agendamento
  - 🔴 **Restaurante** (Vermelho) - Delivery de comida e bebidas
- **Seleção**: Cards visuais com cores
- **Dashboard**: Cada tipo tem seu dashboard específico

### 3️⃣ Escolher Assinatura (Mensal ou Anual)
- **Planos Disponíveis**:
  1. **Básico** - R$ 49,90/mês ou R$ 499,00/ano
  2. **Profissional** - R$ 99,90/mês ou R$ 999,00/ano
  3. **Enterprise** - R$ 299,90/mês ou R$ 2.999,00/ano

- **Tipo de Assinatura**:
  - ⏰ **Mensal**: Cobrança todo mês
  - 📅 **Anual**: Cobrança anual (desconto)

- **Cálculo Automático**: Valor exibido conforme seleção

### 4️⃣ Escolher Dia de Pagamento
- **Opções**: Dia 1 a 28 do mês
- **Padrão**: Dia 10
- **Próxima Cobrança**: Calculada automaticamente
- **Exemplo**: Se escolher dia 15, toda cobrança será no dia 15

### 5️⃣ Vincular ao Dashboard do Suporte
- **Automático**: ✅ Vinculado automaticamente
- **Funcionalidade**: Loja aparece no dashboard de suporte
- **Chamados**: Suporte pode ver chamados desta loja

### 6️⃣ Criar Financeiro da Loja
- **Automático**: ✅ Criado automaticamente
- **Dados Criados**:
  - Valor da mensalidade (baseado no plano e tipo)
  - Data da próxima cobrança
  - Dia de vencimento
  - Status: Pendente (trial) ou Ativo
  - Total pago: R$ 0,00
  - Total pendente: R$ 0,00

### 7️⃣ Criar Página de Login Personalizada
- **Automático**: ✅ Criada automaticamente
- **URL**: `/loja/{slug}/login`
- **Personalização**:
  - Cores baseadas no tipo de loja
  - Logo (se fornecido)
  - Background (se fornecido)
  - Título: Nome da loja
  - Subtítulo: "Acesso ao Painel"

### 8️⃣ Criar Banco de Dados Isolado
- **Automático**: ✅ Criado automaticamente após criar loja
- **Nome**: `db_loja_{slug}.sqlite3`
- **Migrations**: Aplicadas automaticamente
- **Isolamento**: Dados 100% isolados
- **Tabelas**: Produtos, Pedidos, Clientes, etc.

---

## 📋 FORMULÁRIO COMPLETO

### Seção 1: Informações Básicas
```
┌─────────────────────────────────────────┐
│ 1. Informações Básicas                  │
├─────────────────────────────────────────┤
│ Nome da Loja: [________________]        │
│ Slug (URL): [________________]          │
│ CPF ou CNPJ: [________________]         │
│ Descrição: [____________________]       │
│            [____________________]       │
└─────────────────────────────────────────┘
```

### Seção 2: Tipo de Loja
```
┌─────────────────────────────────────────┐
│ 2. Tipo de Loja                         │
├─────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │🟢 E-comm │ │🔵 Serviç │ │🔴 Restau │ │
│ │  erce    │ │  os      │ │  rante   │ │
│ └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────┘
```

### Seção 3: Plano e Assinatura
```
┌─────────────────────────────────────────┐
│ 3. Plano e Assinatura                   │
├─────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │ Básico   │ │Profissio │ │Enterpris │ │
│ │R$ 49,90  │ │R$ 99,90  │ │R$ 299,90 │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│                                         │
│ Tipo: [Mensal ▼]  Vencimento: [10 ▼]  │
│                                         │
│ 💰 Valor: R$ 49,90 (mensal)            │
│    Vencimento todo dia 10 do mês       │
└─────────────────────────────────────────┘
```

### Seção 4: Usuário Administrador
```
┌─────────────────────────────────────────┐
│ 4. Usuário Administrador da Loja        │
├─────────────────────────────────────────┤
│ Nome de Usuário: [________________]     │
│ Senha: [________________]               │
│ E-mail: [________________]              │
└─────────────────────────────────────────┘
```

### Resumo Final
```
┌─────────────────────────────────────────┐
│ Resumo                                  │
├─────────────────────────────────────────┤
│ ✅ Loja: Minha Loja Tech                │
│ ✅ Tipo: E-commerce                     │
│ ✅ Plano: Básico                        │
│ ✅ Assinatura: Mensal                   │
│ ✅ Vencimento: Dia 10                   │
│ ✅ Dashboard de Suporte: Vinculado      │
│ ✅ Página de Login: /loja/slug/login    │
│ ✅ Banco de Dados: Criado automaticamente│
└─────────────────────────────────────────┘

[Cancelar]  [Criar Loja]
```

---

## 🔄 FLUXO DE CRIAÇÃO

### Passo a Passo:

1. **Usuário clica em "+ Nova Loja"**
   - Modal abre com formulário completo

2. **Preenche Seção 1: Informações Básicas**
   - Nome da loja
   - Slug (gerado automaticamente)
   - CPF/CNPJ (com máscara)
   - Descrição (opcional)

3. **Seleciona Seção 2: Tipo de Loja**
   - Escolhe entre E-commerce, Serviços ou Restaurante
   - Cores são aplicadas automaticamente

4. **Configura Seção 3: Plano e Assinatura**
   - Escolhe plano (Básico, Profissional, Enterprise)
   - Seleciona tipo (Mensal ou Anual)
   - Define dia de vencimento (1-28)
   - Valor calculado automaticamente

5. **Define Seção 4: Usuário Administrador**
   - Nome de usuário
   - Senha (mínimo 6 caracteres)
   - E-mail

6. **Revisa Resumo**
   - Todos os dados são exibidos
   - Confirmação visual de todas as 8 funcionalidades

7. **Clica em "Criar Loja"**
   - Sistema cria loja no banco superadmin
   - Cria usuário administrador
   - Cria financeiro com valores calculados
   - Cria banco de dados isolado automaticamente
   - Aplica migrations no novo banco
   - Vincula ao dashboard de suporte
   - Cria página de login personalizada

8. **Sucesso!**
   - Mensagem de confirmação
   - Loja aparece na listagem
   - Banco isolado criado
   - Pronto para uso

---

## 🎨 PERSONALIZAÇÃO AUTOMÁTICA

### Cores por Tipo de Loja:
- **E-commerce**: Verde (#10B981)
- **Serviços**: Azul (#3B82F6)
- **Restaurante**: Vermelho (#EF4444)

### URL de Login:
- Formato: `/loja/{slug}/login`
- Exemplo: `/loja/minha-loja-tech/login`

### Banco de Dados:
- Formato: `db_loja_{slug}.sqlite3`
- Exemplo: `db_loja_minha_loja_tech.sqlite3`

---

## 💰 CÁLCULO DE VALORES

### Mensal:
```
Básico: R$ 49,90/mês
Profissional: R$ 99,90/mês
Enterprise: R$ 299,90/mês
```

### Anual (com desconto):
```
Básico: R$ 499,00/ano (R$ 41,58/mês)
Profissional: R$ 999,00/ano (R$ 83,25/mês)
Enterprise: R$ 2.999,00/ano (R$ 249,92/mês)
```

---

## 📅 PRÓXIMA COBRANÇA

### Cálculo Automático:
- Se hoje é dia 5 e vencimento é dia 10: Próxima cobrança dia 10 deste mês
- Se hoje é dia 15 e vencimento é dia 10: Próxima cobrança dia 10 do próximo mês

### Exemplo:
```
Hoje: 15/01/2026
Dia de vencimento: 10
Próxima cobrança: 10/02/2026
```

---

## ✅ VALIDAÇÕES

### Campos Obrigatórios:
- ✅ Nome da loja
- ✅ Slug
- ✅ CPF ou CNPJ
- ✅ Tipo de loja
- ✅ Plano
- ✅ Nome de usuário
- ✅ Senha (mínimo 6 caracteres)
- ✅ E-mail

### Validações Automáticas:
- ✅ Slug único (não pode repetir)
- ✅ CPF/CNPJ formatado
- ✅ E-mail válido
- ✅ Senha mínima de 6 caracteres
- ✅ Dia de vencimento entre 1 e 28

---

## 🔧 BACKEND

### Endpoint:
```
POST /api/superadmin/lojas/
```

### Payload:
```json
{
  "nome": "Minha Loja Tech",
  "slug": "minha-loja-tech",
  "descricao": "Loja de tecnologia",
  "cpf_cnpj": "12.345.678/0001-90",
  "tipo_loja": 1,
  "plano": 1,
  "tipo_assinatura": "mensal",
  "dia_vencimento": 10,
  "owner_username": "admin_tech",
  "owner_password": "senha123",
  "owner_email": "admin@tech.com"
}
```

### Resposta:
```json
{
  "id": 2,
  "nome": "Minha Loja Tech",
  "slug": "minha-loja-tech",
  "database_name": "loja_minha_loja_tech",
  "database_created": true,
  "login_page_url": "/loja/minha-loja-tech/login",
  "financeiro": {
    "valor_mensalidade": "49.90",
    "data_proxima_cobranca": "2026-02-10",
    "dia_vencimento": 10
  }
}
```

---

## 🎯 RESULTADO FINAL

Após criar a loja, o sistema terá:

1. ✅ **Loja criada** no banco superadmin
2. ✅ **Usuário administrador** criado
3. ✅ **Financeiro configurado** com valores e datas
4. ✅ **Banco isolado** criado e com migrations
5. ✅ **Dashboard de suporte** vinculado
6. ✅ **Página de login** personalizada
7. ✅ **Cores e tema** aplicados
8. ✅ **Pronto para uso** imediatamente

---

## 📱 COMO TESTAR

### 1. Acessar:
```
http://localhost:3000/superadmin/login
```

### 2. Fazer Login:
```
Usuário: superadmin
Senha: super123
```

### 3. Ir para Gerenciar Lojas:
```
http://localhost:3000/superadmin/lojas
```

### 4. Clicar em "+ Nova Loja"

### 5. Preencher Formulário:
- Nome: "Minha Loja Teste"
- CPF/CNPJ: "12345678901"
- Tipo: E-commerce
- Plano: Básico
- Assinatura: Mensal
- Vencimento: Dia 10
- Usuário: "admin_teste"
- Senha: "teste123"
- E-mail: "admin@teste.com"

### 6. Clicar em "Criar Loja"

### 7. Aguardar Criação:
- Loja criada ✅
- Banco criado ✅
- Mensagem de sucesso ✅

### 8. Testar Login da Nova Loja:
```
http://localhost:3000/loja/login?slug=minha-loja-teste
Usuário: admin_teste
Senha: teste123
```

---

## 🎉 SISTEMA COMPLETO!

**Todos os 8 campos implementados e funcionando!**

1. ✅ CPF/CNPJ com máscara
2. ✅ Tipo de loja com cards visuais
3. ✅ Assinatura mensal/anual
4. ✅ Dia de pagamento configurável
5. ✅ Vinculação automática ao suporte
6. ✅ Financeiro criado automaticamente
7. ✅ Login personalizado por loja
8. ✅ Banco isolado criado automaticamente

**Pronto para criar lojas! 🚀**
