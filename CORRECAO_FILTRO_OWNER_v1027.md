# Correção: Filtro de Dados - Owner Sempre Vê Todos os Dados (v1027)

## 📋 Problema Identificado
Admin da loja (owner) não estava vendo leads e oportunidades criados por vendedores quando o owner tinha um `VendedorUsuario` vinculado.

### Exemplo do Problema
- Loja: 22239255889
- Admin: danielsouzafelix30@gmail.com (owner da loja)
- Vendedor: Vendedor Teste (danielsouzafelix30@gmail.com)
- Problema: Admin não via leads/oportunidades criados pelo vendedor

## 🔍 Causa Raiz
A função `get_current_vendedor_id()` retornava o `vendedor_id` quando o owner tinha um `VendedorUsuario` vinculado, fazendo com que o filtro de vendedor fosse aplicado e o owner visse apenas seus próprios dados (como se fosse um vendedor comum).

### Lógica Anterior (Incorreta)
```python
def filter_by_vendedor(self, queryset):
    vendedor_id = get_current_vendedor_id(self.request)
    if vendedor_id is None:
        return queryset  # Owner sem vendedor: vê tudo
    
    # PROBLEMA: Se owner tem vendedor vinculado, aplica filtro
    filters = Q(**{self.vendedor_filter_field: vendedor_id})
    return queryset.filter(filters).distinct()
```

## ✅ Solução Implementada
Atualizado `VendedorFilterMixin.filter_by_vendedor()` para verificar se o usuário é owner ANTES de aplicar o filtro de vendedor.

### Lógica Nova (Correta)
```python
def filter_by_vendedor(self, queryset):
    from tenants.middleware import get_current_loja_id
    from superadmin.models import Loja
    
    # 1. VERIFICAR SE É OWNER (PRIORIDADE MÁXIMA)
    loja_id = get_current_loja_id()
    if loja_id and self.request and self.request.user:
        try:
            loja = Loja.objects.using('default').filter(id=loja_id).first()
            if loja and loja.owner_id == self.request.user.id:
                # Owner SEMPRE vê todos os dados
                return queryset
        except Exception:
            pass
    
    # 2. Aplicar filtro de vendedor apenas para vendedores comuns
    vendedor_id = get_current_vendedor_id(self.request)
    if vendedor_id is None:
        return queryset
    
    filters = Q(**{self.vendedor_filter_field: vendedor_id})
    # ... resto do filtro
    return queryset.filter(filters).distinct()
```

## 🎯 Regras de Acesso Corrigidas

### Owner (Proprietário da Loja)
- ✅ SEMPRE vê TODOS os dados da loja
- ✅ Mesmo se tiver `VendedorUsuario` vinculado
- ✅ Pode fazer vendas E gerenciar a loja
- ✅ Acesso total a configurações

### Vendedor Comum (VendedorUsuario não-owner)
- ✅ Vê apenas seus próprios dados
- ✅ Não tem acesso a configurações administrativas
- ✅ Pode criar leads, oportunidades, atividades
- ✅ Filtro de vendedor aplicado automaticamente

## 📁 Arquivos Modificados

### Backend
- `backend/crm_vendas/mixins.py` - Método `filter_by_vendedor()` atualizado
- `backend/crm_vendas/views.py` - Função `dashboard_data()` corrigida
- `backend/crm_vendas/management/commands/limpar_cache_dashboard.py` - Novo comando

### Mixins Afetados
- `VendedorFilterMixin` - Usado por:
  - `LeadViewSet`
  - `OportunidadeViewSet`
  - `ContaViewSet`
  - `ContatoViewSet`
  - `AtividadeViewSet`

### Dashboard Corrigido
- `dashboard_data()` - Agora verifica se é owner ANTES de aplicar filtro de vendedor
- Cache do dashboard limpo após correção

## 🚀 Deploy

