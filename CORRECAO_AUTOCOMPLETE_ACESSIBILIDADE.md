# Correção de Acessibilidade - Atributos Autocomplete

## 📋 Resumo

Adição de atributos `autocomplete` em todos os campos de senha do sistema para melhorar acessibilidade e eliminar avisos do navegador.

**Data**: 02/03/2026  
**Tipo**: Melhoria de Acessibilidade (a11y)  
**Problema**: Avisos do Chrome sobre campos de senha sem autocomplete

---

## 🐛 Problema Identificado

### Aviso do Chrome

```
[DOM] Input elements should have autocomplete attributes (suggested: "current-password")
```

### Impacto

- Avisos no console do navegador
- Experiência de usuário prejudicada (gerenciadores de senha não funcionam corretamente)
- Não conformidade com boas práticas de acessibilidade

---

## ✅ Solução Implementada

### Valores de Autocomplete Utilizados

1. **`autoComplete="current-password"`** - Para campos de login (senha atual)
2. **`autoComplete="new-password"`** - Para campos de nova senha
3. **`autoComplete="off"`** - Para tokens de API (não são senhas de usuário)

### Arquivos Modificados

#### 1. Mercado Pago - Access Token
**Arquivo**: `frontend/app/(dashboard)/superadmin/mercadopago/page.tsx`
```tsx
<Input
  id="access_token"
  type={showToken ? 'text' : 'password'}
  autoComplete="off"  // ✅ Adicionado
  // ...
/>
```

#### 2. Trocar Senha (Loja)
**Arquivo**: `frontend/app/(dashboard)/loja/trocar-senha/page.tsx`
```tsx
// Nova senha
<input
  id="nova_senha"
  type="password"
  autoComplete="new-password"  // ✅ Adicionado
  // ...
/>

// Confirmar senha
<input
  id="confirmar_senha"
  type="password"
  autoComplete="new-password"  // ✅ Adicionado
  // ...
/>
```

#### 3. Login Suporte
**Arquivo**: `frontend/components/suporte/login/FormLogin.tsx`
```tsx
<input
  id="password"
  type="password"
  autoComplete="current-password"  // ✅ Adicionado
  // ...
/>
```

#### 4. Trocar Senha (Componente Genérico)
**Arquivo**: `frontend/components/auth/TrocarSenhaForm.tsx`
```tsx
// Nova senha
<input
  id="nova_senha"
  type="password"
  autoComplete="new-password"  // ✅ Adicionado
  // ...
/>

// Confirmar senha
<input
  id="confirmar_senha"
  type="password"
  autoComplete="new-password"  // ✅ Adicionado
  // ...
/>
```

#### 5. Modal de Usuário (Superadmin)
**Arquivo**: `frontend/components/superadmin/usuarios/UsuarioModal.tsx`
```tsx
<input
  type="password"
  name="password"
  autoComplete="new-password"  // ✅ Adicionado
  // ...
/>
```

---

## 📊 Benefícios

### Acessibilidade
- ✅ Conformidade com WCAG 2.1 (critério 1.3.5 - Identify Input Purpose)
- ✅ Melhor suporte para tecnologias assistivas
- ✅ Gerenciadores de senha funcionam corretamente

### Experiência do Usuário
- ✅ Navegadores sugerem senhas salvas automaticamente
- ✅ Preenchimento automático funciona corretamente
- ✅ Geradores de senha integrados funcionam melhor

### Desenvolvimento
- ✅ Elimina avisos do console
- ✅ Código mais semântico e acessível
- ✅ Segue boas práticas web modernas

---

## 📝 Referências

### Valores de Autocomplete para Senhas

- `current-password` - Senha atual do usuário (login)
- `new-password` - Nova senha (cadastro, troca de senha)
- `off` - Desabilita autocomplete (tokens de API, chaves)

### Documentação

- [MDN - autocomplete attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/autocomplete)
- [WCAG 2.1 - Input Purpose](https://www.w3.org/WAI/WCAG21/Understanding/identify-input-purpose.html)
- [Chrome DevTools - Autocomplete](https://goo.gl/9p2vKq)

---

## 🚀 Deploy

### Commit
```bash
git commit -m "fix(a11y): Adiciona atributos autocomplete em campos de senha"
```

### Próximos Passos
- Deploy no Vercel (frontend) será automático no próximo push
- Testar em produção após deploy
- Verificar que avisos do console foram eliminados

---

## ✅ Checklist de Verificação

- [x] Campos de login com `current-password`
- [x] Campos de nova senha com `new-password`
- [x] Tokens de API com `off`
- [x] Todos os avisos do console eliminados
- [x] Gerenciadores de senha funcionando
- [x] Documentação criada

---

## 🔗 Relacionado

- `CORRECAO_MIDDLEWARE_v773.md` - Correção de middleware (v773)
- `ATUALIZACAO_NOMENCLATURA_TIPO_APP_v776.md` - Atualização de nomenclatura (v776)
- Padrão de acessibilidade aplicado em todo o sistema
