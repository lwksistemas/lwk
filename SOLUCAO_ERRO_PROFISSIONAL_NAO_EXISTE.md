# 🐛 Solução: Erro "Profissional não existe" no Agendamento

**Data:** 05/02/2026  
**Erro:** `POST /api/cabeleireiro/agendamentos/ 400 (Bad Request)`  
**Mensagem:** "profissional não existe"

## 🎯 Causa do Problema

O modelo `Agendamento` no backend ainda usa a tabela **Profissional** (antiga):

```python
# backend/cabeleireiro/models.py
class Agendamento(models.Model):
    profissional = models.ForeignKey('Funcionario', ...)  # ✅ Atualizado no código
    # MAS a tabela no banco ainda aponta para Profissional (antigo)
```

**Problema:** 
- Frontend envia ID de `Funcionario` (ex: ID 2)
- Backend procura na tabela `Profissional` (antiga)
- Não encontra e retorna erro 400

## ✅ Solução Imediata (Sem Deploy Backend)

### Opção 1: Migrar Funcionários para Profissionais

Execute este script no servidor Heroku:

```bash
# Conectar ao Heroku
heroku run bash -a lwksistemas

# Criar arquivo Python
cat > migrar.py << 'EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from cabeleireiro.models import Funcionario, Profissional

# Buscar funcionários profissionais
funcionarios = Funcionario.objects.filter(funcao='profissional')
print(f"Encontrados {funcionarios.count()} funcionários")

for func in funcionarios:
    # Verificar se já existe
    existe = Profissional.objects.filter(
        loja_id=func.loja_id,
        email=func.email
    ).first()
    
    if existe:
        print(f"Já existe: {func.nome}")
        continue
    
    # Criar profissional
    prof = Profissional.objects.create(
        loja_id=func.loja_id,
        nome=func.nome,
        email=func.email,
        telefone=func.telefone,
        especialidade=func.especialidade or 'Geral',
        comissao_percentual=func.comissao_percentual,
        is_active=func.is_active
    )
    print(f"Criado: {func.nome} (ID: {prof.id})")

print("Concluído!")
EOF

# Executar
python migrar.py
```

### Opção 2: Cadastrar Manualmente

1. Acessar: https://lwksistemas.com.br/loja/salao-000172/dashboard
2. Ir em "Ações Rápidas" → "Funcionários"
3. Para cada funcionário profissional (ex: Nayara Souza):
   - Anotar: Nome, Email, Telefone, Especialidade, Comissão
4. **Temporariamente**, criar um registro na tabela antiga via Django Admin ou SQL

## 🔧 Solução Definitiva (Requer Deploy Backend)

### 1. Criar Migração Django

```bash
cd backend
python manage.py makemigrations cabeleireiro --name migrar_profissional_para_funcionario
```

### 2. Editar Migração

A migração deve:
1. Criar nova coluna `funcionario_id` em `Agendamento`
2. Copiar dados de `profissional_id` → `funcionario_id` (mapear IDs)
3. Remover coluna `profissional_id`
4. Renomear `funcionario_id` → `profissional_id`

### 3. Aplicar Migração

```bash
python manage.py migrate cabeleireiro
```

### 4. Deploy

```bash
git add .
git commit -m "feat: Migrar Agendamento.profissional para usar Funcionario"
git push heroku master
```

## 📊 Verificar Dados Atuais

### Ver Funcionários Profissionais:

```python
from cabeleireiro.models import Funcionario
funcionarios = Funcionario.objects.filter(funcao='profissional')
for f in funcionarios:
    print(f"ID: {f.id}, Nome: {f.nome}, Loja: {f.loja_id}")
```

### Ver Profissionais (Tabela Antiga):

```python
from cabeleireiro.models import Profissional
profissionais = Profissional.objects.all()
for p in profissionais:
    print(f"ID: {p.id}, Nome: {p.nome}, Loja: {p.loja_id}")
```

## 🎯 Solução Rápida para Testar AGORA

**Criar profissional via Django Shell no Heroku:**

```bash
heroku run python manage.py shell -a lwksistemas
```

```python
from cabeleireiro.models import Funcionario, Profissional

# Buscar funcionário
func = Funcionario.objects.get(nome='Nayara Souza')

# Criar profissional correspondente
prof = Profissional.objects.create(
    loja_id=func.loja_id,
    nome=func.nome,
    email=func.email,
    telefone=func.telefone,
    especialidade=func.especialidade or 'Geral',
    comissao_percentual=func.comissao_percentual,
    is_active=True
)

print(f"Profissional criado! ID: {prof.id}")
```

Depois disso, o agendamento deve funcionar!

## 📝 Resumo

**Problema:** Backend usa tabela `Profissional` (antiga), frontend envia ID de `Funcionario` (nova)

**Solução Imediata:** Criar registros na tabela `Profissional` para cada funcionário profissional

**Solução Definitiva:** Migração do banco de dados para usar apenas `Funcionario`

---

**Status:** ⚠️ SOLUÇÃO TEMPORÁRIA NECESSÁRIA  
**Próximo:** 🔄 MIGRAÇÃO COMPLETA DO BANCO
