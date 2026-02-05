# 🐛 Problema: Erro ao Salvar Dados nas Lojas

## 📊 Status Atual

### ✅ Resolvido:
- **Cliente**: Salvando com sucesso!

### ⚠️ Problemas Restantes:
1. **Cliente não aparece na lista após salvar** - Lista não recarrega
2. **Funcionário retorna erro 401** - "As credenciais de autenticação não foram fornecidas"

---

## 🔍 Análise do Problema

### Problema 1: Cliente não aparece na lista

**Causa**: O cliente é salvo com sucesso, mas a lista não é atualizada visualmente.

**Código atual** (correto):
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    if (editando) {
      await apiClient.put(`/cabeleireiro/clientes/${editando.id}/`, formData);
      toast.success('Cliente atualizado!');
    } else {
      await apiClient.post('/cabeleireiro/clientes/', formData);
      toast.success('Cliente cadastrado!');
    }
    setFormData({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' });
    setEditando(null);
    carregarClientes(); // ✅ Já está chamando!
  } catch (error) {
    console.error('Erro ao salvar cliente:', error);
    toast.error('Erro ao salvar cliente');
  }
};
```

**Possíveis causas**:
- A requisição GET `/cabeleireiro/clientes/` pode estar retornando dados em cache
- O estado `clientes` pode não estar sendo atualizado corretamente
- Pode haver um problema com o `ensureArray(response.data)`

**Solução temporária**: Recarregar a página após salvar

---

### Problema 2: Funcionário retorna erro 401

**Erro completo**:
```
GET /api/cabeleireiro/funcionarios/
HTTP 401 Unauthorized
{
  "detail": "As credenciais de autenticação não foram fornecidas."
}
```

**Causa**: O token de autenticação não está sendo enviado na requisição.

**Possíveis causas**:
1. Token expirou
2. Token não está no sessionStorage
3. Interceptor do axios não está adicionando o header Authorization
4. Problema específico com o endpoint de funcionários

**Debug necessário**:
1. Verificar se o token está no sessionStorage:
   ```javascript
   console.log('Token:', sessionStorage.getItem('access_token'));
   ```

2. Verificar se o header está sendo enviado:
   - Abrir DevTools (F12)
   - Aba Network
   - Fazer a requisição
   - Clicar na requisição
   - Ver "Request Headers"
   - Verificar se tem `Authorization: Bearer <token>`

---

## 🔧 Soluções Propostas

### Solução 1: Forçar recarregamento da lista de clientes

Adicionar um pequeno delay antes de recarregar:

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  try {
    if (editando) {
      await apiClient.put(`/cabeleireiro/clientes/${editando.id}/`, formData);
      toast.success('Cliente atualizado!');
    } else {
      await apiClient.post('/cabeleireiro/clientes/', formData);
      toast.success('Cliente cadastrado!');
    }
    setFormData({ nome: '', telefone: '', email: '', cpf: '', data_nascimento: '', observacoes: '' });
    setEditando(null);
    
    // Aguardar um pouco antes de recarregar
    setTimeout(() => {
      carregarClientes();
    }, 500);
  } catch (error) {
    console.error('Erro ao salvar cliente:', error);
    toast.error('Erro ao salvar cliente');
  }
};
```

---

### Solução 2: Verificar e renovar token antes de salvar funcionário

Adicionar verificação de token:

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  
  // Verificar se tem token
  const token = sessionStorage.getItem('access_token');
  if (!token) {
    toast.error('Sessão expirada. Faça login novamente.');
    return;
  }
  
  try {
    if (editando) {
      await apiClient.put(`/cabeleireiro/funcionarios/${editando.id}/`, formData);
      toast.success('Funcionário atualizado!');
    } else {
      await apiClient.post('/cabeleireiro/funcionarios/', formData);
      toast.success('Funcionário cadastrado!');
    }
    setFormData({ nome: '', email: '', telefone: '', cargo: '' });
    setEditando(null);
    setShowForm(false);
    carregarFuncionarios();
  } catch (error) {
    console.error('Erro ao salvar funcionário:', error);
    toast.error('Erro ao salvar funcionário');
  }
};
```

---

## 🎯 Próximos Passos

### Para o usuário:

1. **Teste de Cliente**:
   - Salvar um cliente
   - Fechar o modal
   - Abrir o modal novamente
   - Verificar se o cliente aparece na lista

2. **Teste de Funcionário**:
   - Abrir o console do navegador (F12)
   - Executar: `console.log('Token:', sessionStorage.getItem('access_token'))`
   - Verificar se retorna um token ou null
   - Tentar salvar um funcionário
   - Ver o erro completo no console

3. **Verificar Headers**:
   - Abrir DevTools (F12) → Aba Network
   - Tentar salvar um funcionário
   - Clicar na requisição POST `/api/cabeleireiro/funcionarios/`
   - Ver "Request Headers"
   - Verificar se tem `Authorization: Bearer <token>`

---

## 📝 Informações Adicionais

### Endpoints afetados:
- ✅ `/api/cabeleireiro/clientes/` - Funcionando (salva mas não atualiza lista)
- ❌ `/api/cabeleireiro/funcionarios/` - Erro 401

### Outros apps:
- Verificar se o problema acontece em outros apps (CRM Vendas, Serviços, etc.)
- Se sim, é um problema geral de autenticação
- Se não, é específico do cabeleireiro

---

**Data**: 05/02/2026  
**Status**: Em investigação  
**Prioridade**: Alta
