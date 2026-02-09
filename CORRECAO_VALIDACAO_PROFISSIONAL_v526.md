# Correção de Validação de Profissional no Bloqueio de Agenda - v526

## Problema Identificado

Frontend estava enviando `profissional_id` inválido ao criar bloqueio:
- **Loja 114** tem apenas 1 profissional: ID 43
- **Frontend enviava**: `profissional: 4` (não existe na loja)
- **Erro**: `IntegrityError: Key (profissional_id)=(4) is not present in table "clinica_profissionais"`

### Causa Raiz
O modal de bloqueio inicializava o campo `profissional` com o valor do filtro `profissionalSelecionado`, que podia conter IDs de outras lojas ou valores antigos do cache do navegador.

## Correções Implementadas

### 1. Backend - Validação no Serializer
**Arquivo**: `backend/clinica_estetica/serializers.py`

Adicionado método `validate_profissional()` no `BloqueioAgendaSerializer`:
```python
def validate_profissional(self, value):
    """Valida se o profissional existe na loja atual"""
    if value is None:
        return value
    
    # Pegar loja_id do contexto
    request = self.context.get('request')
    if not request or not hasattr(request, 'loja_id'):
        raise serializers.ValidationError("Contexto de loja não encontrado")
    
    loja_id = request.loja_id
    
    # Verificar se profissional existe na loja
    if not Profissional.objects.filter(id=value.id, loja_id=loja_id).exists():
        raise serializers.ValidationError(
            f"Profissional ID {value.id} não existe na loja atual (ID {loja_id}). "
            f"Verifique se o profissional está cadastrado nesta loja."
        )
    
    return value
```

**Benefícios**:
- ✅ Retorna erro 400 com mensagem clara antes de tentar salvar no banco
- ✅ Previne `IntegrityError` no PostgreSQL
- ✅ Informa qual profissional e qual loja causou o problema

### 2. Frontend - Correção do Estado Inicial
**Arquivo**: `frontend/components/calendario/CalendarioAgendamentos.tsx`

**Antes**:
```typescript
const [formData, setFormData] = useState({
  profissional: profissionalSelecionado || '', // ❌ Usava filtro (pode ser inválido)
  // ...
});
```

**Depois**:
```typescript
const [formData, setFormData] = useState({
  profissional: '', // ✅ Sempre vazio - usuário escolhe explicitamente
  // ...
});
```

**Benefícios**:
- ✅ Usuário deve escolher profissional explicitamente
- ✅ Não herda valores inválidos do filtro
- ✅ Evita confusão entre filtro de visualização e bloqueio específico

## Deploy Realizado

### Backend (Heroku)
```bash
git commit -m "v526: Adicionar validação de profissional no BloqueioAgenda + corrigir frontend"
git push heroku master
```
- ✅ Deploy v519 concluído
- ✅ Migrations aplicadas
- ✅ Validação ativa

### Frontend (Vercel)
```bash
vercel --prod --cwd frontend --yes
```
- ✅ Deploy concluído
- ✅ URL: https://lwksistemas.com.br

## Teste Recomendado

1. Acessar: https://lwksistemas.com.br/loja/teste-5889/dashboard
2. Clicar em "Bloquear Horário"
3. **Verificar**: Campo "Profissional" deve estar vazio (não pré-selecionado)
4. Tentar criar bloqueio sem selecionar profissional → ✅ Deve funcionar (bloqueio geral)
5. Selecionar profissional válido (ID 43) → ✅ Deve funcionar
6. Se tentar enviar ID inválido via API → ❌ Deve retornar erro 400 com mensagem clara

## Impacto

- ✅ **Todas as lojas**: Correção funciona para todas as 6 lojas de clínica
- ✅ **Isolamento multi-tenant**: Validação garante que profissional pertence à loja
- ✅ **UX melhorada**: Usuário escolhe explicitamente ao invés de valor pré-selecionado
- ✅ **Erros mais claros**: Mensagem de validação informa exatamente o problema

## Arquivos Modificados

1. `backend/clinica_estetica/serializers.py` - Validação de profissional
2. `frontend/components/calendario/CalendarioAgendamentos.tsx` - Estado inicial vazio
