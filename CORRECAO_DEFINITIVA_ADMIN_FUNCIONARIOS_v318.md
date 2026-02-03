# Correção Definitiva: Admin Não Aparece em Funcionários (v318)

## 🎯 PROBLEMA RESOLVIDO

Ao criar nova loja, o admin era criado no banco de dados mas **NÃO aparecia** no modal de funcionários.

## 🔍 CAUSA RAIZ

O problema estava nos ViewSets de funcionários (CRM Vendas, Clínica, Restaurante):

```python
class FuncionarioViewSet(BaseModelViewSet):
    queryset = Funcionario.objects.all()  # ❌ PROBLEMA!
    serializer_class = FuncionarioSerializer
```

**Por que isso causava o problema?**

1. O `queryset` definido como **atributo de classe** é avaliado quando a classe é carregada (no início do servidor)
2. Nesse momento, o middleware **ainda não setou** o `loja_id` no contexto
3. O `LojaIsolationManager` retorna queryset vazio quando não há `loja_id` no contexto
4. Esse queryset vazio fica "congelado" como atributo da classe
5. Mesmo que o middleware sete o contexto depois, o queryset já foi avaliado como vazio

## ✅ SOLUÇÃO APLICADA

Remover o atributo `queryset` da classe e obter o queryset **dinamicamente** no método `get_queryset()`:

```python
class FuncionarioViewSet(BaseModelViewSet):
    # ✅ SEM queryset como atributo de classe
    serializer_class = FuncionarioSerializer
    
    def get_queryset(self):
        """Obter queryset dinamicamente (não usar atributo de classe)"""
        loja_id = get_current_loja_id()
        
        if not loja_id:
            return Funcionario.objects.none()
        
        # Garantir que admin existe
        self._ensure_owner_funcionario()
        
        # ✅ Obter queryset AGORA (com contexto já setado)
        queryset = Funcionario.objects.filter(is_active=True)
        
        return queryset
```

## 📝 ARQUIVOS CORRIGIDOS

1. **backend/restaurante/views.py** (v318)
   - Removido `queryset = Funcionario.objects.all()`
   - Queryset obtido dinamicamente em `get_queryset()`

2. **backend/crm_vendas/views.py** (v318)
   - Removido `queryset = Vendedor.objects.all()`
   - Queryset obtido dinamicamente em `get_queryset()`

3. **backend/clinica_estetica/views.py** (v318)
   - Removido `queryset = Funcionario.objects.all()`
   - Queryset obtido dinamicamente em `get_queryset()`

## 🧪 TESTE

1. Criar nova loja de qualquer tipo (CRM Vendas, Clínica, Restaurante)
2. Abrir o modal de funcionários
3. ✅ O admin da loja deve aparecer automaticamente na lista

## 🎓 LIÇÃO APRENDIDA

**NUNCA use `queryset` como atributo de classe quando o modelo usa `LojaIsolationManager`!**

O contexto de loja só é setado pelo middleware **durante a requisição**, então o queryset deve ser obtido dinamicamente no método `get_queryset()`.

## 📊 VERSÕES

- **v316**: Primeira tentativa - forçar avaliação com `list(queryset)` (funcionou parcialmente)
- **v317**: Adicionar logs detalhados (diagnóstico)
- **v318**: Correção definitiva - obter queryset dinamicamente ✅

## ✅ STATUS

**PROBLEMA RESOLVIDO DEFINITIVAMENTE**

Agora ao criar qualquer nova loja, o admin aparecerá automaticamente na lista de funcionários sem erros.
