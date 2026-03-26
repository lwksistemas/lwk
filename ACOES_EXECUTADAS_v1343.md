# Ações Executadas - v1343: Correção Administrador CRM Vendas

## Data: 2026-03-26

## Problema Reportado

Erro grave ao criar lojas CRM Vendas: o administrador não está sendo vinculado na lista de funcionários.

### Sintomas:
- Administrador não aparece em: https://lwksistemas.com.br/loja/{cnpj}/crm-vendas/configuracoes/funcionarios
- Problemas com permissões e filtros de vendas
- Administrador também aparece como vendedor (causando conflitos)

### Lojas Afetadas:
1. https://lwksistemas.com.br/loja/41449198000172/login (Felix Representações)
2. https://lwksistemas.com.br/loja/38900437000154/login
3. https://lwksistemas.com.br/loja/18275574000138/login

## Análise do Problema

### Causa Raiz Identificada

O signal `create_funcionario_for_loja_owner` em `backend/superadmin/signals.py` estava tentando criar um modelo `Funcionario` para lojas CRM Vendas, mas esse modelo NÃO EXISTE no CRM Vendas.

**Código problemático** (linhas 238-245):
```python
elif tipo_loja_nome == 'CRM Vendas':
    from crm_vendas.models import Funcionario  # ❌ ERRO: Modelo não existe!
    
    if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
        funcionario_criado = Funcionario.objects.create(**funcionario_data)
```

### Estrutura do CRM Vendas

O CRM Vendas usa o modelo `Vendedor` (não `Funcionario`) para gerenciar a equipe:

```python
class Vendedor(LojaIsolationMixin, models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=100, default='Vendedor')
    comissao_padrao = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_admin = models.BooleanField(default=False)  # ✅ Campo para marcar admin
    is_active = models.BooleanField(default=True)
```

## Correções Implementadas

### 1. Correção do Signal (v1343)

**Arquivo**: `backend/superadmin/signals.py`
**Linhas**: 238-252

**Alteração**:
```python
elif tipo_loja_nome == 'CRM Vendas':
    # CRM Vendas: admin (owner) é criado como Vendedor com is_admin=True
    # Isso permite que o admin apareça na lista de funcionários e tenha acesso total
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
        logger.info(f"✅ Vendedor Administrador criado para CRM Vendas: {funcionario_criado.nome}")
```

**Impacto**: Novas lojas CRM Vendas criadas a partir de agora terão o administrador automaticamente vinculado como Vendedor.

### 2. Script de Correção Retroativa

**Arquivo**: `backend/corrigir_vendedores_admin_crm.py` (NOVO)

**Funcionalidade**:
- Busca todas as lojas CRM Vendas ativas no sistema
- Para cada loja, verifica se o owner existe como Vendedor
- Se não existir, cria Vendedor com `is_admin=True`
- Se existir mas não estiver marcado como admin, atualiza para `is_admin=True`

**Uso**:
```bash
# Via Heroku CLI
heroku run python manage.py shell -c "from corrigir_vendedores_admin_crm import run; run()" --app lwksistemas-38ad47519238

# Via Django Shell
python manage.py shell
>>> from corrigir_vendedores_admin_crm import run
>>> run()
```

### 3. Documentação Completa

**Arquivo**: `CORRECAO_VENDEDORES_ADMIN_CRM.md` (NOVO)

Documentação detalhada incluindo:
- Descrição do problema
- Análise técnica
- Instruções de correção
- Verificação pós-correção
- Prevenção de problemas futuros

## Arquivos Modificados

1. ✅ `backend/superadmin/signals.py` - Signal corrigido
2. ✅ `backend/corrigir_vendedores_admin_crm.py` - Script de correção (NOVO)
3. ✅ `CORRECAO_VENDEDORES_ADMIN_CRM.md` - Documentação (NOVO)
4. ✅ `ACOES_EXECUTADAS_v1343.md` - Este arquivo (NOVO)

## Próximos Passos (PENDENTES)

### 1. Deploy no Heroku
```bash
git add .
git commit -m "fix: Corrigir vinculação de administrador como Vendedor em CRM Vendas (v1343)"
git push heroku master
```

### 2. Executar Script de Correção
```bash
heroku run python manage.py shell -c "from corrigir_vendedores_admin_crm import run; run()" --app lwksistemas-38ad47519238
```

### 3. Verificar Lojas Afetadas

Para cada loja, verificar:
- Administrador aparece na lista de vendedores
- Está marcado como "Administrador"
- Tem acesso total ao sistema
- Filtros e permissões funcionam corretamente

**URLs para verificar**:
- https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes/funcionarios
- https://lwksistemas.com.br/loja/38900437000154/crm-vendas/configuracoes/funcionarios
- https://lwksistemas.com.br/loja/18275574000138/crm-vendas/configuracoes/funcionarios

### 4. Testar Criação de Nova Loja

Criar uma nova loja CRM Vendas de teste e verificar:
1. Loja é criada com sucesso
2. Administrador aparece automaticamente na lista de vendedores
3. Administrador tem `is_admin=True`
4. Não há erros nos logs

## Resultado Esperado

Após deploy e execução do script:

1. ✅ Todas as 3 lojas afetadas terão o administrador vinculado como Vendedor
2. ✅ Administrador terá acesso total ao CRM
3. ✅ Filtros e permissões funcionarão corretamente
4. ✅ Novas lojas CRM Vendas não terão mais esse problema

## Notas Técnicas

### Por que o erro aconteceu?

O signal original foi criado antes do CRM Vendas ser implementado. Quando o CRM foi adicionado, assumiu-se que teria um modelo `Funcionario` como os outros apps (Clínica de Estética, Restaurante, Serviços), mas o CRM usa `Vendedor` para representar a equipe de vendas.

### Diferença entre Funcionario e Vendedor

| Característica | Funcionario | Vendedor |
|---------------|-------------|----------|
| Apps que usam | Clínica, Restaurante, Serviços | CRM Vendas |
| Campos comuns | nome, email, telefone, cargo | nome, email, telefone, cargo |
| Campo admin | is_admin | is_admin |
| Campos específicos | data_admissao | comissao_padrao |

### Impacto da Correção

- ✅ Sem breaking changes
- ✅ Compatível com lojas existentes
- ✅ Não afeta outros tipos de loja
- ✅ Correção retroativa segura (apenas cria, não deleta)
- ✅ Signal corrigido previne problema em novas lojas

## Logs Relevantes

Após executar o script, espera-se ver nos logs:

```
🔍 Encontradas 3 lojas CRM Vendas ativas

📋 Processando loja: Felix Representações (ID: X, Slug: 41449198000172)
   Owner: admin@email.com
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

## Versão

- **Versão**: v1343
- **Data**: 2026-03-26
- **Tipo**: Correção crítica (bugfix)
- **Prioridade**: Alta
- **Status**: Implementado, aguardando deploy

## Referências

- Issue original: Administrador não vinculado em lojas CRM Vendas
- Lojas afetadas: 3 lojas (41449198000172, 38900437000154, 18275574000138)
- Modelo correto: `crm_vendas.models.Vendedor`
- Signal corrigido: `backend/superadmin/signals.py:238-252`
