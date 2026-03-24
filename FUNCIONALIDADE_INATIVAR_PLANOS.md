# Funcionalidade: Inativar/Ocultar Planos

## Status: ✅ JÁ IMPLEMENTADO

A funcionalidade de inativar planos para que não apareçam na lista de cadastro público já está completamente implementada no sistema.

## Como Funciona

### 1. Campo `is_active` no Modelo PlanoAssinatura

O modelo `PlanoAssinatura` já possui o campo `is_active` (boolean):
- **Ativo (true)**: Plano aparece na lista de cadastro público
- **Inativo (false)**: Plano fica oculto na lista de cadastro público

### 2. Filtro na API Pública

**Arquivo**: `backend/superadmin/views.py`

```python
class PlanoAssinaturaPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet público para listar planos de assinatura (somente leitura)"""
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        # Retornar apenas planos ativos
        return PlanoAssinatura.objects.filter(is_active=True).order_by('preco_mensal')
```

A API pública `/api/public/planos/` já filtra automaticamente apenas planos com `is_active=True`.

### 3. Interface do Superadmin

#### Admin Django
**URL**: https://lwksistemas.com.br/admin/superadmin/planoassinatura/

O campo `is_active` está disponível para edição no admin do Django:
- Aparece na listagem (`list_display`)
- Pode ser filtrado (`list_filter`)
- Pode ser editado no formulário

#### Frontend React (Superadmin)
**URL**: https://lwksistemas.com.br/superadmin/planos

**Componentes**:
1. **PlanoCard** (`frontend/components/superadmin/planos/PlanoCard.tsx`)
   - Mostra badge "Inativo" quando `!plano.is_active`
   - Badge vermelho: `bg-red-100 text-red-800`

2. **ModalNovoPlano** (`frontend/components/superadmin/planos/ModalNovoPlano.tsx`)
   - Checkbox "✅ Plano Ativo" para ativar/desativar
   - Campo `is_active` no formulário (linha 424-432)
   - Valor padrão: `true` (ativo)

## Como Usar

### Opção 1: Admin Django (Recomendado)

1. Acesse: https://lwksistemas.com.br/admin/superadmin/planoassinatura/
2. Clique no plano que deseja inativar
3. Desmarque o checkbox "Is active"
4. Clique em "Salvar"

### Opção 2: Frontend Superadmin

1. Acesse: https://lwksistemas.com.br/superadmin/planos
2. Selecione o tipo de sistema
3. Clique em "Editar" no plano desejado
4. Desmarque o checkbox "✅ Plano Ativo"
5. Clique em "Salvar Alterações"

## Resultado

Quando um plano é inativado:

1. **Página de Cadastro Público** (https://lwksistemas.com.br/cadastro)
   - O plano NÃO aparece na lista de seleção
   - Apenas planos ativos são exibidos

2. **Lojas Existentes**
   - Lojas que já usam o plano continuam funcionando normalmente
   - O plano continua aparecendo no superadmin para gerenciamento

3. **Superadmin**
   - O plano continua visível na lista (com badge "Inativo")
   - Pode ser reativado a qualquer momento
   - Pode ser editado normalmente

## Exemplo de Uso

### Cenário: Descontinuar plano "Básico"

1. Você quer parar de oferecer o plano "Básico" para novos clientes
2. Mas quer manter as lojas existentes que já usam esse plano

**Solução**:
1. Inative o plano "Básico" (marcar `is_active=False`)
2. Novos cadastros não verão mais esse plano
3. Lojas existentes continuam funcionando normalmente

### Cenário: Lançar novo plano temporariamente

1. Você quer testar um novo plano antes de lançar oficialmente
2. Crie o plano com `is_active=False`
3. Teste internamente
4. Quando estiver pronto, ative o plano (`is_active=True`)

## Arquivos Relacionados

### Backend
- `backend/superadmin/models.py` - Modelo PlanoAssinatura com campo `is_active`
- `backend/superadmin/views.py` - ViewSet público com filtro `is_active=True`
- `backend/superadmin/admin.py` - Admin Django com campo editável

### Frontend
- `frontend/components/superadmin/planos/PlanoCard.tsx` - Badge "Inativo"
- `frontend/components/superadmin/planos/ModalNovoPlano.tsx` - Checkbox "Plano Ativo"
- `frontend/components/cadastro/FormularioCadastroLoja.tsx` - Lista apenas planos ativos

## Observações

- ✅ Funcionalidade já está 100% implementada
- ✅ Não requer nenhuma alteração de código
- ✅ Não requer migração de banco de dados
- ✅ Pronto para uso imediato
- ✅ Planos inativos não aparecem no cadastro público
- ✅ Planos inativos continuam visíveis no superadmin
- ✅ Lojas existentes não são afetadas

## Conclusão

A funcionalidade solicitada já existe e está funcionando perfeitamente. Basta usar o checkbox "Is active" no admin do Django ou "✅ Plano Ativo" no frontend do superadmin para ativar/desativar planos.
