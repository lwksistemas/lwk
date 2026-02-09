# Análise do Problema de Cache - v535

## Problema Confirmado

O usuário mostrou a tela "Gerenciar Profissionais" da loja `teste-5889` (ID 114) que tem apenas **2 profissionais**:
1. **Marina Souza** - Fisioterapeuta
2. **Nayara** - Dermatologista

Porém, os logs mostram que o frontend está enviando `profissional_id=4`:

```
[BloqueioAgenda] Dados recebidos: {'profissional': 4, ...}
Key (profissional_id)=(4) is not present in table "clinica_profissionais"
```

## Causa Raiz: Cache do Navegador

O frontend está com **cache desatualizado**. Quando o usuário carregou a página pela primeira vez, pode ter estado em outra loja ou o sistema pode ter tido profissionais diferentes. O navegador armazenou em cache:
- A lista de profissionais com IDs antigos (4, 5, etc.)
- O JavaScript compilado com dados antigos

Quando o usuário seleciona "Marina Souza" no dropdown, o frontend envia o ID 4 (que é o ID antigo/incorreto), mas o backend espera o ID real da Marina na loja atual.

## Arquitetura Multi-Tenant

O sistema usa `django-tenants` com schemas PostgreSQL separados:
- **Schema público**: Contém metadados e referências
- **Schema da loja** (`loja_teste_5889`): Contém dados isolados

Cada schema tem sua própria tabela `clinica_profissionais` com **IDs independentes**. O ID 4 pode existir em outra loja, mas não existe no schema `loja_teste_5889`.

## Solução Imediata

**INSTRUIR O USUÁRIO A LIMPAR O CACHE:**

### Opção 1: Hard Refresh (Mais Rápido)
1. Pressionar `Ctrl + Shift + R` (Windows/Linux)
2. Ou `Cmd + Shift + R` (Mac)
3. Isso força o navegador a recarregar todos os recursos sem usar cache

### Opção 2: Limpar Cache Manualmente
1. Abrir DevTools (F12)
2. Clicar com botão direito no botão de reload
3. Selecionar "Limpar cache e recarregar forçadamente"

### Opção 3: Aba Anônima
1. Abrir uma aba anônima/privada
2. Acessar https://lwksistemas.com.br/loja/teste-5889/dashboard
3. Testar criar bloqueio

## Verificação Após Limpar Cache

Após limpar o cache, o usuário deve:

1. **Abrir DevTools** (F12) → Aba "Network"
2. **Acessar** a página de calendário
3. **Verificar** a requisição para `/api/clinica/profissionais/`
4. **Confirmar** que os IDs retornados são os corretos

Exemplo esperado:
```json
[
  {"id": 123, "nome": "Marina Souza", "especialidade": "Fisioterapeuta"},
  {"id": 124, "nome": "Nayara", "especialidade": "Dermatologista"}
]
```

5. **Tentar criar bloqueio** selecionando Marina
6. **Verificar** na aba Network que o payload enviado tem o ID correto (123, não 4)

## Solução Permanente: Melhorias no Frontend

### 1. Adicionar Cache-Busting
**Arquivo**: `frontend/next.config.js`

Adicionar hash aos arquivos estáticos para forçar reload quando houver mudanças:

```javascript
module.exports = {
  generateBuildId: async () => {
    return `build-${Date.now()}`
  }
}
```

### 2. Adicionar Headers de Cache
**Arquivo**: `frontend/lib/api-client.ts`

Adicionar headers para evitar cache de APIs:

```typescript
const clinicaApiClient = axios.create({
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
});
```

### 3. Validação no Frontend
**Arquivo**: `frontend/components/calendario/CalendarioAgendamentos.tsx`

Adicionar validação antes de enviar:

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  // Validar que o profissional existe na lista carregada
  if (formData.profissional) {
    const profissionalExiste = profissionais.some(
      p => p.id === parseInt(formData.profissional)
    );
    
    if (!profissionalExiste) {
      alert('❌ Erro: Profissional inválido. Por favor, recarregue a página.');
      return;
    }
  }
  
  // ... resto do código
};
```

## Solução Permanente: Melhorias no Backend

### 1. Validação Mais Robusta
**Arquivo**: `backend/clinica_estetica/serializers.py`

A validação atual verifica o `loja_id` do objeto carregado, mas o DRF pode carregar do schema errado. Precisamos consultar diretamente:

```python
def validate(self, data):
    """Valida se o profissional existe na loja atual"""
    profissional_id = data.get('profissional')
    
    if profissional_id is not None:
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        
        if not loja_id:
            raise serializers.ValidationError({
                'profissional': "Contexto de loja não encontrado"
            })
        
        # Consultar diretamente no schema da loja
        from clinica_estetica.models import Profissional
        
        if isinstance(profissional_id, Profissional):
            profissional_id = profissional_id.id
        
        existe = Profissional.objects.filter(
            id=profissional_id,
            is_active=True
        ).exists()
        
        if not existe:
            raise serializers.ValidationError({
                'profissional': f"Profissional ID {profissional_id} não existe nesta loja. "
                               f"Por favor, recarregue a página (Ctrl+Shift+R) e tente novamente."
            })
    
    return data
```

### 2. Adicionar Logs Detalhados
**Arquivo**: `backend/clinica_estetica/views.py`

```python
def perform_create(self, serializer):
    """Preenche automaticamente o loja_id do contexto"""
    from tenants.middleware import get_current_loja_id
    import logging
    logger = logging.getLogger(__name__)
    
    loja_id = get_current_loja_id()
    profissional_id = self.request.data.get('profissional')
    
    # Log detalhado para debug
    logger.info(f"[BloqueioAgenda] loja_id={loja_id}, profissional_id={profissional_id}")
    
    # Verificar se profissional existe
    if profissional_id:
        from clinica_estetica.models import Profissional
        existe = Profissional.objects.filter(id=profissional_id).exists()
        logger.info(f"[BloqueioAgenda] Profissional {profissional_id} existe no schema? {existe}")
    
    serializer.save(loja_id=loja_id)
```

## Teste Completo

Após implementar as melhorias:

1. **Limpar cache** do navegador
2. **Acessar** https://lwksistemas.com.br/loja/teste-5889/dashboard
3. **Abrir DevTools** → Network
4. **Carregar** lista de profissionais
5. **Verificar** IDs retornados
6. **Criar bloqueio** selecionando Marina
7. **Confirmar** que o ID enviado é o correto
8. **Verificar** que o bloqueio foi criado com sucesso

## Próximos Passos

1. ✅ **Instruir usuário** a limpar cache (Ctrl+Shift+R)
2. ⏳ **Aguardar confirmação** do usuário
3. ⏳ **Implementar melhorias** no frontend (cache-busting)
4. ⏳ **Implementar melhorias** no backend (validação robusta)
5. ⏳ **Testar** em produção

## Conclusão

O problema é **cache do navegador** com dados desatualizados. A solução imediata é **limpar o cache**. As melhorias permanentes evitarão que isso aconteça novamente.
