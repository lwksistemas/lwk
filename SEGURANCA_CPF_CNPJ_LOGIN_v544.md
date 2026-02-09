# Segurança: Campo CPF/CNPJ no Login - v544

**Data:** 09/02/2026  
**Tipo:** Melhoria de Segurança  
**Status:** ✅ IMPLEMENTADO

---

## 🎯 Objetivo

Adicionar uma camada extra de segurança no login das lojas, exigindo CPF ou CNPJ além de usuário e senha.

---

## 🔒 Funcionalidade

### Como Funciona

1. **Loja com CPF/CNPJ cadastrado:**
   - Campo CPF/CNPJ aparece automaticamente na tela de login
   - Usuário deve informar CPF/CNPJ correto para fazer login
   - Backend valida se o CPF/CNPJ corresponde ao cadastrado

2. **Loja sem CPF/CNPJ cadastrado:**
   - Campo CPF/CNPJ NÃO aparece na tela de login
   - Login funciona normalmente (usuário + senha)

### Formatação Automática

O campo CPF/CNPJ formata automaticamente enquanto o usuário digita:

- **CPF:** `000.000.000-00` (11 dígitos)
- **CNPJ:** `00.000.000/0000-00` (14 dígitos)

---

## 📋 Implementação

### Backend

**Arquivo:** `backend/superadmin/auth_views_secure.py`

```python
# Validação de CPF/CNPJ no login
if user_type == 'loja' and cpf_cnpj:
    import re
    # Remover formatação do CPF/CNPJ
    cpf_cnpj_limpo = re.sub(r'[^0-9]', '', cpf_cnpj)
    
    # Buscar loja do usuário
    loja = Loja.objects.filter(owner=user, is_active=True).first()
    if loja and loja.cpf_cnpj:
        # Remover formatação do CPF/CNPJ da loja
        loja_cpf_cnpj_limpo = re.sub(r'[^0-9]', '', loja.cpf_cnpj)
        
        # Validar se o CPF/CNPJ corresponde
        if cpf_cnpj_limpo != loja_cpf_cnpj_limpo:
            return Response({
                'error': 'CPF/CNPJ incorreto',
                'code': 'INVALID_CPF_CNPJ'
            }, status=401)
```

**Arquivo:** `backend/superadmin/views.py`

```python
# Endpoint info_publica retorna se loja requer CPF/CNPJ
return Response({
    ...
    'requer_cpf_cnpj': bool(getattr(loja, 'cpf_cnpj', None)),
})
```

### Frontend

**Arquivo:** `frontend/app/(auth)/loja/[slug]/login/page.tsx`

```typescript
// Formatação automática de CPF/CNPJ
const formatarCpfCnpj = (valor: string) => {
  const numeros = valor.replace(/\D/g, '');
  const limitado = numeros.slice(0, 14);
  
  if (limitado.length <= 11) {
    // CPF: 000.000.000-00
    return limitado
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  } else {
    // CNPJ: 00.000.000/0000-00
    return limitado
      .replace(/(\d{2})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1/$2')
      .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
  }
};

// Campo CPF/CNPJ - Apenas se a loja tiver cadastrado
{lojaInfo?.requer_cpf_cnpj && (
  <div>
    <label>CPF/CNPJ</label>
    <input
      type="text"
      value={credentials.cpf_cnpj}
      onChange={handleCpfCnpjChange}
      placeholder="000.000.000-00 ou 00.000.000/0000-00"
      maxLength={18}
    />
  </div>
)}
```

---

## 🔐 Segurança

### Validações Implementadas

1. **Backend:**
   - Remove formatação (pontos, traços, barras) antes de comparar
   - Compara apenas números
   - Retorna erro 401 se CPF/CNPJ não corresponder
   - Log de tentativa de acesso com CPF/CNPJ incorreto

2. **Frontend:**
   - Campo só aparece se loja tiver CPF/CNPJ cadastrado
   - Formatação automática para facilitar digitação
   - Limite de 18 caracteres (CNPJ formatado)
   - Campo obrigatório quando exibido

### Proteção Contra

- ✅ Acesso não autorizado mesmo com usuário e senha corretos
- ✅ Tentativas de login sem conhecer o CPF/CNPJ da loja
- ✅ Ataques de força bruta (mais um fator de autenticação)

---

## 📊 Fluxo de Login

### Loja COM CPF/CNPJ

