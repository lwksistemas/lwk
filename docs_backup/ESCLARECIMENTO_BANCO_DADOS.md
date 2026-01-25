# 🔍 Esclarecimento: Banco de Dados do Sistema

**Data**: 17/01/2026  
**Importante**: Correção de informações

---

## ❓ Pergunta do Usuário

> "O banco de dados do Heroku não é o PostgreSQL? O sistema está usando banco SQL?"

---

## ✅ Resposta: Sistema Usa SQLite (Não PostgreSQL)

### Banco de Dados Atual

```
┌─────────────────────────────────────────┐
│  BANCO DE DADOS REAL                    │
├─────────────────────────────────────────┤
│  Tipo:         SQLite 3                 │
│  Localização:  Heroku (arquivos)        │
│  Arquivos:     db_*.sqlite3             │
│  Custo:        $0 (incluído no Heroku)  │
└─────────────────────────────────────────┘
```

### Arquivos de Banco

```bash
backend/
├── db_superadmin.sqlite3      # Banco principal
├── db_suporte.sqlite3         # Banco de suporte
├── db_loja_harmonis.sqlite3   # Banco da loja Harmonis
├── db_loja_felix.sqlite3      # Banco da loja Felix
└── ...
```

---

## 🤔 Por Que SQLite e Não PostgreSQL?

### Heroku Oferece Ambos

O Heroku oferece:
1. **PostgreSQL** (recomendado para produção)
2. **SQLite** (arquivos locais, mais simples)

### Escolhemos SQLite Por:

```
✅ Simplicidade
   - Zero configuração
   - Não precisa de servidor separado
   - Arquivo único por banco

✅ Custo Zero
   - PostgreSQL Heroku: $0-50/mês
   - SQLite: $0 (incluído)

✅ Suficiente para Começar
   - Até 40-50 lojas
   - Até 50 requisições/segundo
   - Bom para MVP/início

⚠️ Limitações
   - Não escala para 100+ lojas
   - Sem replicação
   - Sem backup automático
   - Concorrência limitada
```

---

## 📊 Comparação: SQLite vs PostgreSQL

| Característica | SQLite (Atual) | PostgreSQL (Heroku) |
|----------------|----------------|---------------------|
| **Custo** | $0 | $0-50/mês |
| **Configuração** | Zero | Média |
| **Capacidade** | 40-50 lojas | 1000+ lojas |
| **Concorrência** | ~50 req/seg | 1000+ req/seg |
| **Backup** | Manual | Automático |
| **Replicação** | ❌ Não | ✅ Sim |
| **Full-text Search** | Limitado | ✅ Completo |
| **Ideal para** | MVP, início | Produção, escala |

---

## 🔄 Quando Migrar para PostgreSQL?

### Sinais de Que Precisa Migrar

```
⚠️ Migrar quando:
✅ 40+ lojas ativas
✅ 1000+ requisições/minuto
✅ Timeouts frequentes
✅ Erros de "database locked"
✅ Precisar de backup automático
✅ Precisar de replicação
✅ Precisar de full-text search
```

### Custo da Migração

```
PostgreSQL Heroku:
- Hobby Dev:     $0/mês (10.000 linhas, 20 conexões)
- Hobby Basic:   $9/mês (10M linhas, 20 conexões)
- Standard 0:    $50/mês (64GB, 120 conexões)

Recomendação Inicial: Hobby Basic ($9/mês)
```

---

## 💡 Recomendação Atual

### Para Agora (0-40 lojas)

```
✅ MANTER SQLite

Motivos:
- Sistema está funcionando bem
- Custo zero
- Suficiente para capacidade atual
- Otimizações já implementadas
- Fácil de gerenciar
```

### Para o Futuro (40+ lojas)

```
🔄 MIGRAR para PostgreSQL

Quando:
- Atingir 40 lojas ativas
- Começar a ter problemas de performance
- Precisar de backup automático
- Quiser escalar para 100+ lojas

Custo adicional: $9/mês (Hobby Basic)
```

---

## 🛠️ Como Migrar (Quando Necessário)

### Passo a Passo

```bash
# 1. Adicionar PostgreSQL no Heroku
heroku addons:create heroku-postgresql:hobby-basic

# 2. Obter URL do banco
heroku config:get DATABASE_URL

# 3. Atualizar settings.py
# Usar dj-database-url para configurar

# 4. Fazer backup do SQLite
python manage.py dumpdata > backup.json

# 5. Migrar para PostgreSQL
python manage.py migrate

# 6. Importar dados
python manage.py loaddata backup.json

# 7. Testar
python manage.py check

# 8. Deploy
git push heroku master
```

---

## 📋 Configuração Atual vs Ideal

### Configuração Atual (SQLite)

```python
# backend/config/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_superadmin.sqlite3',
        'CONN_MAX_AGE': 600,
    }
}
```

**Custo**: $0  
**Capacidade**: 40-50 lojas  
**Ideal para**: MVP, início, desenvolvimento

### Configuração Futura (PostgreSQL)

```python
# backend/config/settings.py
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://user:pass@host:5432/dbname',
        conn_max_age=600,
        ssl_require=True
    )
}
```

**Custo**: $9/mês (Hobby Basic)  
**Capacidade**: 100+ lojas  
**Ideal para**: Produção, escala

---

## 💰 Impacto no Custo Total

### Custo Atual (SQLite)

```
Vercel Pro:       $20/mês
Heroku Hobby:     $7/mês
Domínio:          $3/mês
PostgreSQL:       $0/mês (usando SQLite)
─────────────────────────
TOTAL:            $30/mês (R$ 150/mês)
```

### Custo Futuro (PostgreSQL)

```
Vercel Pro:       $20/mês
Heroku Hobby:     $7/mês
Domínio:          $3/mês
PostgreSQL:       $9/mês (Hobby Basic)
─────────────────────────
TOTAL:            $39/mês (R$ 195/mês)

Aumento: +$9/mês (+30%)
```

---

## 🎯 Conclusão

### Situação Atual

```
✅ Sistema usa SQLite (não PostgreSQL)
✅ Funciona bem para 40-50 lojas
✅ Custo zero
✅ Suficiente para agora
```

### Plano de Ação

```
AGORA (0-40 lojas):
✅ Manter SQLite
✅ Monitorar performance
✅ Economizar $9/mês

FUTURO (40+ lojas):
🔄 Migrar para PostgreSQL
💰 Investir $9/mês adicional
🚀 Escalar para 100+ lojas
```

### Recomendação

**MANTER SQLite por enquanto**. Migrar para PostgreSQL apenas quando:
1. Atingir 40+ lojas ativas
2. Começar a ter problemas de performance
3. Precisar de recursos avançados (backup automático, replicação)

**Economia atual**: $9/mês ($108/ano)

---

**Atualizado em**: 17/01/2026  
**Status**: SQLite funcionando bem  
**Próxima revisão**: Quando atingir 30 lojas
