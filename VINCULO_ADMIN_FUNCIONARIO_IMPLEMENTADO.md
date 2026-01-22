# ✅ VÍNCULO AUTOMÁTICO ADMINISTRADOR → FUNCIONÁRIO

## 📋 RESUMO DA IMPLEMENTAÇÃO

Implementei um sistema que **vincula automaticamente o administrador da loja como funcionário** quando uma nova loja é criada. Esta funcionalidade funciona para **todos os tipos de loja** do sistema.

## 🎯 PROBLEMA IDENTIFICADO

Quando uma loja era criada, o administrador (owner) **NÃO** era automaticamente vinculado como funcionário/vendedor da loja, o que causava:
- Impossibilidade de atribuir tarefas ao administrador
- Falta de registro do administrador nas listas de funcionários
- Necessidade de cadastro manual do administrador como funcionário

## ✅ SOLUÇÃO IMPLEMENTADA

### 1. Adição do Campo `user` aos Modelos

**Modelos Atualizados:**

#### BaseFuncionario (core/models.py)
```python
user = models.OneToOneField(
    'auth.User', 
    on_delete=models.CASCADE, 
    null=True, 
    blank=True, 
    related_name='%(app_label)s_%(class)s',
    help_text='Usuário do sistema vinculado ao funcionário'
)
```

#### Funcionario - Clínica Estética
```python
user = models.OneToOneField(
    User, 
    on_delete=models.CASCADE, 
    null=True, 
    blank=True, 
    related_name='clinica_funcionario'
)
```

### 2. Signal Centralizado no Superadmin

**Arquivo:** `backend/superadmin/signals.py`

O signal `create_funcionario_for_loja_owner` é acionado automaticamente quando uma loja é criada e:

1. Detecta o tipo de loja
2. Cria o funcionário/vendedor apropriado
3. Vincula ao usuário administrador
4. Define cargo padrão baseado no tipo de loja

### 3. Tipos de Loja Suportados

| Tipo de Loja | Modelo | Cargo Padrão | Campos Extras |
|--------------|--------|--------------|---------------|
| **Clínica de Estética** | `Funcionario` | Administrador | - |
| **Serviços** | `Funcionario` | Administrador | - |
| **Restaurante** | `Funcionario` | Gerente | - |
| **CRM Vendas** | `Vendedor` | Gerente de Vendas | meta_mensal: R$ 10.000 |
| **E-commerce** | - | - | Não possui funcionários |

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### Migrations Criadas

```bash
✅ clinica_estetica/migrations/0004_funcionario_user.py
✅ crm_vendas/migrations/0003_vendedor_user.py
✅ restaurante/migrations/0003_funcionario_user.py
✅ servicos/migrations/0003_funcionario_user_alter_cliente_email_and_more.py
```

### Signal Automático

```python
@receiver(post_save, sender='superadmin.Loja')
def create_funcionario_for_loja_owner(sender, instance, created, **kwargs):
    """
    Cria automaticamente um funcionário/vendedor para o administrador
    quando uma loja é criada
    """
    if not created:
        return
    
    # Detecta tipo de loja e cria funcionário apropriado
    # ...
```

### Relacionamento User ↔ Funcionário

```
User (Django Auth)
    ↓ OneToOne
Funcionario/Vendedor
    ↓ Dados
- nome: user.get_full_name() ou user.username
- email: user.email
- cargo: Baseado no tipo de loja
- telefone: '' (preenchido posteriormente)
```

## 📊 SCRIPT DE MIGRAÇÃO

**Arquivo:** `backend/vincular_admins_funcionarios.py`

Script para vincular administradores de **lojas existentes** como funcionários:

```bash
python backend/vincular_admins_funcionarios.py
```

**O que o script faz:**
1. Lista todas as lojas existentes
2. Verifica se o administrador já é funcionário
3. Cria funcionário se não existir
4. Exibe relatório completo

**Saída esperada:**
```
🔄 Vinculando administradores como funcionários...
============================================================

📋 Loja: Clínica Felix
   Tipo: Clínica de Estética
   Admin: felipe
   ✅ Funcionário criado

============================================================
📊 RESUMO
============================================================
Total de lojas processadas: 1
✅ Funcionários criados: 1
ℹ️  Funcionários já existentes: 0
❌ Erros: 0
============================================================
```

## 🚀 COMO FUNCIONA