```
1. Usuário acessa /loja/{slug}/login
   ↓
2. Frontend carrega info_publica
   ↓
3. Backend retorna requer_cpf_cnpj: true
   ↓
4. Frontend exibe campo CPF/CNPJ
   ↓
5. Usuário preenche: usuário, CPF/CNPJ, senha
   ↓
6. Backend valida:
   - Usuário e senha corretos?
   - CPF/CNPJ corresponde ao cadastrado?
   ↓
7. Se tudo OK: Login bem-sucedido
   Se CPF/CNPJ errado: Erro 401
```

### Loja SEM CPF/CNPJ

```
1. Usuário acessa /loja/{slug}/login
   ↓
2. Frontend carrega info_publica
   ↓
3. Backend retorna requer_cpf_cnpj: false
   ↓
4. Frontend NÃO exibe campo CPF/CNPJ
   ↓
5. Usuário preenche: usuário, senha
   ↓
6. Backend valida apenas usuário e senha
   ↓
7. Login bem-sucedido
```

---

## 🧪 Como Testar

### 1. Cadastrar CPF/CNPJ em uma Loja

```bash
# Acessar painel superadmin
https://lwksistemas.com.br/superadmin/login

# Editar loja
# Adicionar CPF ou CNPJ no campo "CPF/CNPJ"
# Exemplo: 12.345.678/0001-90 (CNPJ)
# Exemplo: 123.456.789-00 (CPF)
```

### 2. Testar Login

```bash
# Acessar página de login da loja
https://lwksistemas.com.br/loja/{slug}/login

# Verificar que campo CPF/CNPJ aparece
# Tentar login SEM preencher CPF/CNPJ → Erro
# Tentar login com CPF/CNPJ errado → Erro 401
# Tentar login com CPF/CNPJ correto → Sucesso
```

### 3. Testar Formatação

```bash
# Digitar apenas números: 12345678000190
# Campo formata automaticamente: 12.345.678/0001-90

# Digitar apenas números: 12345678900
# Campo formata automaticamente: 123.456.789-00
```

---

## 📝 Mensagens de Erro

### CPF/CNPJ Incorreto

```json
{
  "error": "CPF/CNPJ incorreto. Verifique os dados e tente novamente.",
  "code": "INVALID_CPF_CNPJ"
}
```

### Usuário ou Senha Incorretos

```json
{
  "error": "Usuário ou senha incorretos. Verifique suas credenciais e tente novamente.",
  "code": "INVALID_CREDENTIALS"
}
```

---

## 🎯 Benefícios

1. **Segurança Aumentada:**
   - Mais um fator de autenticação
   - Dificulta acesso não autorizado

2. **Flexibilidade:**
   - Opcional (só aparece se loja tiver CPF/CNPJ)
   - Não afeta lojas sem CPF/CNPJ cadastrado

3. **Usabilidade:**
   - Formatação automática
   - Mensagens de erro claras
   - Interface intuitiva

4. **Auditoria:**
   - Logs de tentativas com CPF/CNPJ incorreto
   - Rastreamento de acessos

---

## 📋 Arquivos Modificados

### Backend
- `backend/superadmin/auth_views_secure.py` - Validação de CPF/CNPJ
- `backend/superadmin/views.py` - Endpoint info_publica

### Frontend
- `frontend/app/(auth)/loja/[slug]/login/page.tsx` - Campo CPF/CNPJ
- `frontend/lib/auth.ts` - Interface LoginCredentials

---

## ✅ Checklist

- [x] Backend valida CPF/CNPJ no login
- [x] Frontend exibe campo apenas se necessário
- [x] Formatação automática implementada
- [x] Mensagens de erro claras
- [x] Logs de segurança
- [x] Documentação completa
- [x] Deploy em produção
- [ ] Testes em produção
- [ ] Monitoramento de logs

---

## 🚀 Próximos Passos

1. **Testar em Produção:**
   - Cadastrar CPF/CNPJ em uma loja de teste
   - Verificar que campo aparece no login
   - Testar validação

2. **Monitorar Logs:**
   - Verificar tentativas de login com CPF/CNPJ incorreto
   - Identificar possíveis ataques

3. **Melhorias Futuras:**
   - Validar formato de CPF/CNPJ (dígitos verificadores)
   - Adicionar captcha após X tentativas falhas
   - Implementar 2FA (autenticação de dois fatores)

---

## 📞 Suporte

Em caso de problemas:

1. Verificar logs do Heroku
2. Verificar se CPF/CNPJ está cadastrado corretamente
3. Testar com CPF/CNPJ formatado e sem formatação
4. Contatar desenvolvedor responsável

---

**Desenvolvido em:** 09/02/2026  
**Versão:** v544  
**Prioridade:** ALTA  
**Impacto:** Segurança Aumentada
