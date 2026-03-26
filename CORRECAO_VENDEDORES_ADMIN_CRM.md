# Correção: Administrador não vinculado como Vendedor em Lojas CRM Vendas

## Problema Identificado

O sistema estava tentando criar um modelo `Funcionario` para lojas CRM Vendas, mas esse modelo não existe. O CRM Vendas usa o modelo `Vendedor` para gerenciar a equipe de vendas.

### Sintomas:
- Administrador não aparece na lista de funcionários/vendedores
- Problemas com permissões e filtros de vendas
- Erro ao acessar: https://lwksistemas.com.br/loja/{cnpj}/crm-vendas/configuracoes/funcionarios

### Lojas Afetadas:
- https://lwksistemas.com.br/loja/41449198000172/login (Felix Representações)
- https://lwksistemas.com.br/loja/38900437000154/login
- https://lwksistemas.com.br/loja/18275574000138/login

## Correções Implementadas

### 1. Signal Corrigido (v1343)
**Arquivo**: `backend/superadmin/signals.py` (linhas 238-252)

**Antes** (ERRADO):
```python
elif tipo_loja_nome == 'CRM Vendas':
    from crm_vendas.models import Funcionario  # ❌ Modelo não existe!
    
    if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
        funcionario_criado = Funcionario.objects.create(**funcionario_data)
```

**Depois** (CORRETO):
```python
elif tipo_loja_nome == 'CRM Vendas':
    from crm_vendas.models import Vendedor  # ✅ Modelo correto
    
    if not Vendedor.objects.filter(email=owner.email, loja_id=instance.id).exists():
        vendedor_data = {
            'nome': owner.get_full_name() or owner.username,
            'email': owner.email,
            'telefone': '',
            'cargo': 'Administrador',
            'is_admin': True,  # ✅ Marca como administrador
            'is_active': True,
            'loja_id': instance.id
        }
        funcionario_criado = Vendedor.objects.create(**vendedor_data)
```

### 2. Script de Correção Retroativa
**Arquivo**: `backend/corrigir_vendedores_admin_crm.py`

Script que:
- Busca todas as lojas CRM Vendas ativas
- Verifica se o owner existe como Vendedor
- Cria Vendedor com `is_admin=True` se não existir
- Atualiza vendedores existentes para `is_admin=True` se necessário

## Como Executar a Correção

### Opção 1: Via Heroku CLI (RECOMENDADO)

```bash
# 1. Fazer deploy das correções
git add backend/superadmin/signals.py backend/corrigir_vendedores_admin_crm.py
git commit -m "fix: Corrigir vinculação de administrador como Vendedor em CRM Vendas (v1343)"
git push heroku master

# 2. Executar script de correção no Heroku
heroku run python manage.py shell -c "from corrigir_vendedores_admin_crm import run; run()" --app lwksistemas-38ad47519238
```

### Opção 2: Via Console do Heroku (Interface Web)

1. Acessar: https://dashboard.heroku.com/apps/lwksistemas-38ad47519238
2. Clicar em "More" > "Run console"
3. Executar:
```bash
python manage.py shell
```
4. No shell Python, executar:
```python
from corrigir_vendedores_admin_crm import run
run()
```

### Opção 3: Via Django Admin (Mais Simples)

1. Acessar cada loja manualmente
2. Ir em Configurações > Vendedores
3. Adicionar o administrador manualmente como Vendedor com:
   - Nome: [Nome do admin]
   - Email: [Email do admin]
   - Cargo: Administrador
   - Is Admin: ✅ Marcado
   - Is Active: ✅ Marcado

## Verificação Pós-Correção

Para cada loja corrigida, verificar:

1. **Lista de Vendedores**:
   - Acessar: https://lwksistemas.com.br/loja/{cnpj}/crm-vendas/configuracoes/funcionarios
   - Verificar se administrador aparece na lista
   - Verificar se está marcado como "Administrador"

2. **Permissões**:
   - Testar acesso a todas as funcionalidades do CRM
   - Verificar se filtros de vendas funcionam corretamente
   - Confirmar que admin pode ver todas as oportunidades

3. **Logs do Sistema**:
```bash
heroku logs --tail --app lwksistemas-38ad47519238 | grep "Vendedor"
```

## Resultado Esperado

Após a correção, o script deve exibir:

```
🔍 Encontradas 3 lojas CRM Vendas ativas

📋 Processando loja: Felix Representações (ID: X, Slug: 41449198000172)
   Owner: admin@email.com (admin@email.com)
   🔧 Criando Vendedor admin...
   ✅ Vendedor admin criado: Admin Name (ID: Y)

============================================================
📊 RESUMO DA CORREÇÃO
============================================================
Total de lojas processadas: 3
Lojas corrigidas: 3
Lojas já corretas: 0
Erros: 0
============================================================
✅ Correção concluída com sucesso!
```

## Prevenção de Problemas Futuros

### Novas Lojas CRM Vendas
O signal corrigido (`backend/superadmin/signals.py`) garante que:
- Toda nova loja CRM Vendas criada terá o administrador automaticamente vinculado como Vendedor
- O vendedor será marcado com `is_admin=True`
- Não haverá mais tentativa de criar modelo `Funcionario` inexistente

### Testes Recomendados
Após o deploy, criar uma nova loja CRM Vendas de teste e verificar:
1. Loja é criada com sucesso
2. Administrador aparece automaticamente na lista de vendedores
3. Administrador tem acesso total ao sistema
4. Não há erros nos logs

## Arquivos Modificados

- ✅ `backend/superadmin/signals.py` (v1343)
- ✅ `backend/corrigir_vendedores_admin_crm.py` (novo)
- ✅ `CORRECAO_VENDEDORES_ADMIN_CRM.md` (documentação)

## Próximos Passos

1. ✅ Correção do signal implementada
2. ✅ Script de correção retroativa criado
3. ⏳ **PENDENTE**: Deploy no Heroku
4. ⏳ **PENDENTE**: Executar script de correção
5. ⏳ **PENDENTE**: Verificar lojas afetadas
6. ⏳ **PENDENTE**: Testar criação de nova loja CRM Vendas

## Notas Técnicas

### Diferença entre Funcionario e Vendedor

- **Funcionario**: Modelo usado em Clínica de Estética, Restaurante, Serviços, Cabeleireiro
- **Vendedor**: Modelo usado APENAS em CRM Vendas
- Ambos têm campos similares: nome, email, telefone, cargo, is_admin, is_active
- Vendedor tem campos adicionais: comissao_padrao

### Por que o erro aconteceu?

O signal original foi criado antes do CRM Vendas ser implementado. Quando o CRM foi adicionado, o desenvolvedor assumiu que teria um modelo `Funcionario` como os outros apps, mas o CRM usa `Vendedor` para representar a equipe de vendas.

### Impacto da Correção

- ✅ Sem breaking changes
- ✅ Compatível com lojas existentes
- ✅ Não afeta outros tipos de loja
- ✅ Correção retroativa segura (apenas cria, não deleta)