### Para Novas Lojas

1. **Superadmin cria loja** via API `/api/superadmin/lojas/`
2. **Signal é acionado** automaticamente
3. **Funcionário é criado** com dados do administrador
4. **Administrador pode ser usado** em agendamentos, vendas, etc.

### Para Lojas Existentes

1. **Executar script** `vincular_admins_funcionarios.py`
2. **Aplicar migrations** se ainda não aplicadas
3. **Verificar funcionários** criados

## 🧪 COMO TESTAR

### 1. Testar Criação de Nova Loja

```bash
# Fazer login como superadmin
TOKEN=$(curl -s -X POST "https://lwksistemas-38ad47519238.herokuapp.com/api/auth/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "senha"}' | jq -r '.access')

# Criar nova loja de clínica
curl -X POST "https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Clínica Teste",
    "slug": "clinica-teste",
    "tipo_loja": 1,
    "plano": 1,
    "tipo_assinatura": "mensal",
    "owner_username": "admin_clinica",
    "owner_email": "admin@clinica.com",
    "dia_vencimento": 10
  }'

# Verificar se funcionário foi criado
curl -H "Authorization: Bearer $TOKEN" \
  "https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/funcionarios/"
```

### 2. Verificar Funcionário na Interface

1. **Acesse:** https://lwksistemas.com.br/loja/felix/dashboard
2. **Login:** felipe / 147Luiz@
3. **Navegue:** Menu → Funcionários (se disponível)
4. **Verifique:** Administrador deve aparecer na lista

### 3. Testar em Agendamentos

1. **Crie um agendamento** na clínica
2. **Selecione profissional:** Administrador deve aparecer
3. **Confirme:** Agendamento pode ser atribuído ao admin

## 📝 BENEFÍCIOS DA IMPLEMENTAÇÃO

### ✅ Automação
- Funcionário criado automaticamente
- Sem necessidade de cadastro manual
- Processo transparente para o usuário

### ✅ Consistência
- Todos os tipos de loja seguem o mesmo padrão
- Dados sincronizados entre User e Funcionário
- Relacionamento OneToOne garante unicidade

### ✅ Flexibilidade
- Campo `user` é opcional (null=True, blank=True)
- Funcionários podem existir sem usuário
- Usuários podem ter múltiplos papéis

### ✅ Rastreabilidade
- Logs detalhados de criação
- Erros não interrompem criação da loja
- Fácil identificação de problemas

## ⚠️ CONSIDERAÇÕES IMPORTANTES

### Migrations Pendentes

**IMPORTANTE:** As migrations precisam ser aplicadas em produção:

```bash
# No Heroku
heroku run python manage.py migrate --app lwksistemas

# Ou localmente
python backend/manage.py migrate
```

### Lojas Existentes

Para lojas já criadas, executar o script de migração:

```bash
# No Heroku
heroku run python vincular_admins_funcionarios.py --app lwksistemas

# Ou localmente
python backend/vincular_admins_funcionarios.py
```

### E-commerce

O tipo de loja **E-commerce** não possui modelo de funcionário, portanto:
- Não cria funcionário automaticamente
- Administrador gerencia apenas via painel admin
- Pode ser implementado futuramente se necessário

## 🔄 PRÓXIMOS PASSOS SUGERIDOS

- [ ] Aplicar migrations em produção
- [ ] Executar script para lojas existentes
- [ ] Testar criação de novas lojas
- [ ] Verificar funcionários em agendamentos
- [ ] Adicionar testes automatizados
- [ ] Documentar para usuários finais

## 📚 ARQUIVOS MODIFICADOS

```
backend/
├── core/models.py                          # Campo user em BaseFuncionario
├── clinica_estetica/models.py              # Campo user em Funcionario
├── clinica_estetica/apps.py                # Removido signal local
├── superadmin/signals.py                   # Signal centralizado (NOVO)
├── superadmin/apps.py                      # Já registra signals
├── vincular_admins_funcionarios.py         # Script de migração (NOVO)
└── migrations/
    ├── clinica_estetica/0004_*.py
    ├── crm_vendas/0003_*.py
    ├── restaurante/0003_*.py
    └── servicos/0003_*.py
```

---

**Data de Implementação:** 22 de Janeiro de 2026  
**Versão:** v1.2.0  
**Status:** ✅ IMPLEMENTADO - Aguardando aplicação de migrations