# Solução: Isolamento de Dados entre Lojas - v483

## ✅ Situação Atual

O sistema **JÁ TEM** isolamento de dados por loja usando **SQLite com bancos separados**:

```
backend/
├── db_superadmin.sqlite3          (dados do superadmin)
├── db_suporte.sqlite3             (dados do suporte)
├── db_loja_template.sqlite3       (template vazio)
├── db_loja_clinica_harmonis_5898.sqlite3  (loja de teste)
└── db_loja_NOVA_LOJA.sqlite3      (deve ser criado vazio)
```

## 🎯 Objetivo

Quando criar uma **nova loja de clínica de estética**, ela deve vir:
- ✅ **Completamente vazia** (sem clientes, procedimentos, agendamentos)
- ✅ **Apenas com admin/funcionário** criado automaticamente
- ✅ **Banco de dados próprio** (`db_loja_NOME.sqlite3`)

## 📋 O que NÃO fazer

- ❌ **NÃO copiar** dados da loja de teste (clinica-harmonis-5898)
- ❌ **NÃO usar** o banco `db_loja_template.sqlite3` com dados
- ❌ **NÃO compartilhar** banco entre lojas

## ✅ O que fazer

### 1. Garantir que cada loja tem seu próprio banco

Quando criar uma nova loja, o sistema deve:

```python
# Ao criar loja no superadmin
loja = Loja.objects.create(
    nome="Nova Clínica",
    slug="nova-clinica-123",
    database_name="loja_nova_clinica_123",  # Nome único
    tipo_loja=tipo_clinica,
    # ...
)

# O middleware vai criar/usar o banco:
# backend/db_loja_nova_clinica_123.sqlite3
```

### 2. Criar banco vazio (sem dados)

O banco deve ser criado com:
- ✅ Estrutura de tabelas (migrations)
- ✅ Admin/funcionário da loja
- ❌ SEM clientes
- ❌ SEM procedimentos
- ❌ SEM agendamentos

### 3. Verificar isolamento

Cada loja deve acessar apenas seu próprio banco:

```python
# Loja A acessa: db_loja_a.sqlite3
# Loja B acessa: db_loja_b.sqlite3
# Loja C acessa: db_loja_c.sqlite3
```

## 🔍 Como Verificar se está Funcionando

### Teste 1: Criar Nova Loja
```
1. Criar nova loja "Clínica Teste"
2. Verificar que arquivo db_loja_clinica_teste_XXX.sqlite3 foi criado
3. Acessar dashboard da nova loja
4. ✅ Dashboard deve estar vazio
5. ✅ Sem clientes, procedimentos ou agendamentos
```

### Teste 2: Isolamento entre Lojas
```
1. Adicionar cliente na Loja A
2. Acessar Loja B
3. ✅ Cliente da Loja A NÃO deve aparecer na Loja B
```

### Teste 3: Loja de Teste
```
1. Acessar clinica-harmonis-5898
2. ✅ Deve ter seus próprios dados
3. ✅ Dados NÃO devem aparecer em outras lojas
```

## 🛠️ Comandos Úteis

### Listar bancos de lojas
```bash
cd backend
ls -lh db_loja_*.sqlite3
```

### Verificar tamanho dos bancos
```bash
cd backend
du -h db_loja_*.sqlite3
```

### Verificar qual banco a loja está usando
```python
from superadmin.models import Loja

loja = Loja.objects.get(slug='nova-clinica')
print(f"Database: {loja.database_name}")
print(f"Criado: {loja.database_created}")
```

## 📝 Resumo

**O sistema JÁ TEM isolamento correto!**

Se uma nova loja está mostrando dados de outra loja, o problema pode ser:

1. **Banco não foi criado** → Loja está usando banco de outra loja
2. **database_name duplicado** → Duas lojas com mesmo database_name
3. **Middleware não está funcionando** → Não está trocando de banco

**Solução:** Verificar que cada loja tem um `database_name` único e que o arquivo `.sqlite3` correspondente existe.

---

**Última atualização:** 08/02/2026  
**Versão:** v483  
**Status:** ✅ Sistema já tem isolamento - apenas garantir que funciona
