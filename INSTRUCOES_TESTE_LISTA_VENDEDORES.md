# Instruções para Testar Lista de Vendedores

## Problema Resolvido
O endpoint `/api/crm-vendas/vendedores/` estava retornando lista vazia devido a um `Exists()` cross-database no `VendedorViewSet.get_queryset()`. Isso foi corrigido na versão v1356.

## Como Testar

### 1. Limpar Cache do Navegador
O navegador pode estar cacheando a resposta antiga. Para limpar:

**Chrome/Edge:**
1. Pressione `F12` para abrir DevTools
2. Clique com botão direito no ícone de recarregar
3. Selecione "Limpar cache e recarregar forçadamente"

**Firefox:**
1. Pressione `Ctrl+Shift+Delete`
2. Selecione "Cache"
3. Clique em "Limpar agora"

### 2. Fazer Logout e Login Novamente
1. Acesse https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes/funcionarios
2. Faça logout
3. Faça login novamente com suas credenciais
4. Acesse a página de funcionários novamente

### 3. Verificar se o Vendedor Aparece
Após fazer login novamente, você deve ver:
- **LUIZ HENRIQUE FELIX** com badge "Administrador"
- Email: consultorluizfelix@hotmail.com
- Botão "Reenviar senha"

## Versões Deployed
- Backend: v1361 (Heroku)
- Frontend: Deployed no Vercel

## Se Ainda Não Aparecer
Se após limpar o cache e fazer login novamente o vendedor ainda não aparecer, execute o seguinte comando no Heroku para verificar:

```bash
heroku run python backend/verificar_vendedor_admin_loja.py --app lwksistemas
```

Isso mostrará se o vendedor existe no banco e se o VendedorUsuario está vinculado corretamente.