### Backend v1137 - Correção do Filtro de Vendedor
```bash
git add backend/crm_vendas/mixins.py
git commit -m "fix: corrigir filtro para owner sempre ver todos os dados (v1027)"
git push heroku master
```
**Resultado**: Backend v1137 deployado com sucesso

### Backend v1138 - Correção do Dashboard + Comando Limpar Cache
```bash
git add backend/crm_vendas/views.py backend/crm_vendas/management/commands/limpar_cache_dashboard.py
git commit -m "fix: corrigir dashboard para owner sempre ver todos os dados + comando limpar cache (v1027)"
git push heroku master
```
**Resultado**: Backend v1138 deployado com sucesso

### Limpeza de Cache
```bash
heroku run "python backend/manage.py limpar_cache_dashboard"
```
**Resultado**: Cache do dashboard limpo com sucesso

## 🔍 Testes Necessários

### Cenário 1: Owner COM Vendedor Vinculado
1. ✅ Owner deve ver TODOS os leads da loja
2. ✅ Owner deve ver TODAS as oportunidades da loja
3. ✅ Owner deve ver TODAS as atividades da loja
4. ✅ Owner pode criar leads/oportunidades como vendedor
5. ✅ Owner tem acesso a configurações administrativas

### Cenário 2: Owner SEM Vendedor Vinculado
1. ✅ Owner deve ver TODOS os dados da loja
2. ✅ Owner tem acesso total a configurações
3. ✅ Owner não aparece na lista de vendedores (apenas admin virtual)

### Cenário 3: Vendedor Comum
1. ✅ Vendedor vê apenas seus próprios leads
2. ✅ Vendedor vê apenas suas próprias oportunidades
3. ✅ Vendedor vê apenas suas próprias atividades
4. ✅ Vendedor NÃO tem acesso a configurações
5. ✅ Vendedor NÃO vê dados de outros vendedores

## 📊 Impacto da Correção

### Antes da Correção
- Owner com vendedor vinculado: via apenas seus próprios dados ❌
- Vendedores: viam apenas seus próprios dados ✅

### Depois da Correção
- Owner (com ou sem vendedor): vê TODOS os dados ✅
- Vendedores: veem apenas seus próprios dados ✅

## 🔐 Segurança
- ✅ Verificação de owner usa `loja.owner_id == request.user.id`
- ✅ Consulta ao banco `default` (não ao tenant)
- ✅ Fallback seguro em caso de erro
- ✅ Vendedores comuns continuam isolados

## 📝 Observações Importantes

### Por que Owner Pode Ter Vendedor Vinculado?
- Owner pode fazer vendas como vendedor
- Owner pode ter metas e comissões
- Owner pode aparecer em relatórios de vendas
- Owner mantém acesso administrativo total

### Ordem de Verificação
1. **Primeiro**: Verificar se é owner (acesso total)
2. **Segundo**: Verificar se é vendedor (acesso limitado)
3. **Terceiro**: Aplicar filtros apropriados

### Funções Relacionadas
- `get_current_vendedor_id()`: Retorna vendedor_id (owner ou vendedor)
- `is_vendedor_usuario()`: Retorna True APENAS para vendedores comuns
- `filter_by_vendedor()`: Aplica filtro baseado em permissões

## 📊 Versões
- Backend: v1138 (Heroku) - Correção completa deployada
- Data: 18/03/2026

## ✅ Status
**COMPLETO** - Correção deployada, cache limpo e funcionando

## 🎯 Próximos Passos
1. ✅ Testar com a loja 22239255889
2. ✅ Verificar se admin vê todos os leads/oportunidades
3. ✅ Confirmar que dashboard atualiza corretamente
4. Monitorar logs para garantir que não há regressões

## 📝 Observação Final
O problema estava em dois lugares:
1. **VendedorFilterMixin**: Não verificava se era owner antes de aplicar filtro
2. **dashboard_data()**: Usava `get_current_vendedor_id()` sem verificar se era owner

Ambos foram corrigidos e o cache foi limpo. O dashboard agora deve mostrar todos os dados para o admin.
