# Correção: Adiciona Funcionalidade de Excluir Oportunidade (v1023)

**Data**: 18/03/2026  
**Versão**: v1023  
**Status**: ✅ IMPLEMENTADO

---

## 🔴 PROBLEMA

No pipeline de vendas (`https://lwksistemas.com.br/loja/22239255889/crm-vendas/pipeline`), não havia opção para excluir oportunidades.

### Comportamento Observado

1. ✅ Criar oportunidade funcionava
2. ✅ Editar oportunidade (etapa, comissão, datas) funcionava
3. ❌ **NÃO havia opção de excluir oportunidade**

---

## 🔍 ANÁLISE

### Modal de Edição Incompleto

O modal de edição de oportunidade tinha apenas:
- Campo para alterar etapa
- Campo para alterar valor da comissão
- Campos para datas de fechamento
- Botões: "Cancelar" e "Salvar"

**Faltava**: Botão de excluir oportunidade

### Backend Já Suportava Exclusão

O `OportunidadeViewSet` já tinha o método `destroy()` herdado do `BaseModelViewSet`, que faz soft delete (marca como `is_active=False`).

---

## ✅ SOLUÇÃO IMPLEMENTADA

### Modificações no Frontend

Adicionado funcionalidade de exclusão no modal de edição de oportunidade:

1. **Novo estado**: `modalExcluir` para controlar confirmação de exclusão
2. **Novo botão**: "Excluir" no modal de edição
3. **Modal de confirmação**: Pergunta se o usuário tem certeza antes de excluir
4. **Função de exclusão**: `handleExcluirOportunidade()` que chama a API DELETE

### Fluxo de Exclusão

1. Usuário clica no card da oportunidade no pipeline
2. Modal de edição abre
3. Usuário clica no botão "Excluir"
4. Modal muda para modo de confirmação
5. Usuário confirma a exclusão
6. API DELETE é chamada
7. Oportunidade é removida (soft delete)
8. Lista de oportunidades é recarregada

### Código Implementado

```typescript
// Estado para controlar modal de exclusão
const [modalExcluir, setModalExcluir] = useState(false);

// Função para excluir oportunidade
const handleExcluirOportunidade = async () => {
  if (!oportunidadeEditar) return;
  setEnviando(true);
  try {
    await apiClient.delete(`/crm-vendas/oportunidades/${oportunidadeEditar.id}/`);
    setOportunidadeEditar(null);
    setModalExcluir(false);
    loadOportunidades(setOportunidades, setError);
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } } };
    setFormErro(e.response?.data?.detail || 'Erro ao excluir oportunidade.');
  } finally {
    setEnviando(false);
  }
};

// Botões no modal
{!modalExcluir ? (
  <div className="flex gap-2">
    <button type="button" onClick={() => setOportunidadeEditar(null)}>
      Cancelar
    </button>
    <button type="button" onClick={() => setModalExcluir(true)}>
      Excluir
    </button>
    <button type="submit">
      Salvar
    </button>
  </div>
) : (
  <div className="space-y-4">
    <p>Tem certeza que deseja excluir a oportunidade "{oportunidadeEditar.titulo}"?</p>
    <div className="flex gap-2">
      <button type="button" onClick={() => setModalExcluir(false)}>
        Cancelar
      </button>
      <button type="button" onClick={handleExcluirOportunidade}>
        Confirmar exclusão
      </button>
    </div>
  </div>
)}
```

---

## 📋 ARQUIVOS MODIFICADOS

### Frontend

- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/pipeline/page.tsx`
  - Adicionado estado `modalExcluir`
  - Adicionado função `handleExcluirOportunidade()`
  - Modificado modal de edição para incluir botão "Excluir"
  - Adicionado modal de confirmação de exclusão

---

## 🚀 DEPLOY

### Frontend (Vercel)

```bash
cd /caminho/do/projeto
git add frontend/app/\(dashboard\)/loja/\[slug\]/crm-vendas/pipeline/page.tsx
git commit -m "feat(crm): adiciona funcionalidade de excluir oportunidade no pipeline (v1023)"
cd frontend
vercel --prod --yes
```

**Deploy concluído**: ✅ https://lwksistemas.com.br (18/03/2026 11:45)

---

## ✅ RESULTADO

1. ✅ Criar oportunidade funciona
2. ✅ Editar oportunidade funciona
3. ✅ **Excluir oportunidade funciona** (com confirmação)
4. ✅ Soft delete: oportunidade é marcada como `is_active=False` (não é deletada do banco)

---

## 🔒 SEGURANÇA

### Soft Delete

O backend usa soft delete (`is_active=False`) em vez de deletar fisicamente do banco:

```python
def destroy(self, request, *args, **kwargs):
    """Soft delete - marca como inativo ao invés de deletar"""
    instance = self.get_object()
    if hasattr(instance, 'is_active'):
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        return super().destroy(request, *args, **kwargs)
```

### Permissões

- ✅ Vendedores podem excluir apenas suas próprias oportunidades
- ✅ Proprietário (owner) pode excluir qualquer oportunidade da loja
- ✅ Filtro de vendedor aplicado automaticamente via `VendedorFilterMixin`

---

## 📝 FUNCIONALIDADES DO PIPELINE

### Criar Oportunidade

1. Clicar em "Nova oportunidade"
2. Selecionar lead
3. Preencher título, valor, etapa
4. Adicionar produtos/serviços (opcional)
5. Definir comissão (opcional)
6. Salvar

### Editar Oportunidade

1. Clicar no card da oportunidade
2. Alterar etapa (mover no pipeline)
3. Alterar valor da comissão
4. Definir datas de fechamento
5. Salvar

### Excluir Oportunidade

1. Clicar no card da oportunidade
2. Clicar em "Excluir"
3. Confirmar exclusão
4. Oportunidade é removida do pipeline

---

## 🔗 REFERÊNCIAS

- Correção anterior: `CORRECAO_PRODUTOS_NAO_APARECEM_v1022.md`
- Permissões owner: `CORRECAO_PERMISSOES_OWNER_v1020.md`
- Vinculação admin-vendedor: `ANALISE_ADMIN_NAO_VINCULADO_VENDEDOR.md`
