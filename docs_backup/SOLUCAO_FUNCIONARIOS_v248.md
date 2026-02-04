# ✅ Solução: Funcionários não aparecem

## 🎯 Problema

Você está em https://lwksistemas.com.br/loja/vida/dashboard e vê:
```
Nenhum funcionário cadastrado
O administrador da loja é automaticamente cadastrado como funcionário
```

## ✅ Verificação no Banco

Executei comando no Heroku e confirmei:

**Funcionário EXISTE:**
- Nome: felipe
- Email: financeiroluiz@hotmail.com
- Cargo: Administrador
- is_admin: **True** ✅
- ID: 37
- loja_id: 72

## 🔍 Causa do Problema

O localStorage do navegador não tem o `current_loja_id` salvo, então o frontend não está enviando o header `X-Loja-ID: 72` nas requisições.

Sem esse header, o backend não sabe qual loja filtrar e retorna lista vazia.

## 🚀 SOLUÇÃO RÁPIDA (30 segundos)

### Execute AGORA no navegador:

1. Acesse: https://lwksistemas.com.br/loja/vida/dashboard
2. Pressione **F12**
3. Vá na aba **Console**
4. Cole e execute:

```javascript
localStorage.setItem('current_loja_id', '72');
location.reload();
```

5. Após recarregar, clique em **"Funcionários"**

**Pronto!** Deve aparecer o funcionário felipe com badge de Administrador.

## 🔧 Por que isso aconteceu?

O código do frontend salva o `loja_id` quando carrega as informações da loja:

```typescript
// frontend/app/(dashboard)/loja/[slug]/dashboard/page.tsx
const lojaResponse = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
if (lojaResponse.data.id) {
  localStorage.setItem('current_loja_id', lojaResponse.data.id.toString());
}
```

Mas pode ter acontecido:
1. Você acessou antes do código ser deployado
2. Cache do navegador/Vercel
3. Erro na requisição que não salvou o ID

## 🎯 Teste Completo

Após executar a solução, você deve ver:

### No Modal de Funcionários:
```
Gerenciar Funcionários

👤 felipe
   📧 financeiroluiz@hotmail.com
   🏷️ Administrador
   
   [Badge azul: 👤 Administrador]
   
   [Botão Editar] [Botão Excluir - desabilitado]
```

### No DevTools (Network):
```
Request URL: https://lwksistemas-38ad47519238.herokuapp.com/api/clinica/funcionarios/
Request Headers:
  X-Loja-ID: 72
  Content-Type: application/json
```

### Nos Logs do Heroku:
```
🔍 [TenantMiddleware] URL: /api/clinica/funcionarios/ | Slug detectado: vida
✅ [TenantMiddleware] Contexto setado: loja_id=72, db=loja_vida
```

## 📊 Arquitetura Funcionando

```
Frontend (Vercel)
  ↓
  1. Carrega loja: GET /api/superadmin/lojas/info_publica/?slug=vida
  2. Salva no localStorage: current_loja_id = 72
  3. Clica em "Funcionários"
  4. Envia: GET /api/clinica/funcionarios/ com header X-Loja-ID: 72
  ↓
Backend (Heroku)
  ↓
  5. TenantMiddleware detecta X-Loja-ID: 72
  6. Seta contexto: set_current_loja_id(72)
  7. LojaIsolationManager filtra: WHERE loja_id = 72
  8. Retorna: [{ id: 37, nome: "felipe", is_admin: true, ... }]
  ↓
Frontend
  ↓
  9. Renderiza funcionário com badge de Administrador
```

## ✅ Checklist Final

- [x] Funcionário existe no banco (felipe, ID: 37)
- [x] Funcionário marcado como admin (is_admin: True)
- [x] Backend v247 deployado com middleware correto
- [x] Frontend v245 deployado com X-Loja-ID
- [ ] localStorage tem current_loja_id = 72 ← **EXECUTAR SOLUÇÃO**
- [ ] Funcionário aparece no modal ← **VERIFICAR APÓS SOLUÇÃO**

## 🎬 Próximos Passos

Após resolver:

1. **Testar CRUD completo:**
   - ✅ Listar funcionários
   - ➕ Criar novo funcionário
   - ✏️ Editar funcionário
   - 🗑️ Excluir funcionário (não-admin)

2. **Testar em outras lojas:**
   - Criar nova loja
   - Verificar se funcionário admin é criado automaticamente
   - Verificar isolamento de dados

3. **Documentar para usuários:**
   - Se aparecer "Nenhum funcionário", recarregar a página
   - Limpar cache se necessário

## 🆘 Se Não Funcionar

Execute no terminal e me envie o resultado:

```bash
heroku logs --tail --app lwksistemas
```

Depois clique em "Funcionários" no dashboard e copie os logs que aparecerem.
