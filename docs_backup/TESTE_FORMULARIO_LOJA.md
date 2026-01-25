# 🧪 TESTE DO FORMULÁRIO DE CRIAÇÃO DE LOJA

## ✅ Status: Implementado e Pronto para Teste

**URL**: http://localhost:3000/superadmin/lojas  
**Botão**: "+ Nova Loja"

---

## 🚀 PASSO A PASSO PARA TESTAR

### 1. Fazer Login como Super Admin
```
URL: http://localhost:3000/superadmin/login
Usuário: superadmin
Senha: super123
```

### 2. Ir para Gerenciar Lojas
```
URL: http://localhost:3000/superadmin/lojas
ou
Clicar em "Gerenciar Lojas" no dashboard
```

### 3. Clicar em "+ Nova Loja"
- Botão verde no canto superior direito
- Modal abrirá com formulário completo

---

## 📝 DADOS DE TESTE

### Exemplo 1: Loja de Tecnologia
```
=== Seção 1: Informações Básicas ===
Nome da Loja: Tech Store Brasil
Slug: tech-store-brasil (gerado automaticamente)
CPF/CNPJ: 12345678901234 (será formatado como 12.345.678/9012-34)
Descrição: Loja de produtos de tecnologia e eletrônicos

=== Seção 2: Tipo de Loja ===
Tipo: E-commerce (Verde)

=== Seção 3: Plano e Assinatura ===
Plano: Básico (R$ 49,90/mês)
Tipo de Assinatura: Mensal
Dia de Vencimento: 10

=== Seção 4: Usuário Administrador ===
Nome de Usuário: admin_tech
Senha: tech123456
E-mail: admin@techstore.com.br
```

### Exemplo 2: Salão de Beleza
```
=== Seção 1: Informações Básicas ===
Nome da Loja: Salão Beleza Total
Slug: salao-beleza-total
CPF/CNPJ: 98765432100 (será formatado como 987.654.321-00)
Descrição: Salão de beleza com agendamento online

=== Seção 2: Tipo de Loja ===
Tipo: Serviços (Azul)

=== Seção 3: Plano e Assinatura ===
Plano: Profissional (R$ 99,90/mês)
Tipo de Assinatura: Mensal
Dia de Vencimento: 15

=== Seção 4: Usuário Administrador ===
Nome de Usuário: admin_salao
Senha: salao123456
E-mail: admin@belezatotal.com.br
```

### Exemplo 3: Restaurante
```
=== Seção 1: Informações Básicas ===
Nome da Loja: Pizzaria Bella Napoli
Slug: pizzaria-bella-napoli
CPF/CNPJ: 11222333000144 (será formatado como 11.222.333/0001-44)
Descrição: Pizzaria com delivery

=== Seção 2: Tipo de Loja ===
Tipo: Restaurante (Vermelho)

=== Seção 3: Plano e Assinatura ===
Plano: Enterprise (R$ 299,90/mês)
Tipo de Assinatura: Anual (R$ 2.999,00/ano)
Dia de Vencimento: 5

=== Seção 4: Usuário Administrador ===
Nome de Usuário: admin_pizzaria
Senha: pizza123456
E-mail: admin@bellanapoli.com.br
```

---

## ✅ CHECKLIST DE TESTE

