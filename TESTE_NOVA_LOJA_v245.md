# 🧪 TESTE NOVA LOJA v245 - Criação Automática de Funcionário

## Objetivo
Testar se o signal cria automaticamente o funcionário quando uma nova loja é criada.

## Passos para Criar Nova Loja

### 1. Acessar Painel Superadmin
```
https://lwksistemas.com.br/superadmin/dashboard
```

### 2. Clicar em "Criar Nova Loja"

### 3. Preencher Dados da Loja
- **Nome**: (escolher um nome)
- **Slug**: (será gerado automaticamente)
- **Tipo de Loja**: Clínica de Estética (ou outro tipo)
- **Plano**: Escolher um plano
- **Proprietário**: Selecionar usuário

### 4. Salvar

## Verificações Após Criação

### 1. Verificar Logs do Heroku
```bash
heroku logs --tail | grep -E "(Funcionário|funcionario|Signal)"
```

**Log esperado**:
```
✅ Funcionário admin criado automaticamente: [nome] para loja [nome_loja] (Clínica de Estética)
```

### 2. Verificar no Banco de Dados
```bash
heroku run python backend/manage.py shell
```

```python
from superadmin.models import Loja
from clinica_estetica.models import Funcionario

# Buscar a loja recém-criada
loja = Loja.objects.last()
print(f"Loja: {loja.nome} (ID: {loja.id})")

# Buscar funcionários da loja
funcionarios = Funcionario.objects.all_without_filter().filter(loja_id=loja.id)
print(f"Funcionários: {funcionarios.count()}")

for func in funcionarios:
    print(f"  - {func.nome} ({func.email}) - Admin: {func.is_admin}")
```

### 3. Verificar no Dashboard da Loja
```
https://lwksistemas.com.br/loja/[slug]/dashboard
```

1. Fazer login com o usuário proprietário
2. Clicar no botão rosa "👥 Funcionários"
3. Verificar se o funcionário aparece com badge "👤 Administrador"

## Resultados Esperados

### ✅ Signal Executado
- Log mostra criação do funcionário
- Sem erros no log

### ✅ Funcionário Criado
- Existe no banco de dados
- `is_admin = True`
- `loja_id` correto
- Nome e email do proprietário

### ✅ Dashboard Funciona
- Modal abre sem erros
- Funcionário aparece na lista
- Badge "👤 Administrador" visível
- Botão "Excluir" não aparece para admin

## Comandos Úteis

### Verificar Última Loja Criada
```bash
heroku run python backend/manage.py shell
```
```python
from superadmin.models import Loja
loja = Loja.objects.last()
print(f"ID: {loja.id}, Nome: {loja.nome}, Slug: {loja.slug}")
```

### Verificar Funcionários da Loja
```bash
heroku run python backend/manage.py shell
```
```python
from clinica_estetica.models import Funcionario
from superadmin.models import Loja

loja = Loja.objects.last()
funcionarios = Funcionario.objects.all_without_filter().filter(loja_id=loja.id)

for func in funcionarios:
    print(f"ID: {func.id}, Nome: {func.nome}, Email: {func.email}, Admin: {func.is_admin}")
```

### Criar Funcionário Manualmente (se necessário)
```bash
heroku run python backend/manage.py shell
```
```python
from clinica_estetica.models import Funcionario
from superadmin.models import Loja

loja = Loja.objects.last()
owner = loja.owner

funcionario = Funcionario.objects.create(
    nome=owner.get_full_name() or owner.username,
    email=owner.email,
    telefone='',
    cargo='Administrador',
    is_admin=True,
    loja_id=loja.id
)
print(f"✅ Funcionário criado: {funcionario.nome}")
```

## Troubleshooting

### Problema: Funcionário não foi criado
**Possíveis causas**:
1. Signal não foi carregado
2. Erro durante a criação
3. Tipo de loja não suportado

**Solução**:
1. Verificar logs do Heroku
2. Executar comando manual de criação
3. Verificar se o tipo de loja está no signal

### Problema: Funcionário não aparece no dashboard
**Possíveis causas**:
1. `X-Loja-ID` não está sendo enviado
2. Middleware não está setando contexto
3. Cache do navegador

**Solução**:
1. Limpar cache do navegador
2. Verificar console do navegador (F12)
3. Verificar logs do Heroku para ver se middleware está funcionando

### Problema: Erro ao abrir modal
**Possíveis causas**:
1. API retornando erro
2. CORS bloqueando requisição
3. Autenticação falhando

**Solução**:
1. Verificar console do navegador
2. Verificar logs do Heroku
3. Testar API diretamente

## Dados para Teste

### Loja de Teste Sugerida
- **Nome**: Clínica Teste
- **Tipo**: Clínica de Estética
- **Plano**: Básico
- **Proprietário**: Seu usuário

### Após Criação
- **URL**: https://lwksistemas.com.br/loja/clinica-teste/dashboard
- **Login**: Seu email e senha
- **Funcionário**: Deve aparecer automaticamente

## Checklist de Teste

- [ ] Loja criada com sucesso
- [ ] Log mostra criação de funcionário
- [ ] Funcionário existe no banco
- [ ] `is_admin = True`
- [ ] `loja_id` correto
- [ ] Dashboard abre sem erros
- [ ] Modal de funcionários abre
- [ ] Funcionário aparece na lista
- [ ] Badge "👤 Administrador" visível
- [ ] Botão "Excluir" não aparece para admin
- [ ] Pode criar novos funcionários
- [ ] Pode editar funcionários
- [ ] Pode excluir funcionários (exceto admin)

## Próximos Passos Após Teste

Se tudo funcionar:
1. ✅ Sistema está funcionando corretamente
2. ✅ Pode criar lojas normalmente
3. ✅ Funcionários são criados automaticamente

Se houver problemas:
1. Verificar logs
2. Executar comando de correção
3. Reportar erro para análise
