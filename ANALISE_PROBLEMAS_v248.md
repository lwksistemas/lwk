# 🔍 Análise de Problemas - Funcionários v248

## ❌ Problemas Identificados

### Problema 1: Funcionários não aparecem na listagem
**Causa:** localStorage não tem `current_loja_id` salvo
**Status:** ⚠️ Requer ação do usuário

### Problema 2: Erro 400 ao criar funcionário
**Causa:** Serializer esperava `loja_id` mas frontend não enviava
**Status:** ✅ CORRIGIDO em v248

## 🔧 Correções Implementadas (v248)

### Backend - Serializers Atualizados

**Arquivo:** `backend/clinica_estetica/serializers.py`
```python
class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']  # ← loja_id read-only
    
    def create(self, validated_data):
        """Adiciona loja_id automaticamente do contexto"""
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        if loja_id:
            validated_data['loja_id'] = loja_id  # ← Adiciona automaticamente
        return super().create(validated_data)
```

**Arquivo:** `backend/crm_vendas/serializers.py`
```python
class VendedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendedor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'loja_id']  # ← loja_id read-only
    
    def create(self, validated_data):
        """Adiciona loja_id automaticamente do contexto"""
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        if loja_id:
            validated_data['loja_id'] = loja_id  # ← Adiciona automaticamente
        return super().create(validated_data)
```

### O que mudou?

1. **`loja_id` agora é read-only**: Frontend não precisa mais enviar
2. **Método `create()` customizado**: Pega `loja_id` do contexto do middleware
3. **Funciona para todas as lojas**: Usa o ID da loja atual automaticamente

## 🎯 Como Testar Agora

### Passo 1: Forçar localStorage (OBRIGATÓRIO)

**No navegador** (não no terminal!):
1. Acesse: https://lwksistemas.com.br/loja/vida/dashboard
2. Pressione **F12**
3. Aba **Console**
4. Cole e execute:

```javascript
localStorage.setItem('current_loja_id', '72');
location.reload();
```

### Passo 2: Verificar se funcionário aparece

Após recarregar, clique em **"Funcionários"**.

**Deve aparecer:**
```
👥 felipe (Administrador)
   📧 financeiroluiz@hotmail.com
   🏷️ Administrador
   [Badge: 👤 Administrador]
```

### Passo 3: Testar criação de novo funcionário

1. Clique em **"+ Cadastrar Funcionário"**
2. Preencha:
   - Nome: Maria Silva
   - Email: maria@teste.com
   - Telefone: (11) 99999-9999
   - Cargo: Recepcionista
3. Clique em **"Cadastrar"**

**Resultado esperado:**
- ✅ Mensagem: "Funcionário cadastrado com sucesso!"
- ✅ Maria aparece na lista
- ✅ Felipe continua com badge de Administrador

## 📊 Fluxo Corrigido

```
Frontend
  ↓
  1. localStorage tem: current_loja_id = 72
  2. clinicaApiClient adiciona header: X-Loja-ID: 72
  3. POST /api/clinica/funcionarios/
     Body: { nome, email, telefone, cargo }  ← SEM loja_id
  ↓
Backend
  ↓
  4. TenantMiddleware detecta: X-Loja-ID: 72
  5. set_current_loja_id(72)
  6. FuncionarioSerializer.create()
  7. get_current_loja_id() → 72
  8. validated_data['loja_id'] = 72  ← Adiciona automaticamente
  9. Funcionario.objects.create(...)
  ↓
Response
  ↓
  10. Status 201 Created
  11. Retorna funcionário criado
```

## ⚠️ Problema Restante

### localStorage não persiste automaticamente

**Causa:** Código do frontend salva `loja_id` ao carregar a página, mas pode falhar se:
- Cache do navegador
- Erro na requisição
- Página acessada antes do deploy

**Solução temporária:** Executar manualmente o código JavaScript

**Solução permanente:** Adicionar verificação no frontend:

```typescript
// frontend/app/(dashboard)/loja/[slug]/dashboard/templates/clinica-estetica.tsx
const loadFuncionarios = async () => {
  try {
    // Garantir que loja_id está no localStorage
    if (!localStorage.getItem('current_loja_id')) {
      localStorage.setItem('current_loja_id', loja.id.toString());
    }
    
    const response = await clinicaApiClient.get('/clinica/funcionarios/');
    setFuncionarios(response.data);
  } catch (error) {
    console.error('Erro ao carregar funcionários:', error);
  }
};
```

## ✅ Checklist de Verificação

- [x] Serializer atualizado (loja_id read-only)
- [x] Método create() adiciona loja_id automaticamente
- [x] Deploy v248 concluído no Heroku
- [ ] localStorage setado manualmente (usuário precisa fazer)
- [ ] Funcionário felipe aparece na lista
- [ ] Criação de novo funcionário funciona (sem erro 400)

## 🚀 Próximos Passos

1. **Executar código JavaScript** no navegador (Passo 1 acima)
2. **Testar listagem** de funcionários
3. **Testar criação** de novo funcionário
4. **Verificar isolamento** (funcionários de uma loja não aparecem em outra)

## 📝 Versões

- **Backend:** v248 (Heroku) ✅ Deployado
- **Frontend:** v245 (Vercel) - Não precisa atualizar
- **Correção:** Serializers com loja_id automático

## 🆘 Se Ainda Não Funcionar

Execute no DevTools Console e me envie o resultado:

```javascript
// 1. Verificar localStorage
console.log('loja_id:', localStorage.getItem('current_loja_id'));

// 2. Testar API diretamente
fetch('https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/funcionarios/', {
  headers: { 'X-Loja-ID': '72' }
})
.then(r => r.json())
.then(data => console.log('Funcionários:', data));

// 3. Verificar headers da última requisição
// (Vá na aba Network, clique em funcionarios/, veja Headers)
```