### Antes de Criar
- [ ] Backend rodando (http://localhost:8000)
- [ ] Frontend rodando (http://localhost:3000)
- [ ] Login como superadmin funcionando
- [ ] Página de lojas carregando

### Durante o Preenchimento
- [ ] Nome da loja gera slug automaticamente
- [ ] CPF/CNPJ aplica máscara ao digitar
- [ ] Tipos de loja aparecem como cards coloridos
- [ ] Planos aparecem com preços
- [ ] Tipo de assinatura altera valor exibido
- [ ] Dia de vencimento tem opções de 1 a 28
- [ ] Resumo mostra todos os dados preenchidos

### Após Criar
- [ ] Mensagem de sucesso aparece
- [ ] Loja aparece na listagem
- [ ] Banco isolado foi criado
- [ ] Pode acessar login da nova loja

### Testar Login da Nova Loja
- [ ] URL: http://localhost:3000/loja/login?slug={slug}
- [ ] Login com credenciais criadas funciona
- [ ] Dashboard da loja carrega
- [ ] Cores personalizadas aplicadas

---

## 🔍 VERIFICAÇÕES NO BACKEND

### Verificar Loja Criada
```bash
cd backend
sqlite3 db_superadmin.sqlite3 "SELECT id, nome, slug, cpf_cnpj, tipo_assinatura FROM superadmin_loja;"
```

### Verificar Financeiro Criado
```bash
sqlite3 db_superadmin.sqlite3 "SELECT loja_id, valor_mensalidade, dia_vencimento, data_proxima_cobranca FROM superadmin_financeiroloja;"
```

### Verificar Banco Isolado Criado
```bash
ls -la db_loja_*.sqlite3
```

### Verificar Usuário Criado
```bash
sqlite3 db_superadmin.sqlite3 "SELECT username, email, is_staff FROM auth_user WHERE username LIKE 'admin_%';"
```

---

## 🐛 PROBLEMAS COMUNS

### Erro: "lojas.map is not a function"
**Solução**: Já corrigido! O código agora verifica se é array antes de fazer map.

### Erro: "Authentication credentials not provided"
**Solução**: Fazer login novamente como superadmin.

### Erro: "Slug already exists"
**Solução**: Usar um slug diferente ou adicionar número no final.

### Erro: "Username already exists"
**Solução**: Usar um nome de usuário diferente.

### Modal não abre
**Solução**: 
1. Verificar console do navegador (F12)
2. Recarregar página
3. Fazer logout e login novamente

### Banco não é criado
**Solução**: O banco é criado automaticamente após criar a loja. Aguarde alguns segundos.

---

## 📊 RESULTADO ESPERADO

Após criar a loja com sucesso, você deve ver:

### Na Listagem de Lojas:
```
┌────────────────────────────────────────────────────────────┐
│ Loja              │ Tipo      │ Plano  │ Status │ Banco   │
├────────────────────────────────────────────────────────────┤
│ Tech Store Brasil │ E-commerce│ Básico │ Ativa  │ ✓ Criado│
│ admin_tech        │           │        │ Trial  │         │
└────────────────────────────────────────────────────────────┘
```

### No Sistema de Arquivos:
```
backend/
├── db_superadmin.sqlite3
├── db_suporte.sqlite3
├── db_loja_template.sqlite3
├── db_loja_loja_exemplo.sqlite3
└── db_loja_tech_store_brasil.sqlite3  ← NOVO!
```

### No Banco Superadmin:
```sql
-- Loja
id: 2
nome: Tech Store Brasil
slug: tech-store-brasil
cpf_cnpj: 12.345.678/9012-34
tipo_assinatura: mensal

-- Financeiro
loja_id: 2
valor_mensalidade: 49.90
dia_vencimento: 10
data_proxima_cobranca: 2026-02-10
```

### Login da Nova Loja:
```
URL: http://localhost:3000/loja/login?slug=tech-store-brasil
Tema: Verde (E-commerce)
Título: Tech Store Brasil
Usuário: admin_tech
Senha: tech123456
```

---

## 🎯 TESTE COMPLETO

### Cenário 1: Criar Loja E-commerce
1. ✅ Preencher formulário com dados do Exemplo 1
2. ✅ Clicar em "Criar Loja"
3. ✅ Aguardar mensagem de sucesso
4. ✅ Verificar loja na listagem
5. ✅ Acessar login da loja
6. ✅ Fazer login com credenciais criadas
7. ✅ Verificar dashboard carregando

### Cenário 2: Criar Loja de Serviços
1. ✅ Repetir processo com dados do Exemplo 2
2. ✅ Verificar tema azul no login
3. ✅ Verificar funcionalidades de serviços

### Cenário 3: Criar Restaurante
1. ✅ Repetir processo com dados do Exemplo 3
2. ✅ Verificar tema vermelho no login
3. ✅ Verificar assinatura anual no financeiro

---

## 📝 RELATÓRIO DE TESTE

Use este template para documentar seus testes:

```
Data: ___________
Testador: ___________

Teste 1: Criar Loja E-commerce
- Formulário preenchido: [ ] Sim [ ] Não
- Loja criada: [ ] Sim [ ] Não
- Banco criado: [ ] Sim [ ] Não
- Login funciona: [ ] Sim [ ] Não
- Observações: _______________________

Teste 2: Criar Loja de Serviços
- Formulário preenchido: [ ] Sim [ ] Não
- Loja criada: [ ] Sim [ ] Não
- Banco criado: [ ] Sim [ ] Não
- Login funciona: [ ] Sim [ ] Não
- Observações: _______________________

Teste 3: Criar Restaurante
- Formulário preenchido: [ ] Sim [ ] Não
- Loja criada: [ ] Sim [ ] Não
- Banco criado: [ ] Sim [ ] Não
- Login funciona: [ ] Sim [ ] Não
- Observações: _______________________

Problemas Encontrados:
1. _______________________
2. _______________________
3. _______________________

Status Final: [ ] Aprovado [ ] Reprovado
```

---

## 🎉 SUCESSO!

Se todos os testes passarem, você terá:

✅ Formulário completo com 8 campos funcionando  
✅ Criação automática de loja, financeiro e banco  
✅ Login personalizado por loja  
✅ Sistema multi-loja 100% operacional  

**Pronto para criar quantas lojas quiser! 🚀**
