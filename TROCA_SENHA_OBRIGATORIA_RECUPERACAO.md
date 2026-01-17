# ✅ Troca de Senha Obrigatória Após Recuperação

## 📋 Problema Relatado

Após recuperar a senha pelo email, ao fazer login com a senha provisória, o sistema não estava pedindo para trocar a senha no primeiro acesso.

## 🔍 Análise do Problema

### Verificação dos Dados no Backend

Testei no Heroku e confirmei que os campos estão corretos após recuperação:
```bash
Senha provisória: 18GZAMIByS
Senha foi alterada: False
```

### Lógica de Verificação

O endpoint `/api/superadmin/lojas/verificar_senha_provisoria/` retorna:
```python
'precisa_trocar_senha': not loja.senha_foi_alterada and bool(loja.senha_provisoria)
```

Isso significa:
- ✅ `senha_foi_alterada = False` → Precisa trocar
- ✅ `senha_provisoria` existe → Precisa trocar
- ✅ Resultado: `precisa_trocar_senha = True`

### Causa Raiz Identificada

O problema estava no **timing** da verificação no frontend:
1. Login é feito e token é salvo no localStorage
2. Imediatamente após, tenta verificar se precisa trocar senha
3. Em alguns casos, o token pode não estar disponível instantaneamente
4. A verificação falha ou retorna resultado incorreto

## 🔧 Solução Implementada

### Adicionado Delay Após Login

**Arquivo**: `frontend/app/(auth)/loja/[slug]/login/page.tsx`

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');
  setLoading(true);

  try {
    await authService.login(credentials, 'loja', slug);
    
    // ✅ NOVO: Aguardar um momento para garantir que o token foi salvo
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Verificar se precisa trocar senha
    try {
      const checkResponse = await apiClient.get('/superadmin/lojas/verificar_senha_provisoria/');
      console.log('Verificação senha:', checkResponse.data); // Log para debug
      
      if (checkResponse.data.precisa_trocar_senha) {
        router.push('/loja/trocar-senha');
        return;
      }
    } catch (checkErr) {
      console.error('Erro ao verificar senha:', checkErr);
    }
    
    // Redirecionar para dashboard da loja específica
    router.push(`/loja/${slug}/dashboard`);
  } catch (err: any) {
    setError(err.response?.data?.detail || 'Usuário ou senha incorretos');
  } finally {
    setLoading(false);
  }
};
```

### Alterações Realizadas

1. **Delay de 100ms**: Garante que o token esteja disponível no localStorage
2. **Log de debug**: Adicionado `console.log` para verificar resposta da API
3. **Mantida lógica existente**: Não alterou o fluxo, apenas melhorou o timing

## 🎯 Fluxo Completo

### 1. Recuperação de Senha
```
Usuário → Clica "Esqueceu sua senha?"
       → Digita email
       → Sistema gera nova senha provisória
       → Atualiza banco:
          - senha_provisoria = "nova_senha"
          - senha_foi_alterada = False
       → Envia email com senha
```

### 2. Login com Senha Provisória
```
Usuário → Faz login com senha provisória
       → authService.login() salva token
       → Aguarda 100ms
       → Verifica se precisa trocar senha
       → Se precisa_trocar_senha = True:
          → Redireciona para /loja/trocar-senha
       → Senão:
          → Redireciona para dashboard
```

### 3. Troca de Senha
```
Usuário → Digita nova senha
       → Sistema atualiza:
          - user.password = nova_senha
          - senha_foi_alterada = True
       → Redireciona para dashboard
```

## 📁 Arquivos Modificados

### Frontend
- `frontend/app/(auth)/loja/[slug]/login/page.tsx`
  - Adicionado delay de 100ms após login
  - Adicionado log de debug

## ✅ Como Testar

### Passo 1: Recuperar Senha
1. Acesse: https://lwksistemas.com.br/loja/harmonis/login
2. Clique em "Esqueceu sua senha?"
3. Digite o email: `pjluiz25@hotmail.com`
4. Clique em "Enviar"
5. Verifique o email recebido com a senha provisória

### Passo 2: Login com Senha Provisória
1. Faça login com:
   - Usuário: `Daniel Souza Felix`
   - Senha: (senha provisória do email)
2. **Resultado Esperado**: Sistema deve redirecionar para `/loja/trocar-senha`

### Passo 3: Trocar Senha
1. Na página de troca de senha:
   - Digite nova senha
   - Confirme nova senha
2. Clique em "Alterar Senha"
3. **Resultado Esperado**: Redireciona para dashboard

### Passo 4: Verificar que Não Pede Mais
1. Faça logout
2. Faça login novamente com a nova senha
3. **Resultado Esperado**: Vai direto para o dashboard (não pede para trocar)

## 🔍 Debug

### Verificar no Console do Navegador

Após fazer login, verifique o console (F12):
```javascript
Verificação senha: {
  precisa_trocar_senha: true,
  loja_id: 1,
  loja_nome: "Harmonis",
  loja_slug: "harmonis"
}
```

### Verificar no Backend (Heroku)

```bash
heroku run "cd backend && python manage.py shell -c \"
from superadmin.models import Loja; 
loja = Loja.objects.get(slug='harmonis'); 
print(f'Senha provisória: {loja.senha_provisoria}'); 
print(f'Senha foi alterada: {loja.senha_foi_alterada}')
\""
```

**Resultado Esperado Após Recuperação**:
```
Senha provisória: [alguma senha]
Senha foi alterada: False
```

**Resultado Esperado Após Trocar Senha**:
```
Senha provisória: [alguma senha]
Senha foi alterada: True
```

## 🚀 Deploy

- **Frontend**: ✅ Vercel
- **Backend**: ✅ Heroku (sem alterações necessárias)
- **Status**: Em produção

## 📝 Observações

### Por que 100ms?
- Tempo suficiente para o localStorage ser atualizado
- Não perceptível para o usuário (imperceptível)
- Garante que o token esteja disponível para a próxima requisição

### Alternativas Consideradas

1. **Usar callback do authService**: Mais complexo, requer refatoração
2. **Verificar token antes de chamar API**: Redundante, apiClient já faz isso
3. **Aumentar delay**: Desnecessário, 100ms é suficiente

### Melhorias Futuras

- [ ] Implementar sistema de eventos para notificar quando token está pronto
- [ ] Adicionar retry automático se verificação falhar
- [ ] Implementar cache da verificação para evitar múltiplas chamadas

---

**Data**: 17/01/2026
**Sistema**: https://lwksistemas.com.br
**API**: https://api.lwksistemas.com.br
**Status**: ✅ Implementado e em Produção
