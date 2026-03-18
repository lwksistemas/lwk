# Diagnóstico: Migrations não criam tabelas no schema - v1001

**Data**: 17/03/2026  
**Problema**: Migrations rodam sem erro, search_path está correto, mas tabelas não são criadas

---

## 🔍 SINTOMAS

```
✅ search_path da conexão: loja_41449198000172, public
✅ Migrations aplicadas: stores
✅ Migrations aplicadas: products
✅ Migrations aplicadas: crm_vendas
❌ Schema 'loja_41449198000172' está VAZIO após migrations!
⚠️  Nenhuma tabela encontrada em 'public' para mover
```

---

## 🤔 HIPÓTESES

### 1. Django migrate cria nova conexão
O `call_command('migrate')` pode criar uma nova conexão que não passa pelo `init_connection_state()` do nosso backend customizado.

### 2. Migrations já aplicadas
As migrations podem já estar marcadas como aplicadas no `django_migrations`, então o Django pula a criação das tabelas.

### 3. Backend não está sendo usado
O ENGINE pode não estar sendo reconhecido corretamente pelo Django.

---

## 🔧 PRÓXIMOS PASSOS

1. Verificar se as migrations estão marcadas como aplicadas na tabela `django_migrations`
2. Testar se o backend está sendo usado com um teste direto de conexão
3. Verificar se `call_command('migrate')` respeita o ENGINE configurado
4. Considerar usar `--run-syncdb` para forçar criação de tabelas

---

## 💡 SOLUÇÃO PROPOSTA

Usar `call_command('migrate', '--run-syncdb')` para forçar a criação das tabelas, ou limpar a tabela `django_migrations` antes de rodar as migrations.
