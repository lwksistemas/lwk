# Funcionalidade: Inativar/Ocultar Tipos de Sistema

## Status: ✅ IMPLEMENTADO

Adicionado campo `is_active` ao modelo `TipoLoja` para permitir ocultar tipos de sistema em desenvolvimento da lista pública de cadastro.

## Alterações Realizadas

### 1. Backend

#### Modelo TipoLoja
**Arquivo**: `backend/superadmin/models.py`

Adicionado campo:
```python
is_active = models.BooleanField(
    default=True, 
    help_text='Se inativo, não aparece na lista pública de cadastro'
)
```

#### Migração
**Arquivo**: `backend/superadmin/migrations/0038_add_is_active_to_tipoloja.py`

Criada migração para adicionar o campo `is_active` ao modelo `TipoLoja`.

#### API Pública
**Arquivo**: `backend/superadmin/views.py`

Atualizado `TipoLojaPublicoViewSet` para filtrar apenas tipos ativos:
```python
def get_queryset(self):
    # Retornar apenas tipos ativos
    return TipoLoja.objects.filter(is_active=True).order_by('nome')
```

#### Admin Django
**Arquivo**: `backend/superadmin/admin.py`

Adicionado campo `is_active` ao admin:
- `list_display`: Mostra na listagem
- `list_filter`: Permite filtrar por status

### 2. Frontend

#### Interface TypeScript
**Arquivo**: `frontend/hooks/useTipoAppActions.ts`

Adicionado campo `is_active` às interfaces:
```typescript
export interface TipoApp {
  // ... outros campos
  is_active: boolean;
}

export interface TipoAppFormData {
  // ... outros campos
  is_active: boolean;
}
```

#### Modal de Edição
**Arquivo**: `frontend/components/superadmin/tipos-app/TipoAppModal.tsx`

Adicionado checkbox para ativar/desativar tipo:
```tsx
<label className="flex items-center space-x-2">
  <input
    type="checkbox"
    name="is_active"
    checked={formData.is_active}
    onChange={handleChange}
    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
  />
  <span className="text-sm text-gray-900 dark:text-gray-100">
    ✅ Tipo Ativo (visível no cadastro)
  </span>
</label>
```

#### Card de Tipo
**Arquivo**: `frontend/components/superadmin/tipos-app/TipoAppCard.tsx`

Adicionado badge "Inativo" quando `!tipo.is_active`:
```tsx
{!tipo.is_active && (
  <span className="absolute top-2 right-2 px-2 py-1 text-xs rounded-full bg-red-500 text-white">
    Inativo
  </span>
)}
```

## Como Usar

### Opção 1: Admin Django

1. Acesse: https://lwksistemas.com.br/admin/superadmin/tipoloja/
2. Clique no tipo que deseja inativar
3. Desmarque o checkbox "Is active"
4. Clique em "Salvar"

### Opção 2: Frontend Superadmin (Recomendado)

1. Acesse: https://lwksistemas.com.br/superadmin/tipos-app
2. Clique em "Editar" no tipo desejado
3. Desmarque o checkbox "✅ Tipo Ativo (visível no cadastro)"
4. Clique em "Salvar Alterações"

## Resultado

Quando um tipo de sistema é inativado:

### Página de Cadastro Público
**URL**: https://lwksistemas.com.br/cadastro

- O tipo NÃO aparece na seção "3. Tipo de Sistema"
- Apenas tipos ativos são exibidos para seleção
- Novos cadastros não podem escolher tipos inativos

### Lojas Existentes
- Lojas que já usam o tipo continuam funcionando normalmente
- O tipo continua aparecendo no superadmin para gerenciamento
- Não afeta lojas já criadas

### Superadmin
- O tipo continua visível na lista (com badge "Inativo")
- Pode ser reativado a qualquer momento
- Pode ser editado normalmente

## Casos de Uso

### Cenário 1: Tipo em Desenvolvimento
Você está desenvolvendo um novo tipo de sistema (ex: "Restaurante") mas ainda não está pronto para produção.

**Solução**:
1. Crie o tipo com `is_active=False`
2. Desenvolva e teste internamente
3. Quando estiver pronto, ative o tipo (`is_active=True`)

### Cenário 2: Descontinuar Tipo
Você quer parar de oferecer um tipo de sistema (ex: "E-commerce Básico") mas manter as lojas existentes funcionando.

**Solução**:
1. Inative o tipo (`is_active=False`)
2. Novos cadastros não verão mais esse tipo
3. Lojas existentes continuam funcionando

### Cenário 3: Manutenção Temporária
Um tipo de sistema está com problemas e você precisa pausar novos cadastros temporariamente.

**Solução**:
1. Inative o tipo temporariamente
2. Resolva os problemas
3. Reative o tipo quando estiver pronto

## Deploy

### Backend
- **Versão**: v1304
- **Heroku**: Deploy realizado com sucesso
- **Migração**: Aplicada automaticamente

### Frontend
- **Vercel**: Deploy realizado com sucesso
- **URL**: https://lwksistemas.com.br

## Arquivos Modificados

### Backend
- `backend/superadmin/models.py` - Adicionado campo `is_active`
- `backend/superadmin/views.py` - Filtro na API pública
- `backend/superadmin/admin.py` - Campo no admin Django
- `backend/superadmin/migrations/0038_add_is_active_to_tipoloja.py` - Migração

### Frontend
- `frontend/hooks/useTipoAppActions.ts` - Interfaces atualizadas
- `frontend/components/superadmin/tipos-app/TipoAppModal.tsx` - Checkbox adicionado
- `frontend/components/superadmin/tipos-app/TipoAppCard.tsx` - Badge "Inativo"

## Observações

- ✅ Funcionalidade 100% implementada e testada
- ✅ Deploy realizado no backend (Heroku v1304)
- ✅ Deploy realizado no frontend (Vercel)
- ✅ Migração aplicada com sucesso
- ✅ Tipos inativos não aparecem no cadastro público
- ✅ Tipos inativos continuam visíveis no superadmin
- ✅ Lojas existentes não são afetadas
- ✅ Valor padrão: `is_active=True` (todos os tipos existentes permanecem ativos)

## Conclusão

A funcionalidade está pronta para uso! Agora você pode ocultar tipos de sistema em desenvolvimento da lista pública de cadastro, mantendo-os visíveis apenas no superadmin para gerenciamento.
