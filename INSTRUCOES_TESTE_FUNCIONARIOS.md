# Instruções para Testar Lista de Funcionários
**Data: 2026-03-26**
**Versão: v1354**

## ✅ Correções Implementadas

1. **Backend (v1347)**: Signal corrigido para criar Vendedor com `is_admin=True`
2. **Backend (v1354)**: Script executado para criar `VendedorUsuario` vinculando owner ao vendedor
3. **Frontend (v1348)**: Correções de permissões deployed no Vercel

## 🔍 Verificação no Banco de Dados

Executamos verificação e confirmamos:

```
Loja: Felix Representações (ID: 172)
Schema: loja_41449198000172
Vendedor: LUIZ HENRIQUE FELIX
- ID: 1
- Email: consultorluizfelix@hotmail.com
- is_admin: True
- is_active: True
- loja_id: 172

VendedorUsuario: ✅ Existe (vincula owner ao vendedor)
```

## 🧪 Como Testar

### 1. Limpar Cache do Navegador

**Chrome/Edge:**
1. Pressione `Ctrl+Shift+Delete` (Windows) ou `Cmd+Shift+Delete` (Mac)
2. Selecione "Imagens e arquivos em cache"
3. Clique em "Limpar dados"

**Ou use modo anônimo:**
1. Pressione `Ctrl+Shift+N` (Windows) ou `Cmd+Shift+N` (Mac)

### 2. Fazer Logout e Login Novamente

1. Acesse: https://lwksistemas.com.br/loja/41449198000172/login
2. Faça logout se estiver logado
3. Faça login novamente com suas credenciais
4. Acesse: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes/funcionarios

### 3. Resultado Esperado

Você deve ver:

```
Cadastrar funcionários
Gerencie vendedores e equipe de vendas

[Novo vendedor]

┌─────────────────────────────────────────────────────────┐
│ LUIZ HENRIQUE FELIX                    [Administrador]  │
│ consultorluizfelix@hotmail.com                          │
│ ✉ Acesso ao sistema                                    │
│                                    [Reenviar senha]     │
└─────────────────────────────────────────────────────────┘
```

## ❓ Se Ainda Não Aparecer

### Opção 1: Verificar Console do Navegador

1. Pressione `F12` para abrir DevTools
2. Vá na aba "Console"
3. Recarregue a página (`F5`)
4. Procure por erros em vermelho
5. Tire um print e envie

### Opção 2: Verificar Rede

1. Pressione `F12` para abrir DevTools
2. Vá na aba "Network" (Rede)
3. Recarregue a página (`F5`)
4. Procure pela requisição `/api/crm-vendas/vendedores/`
5. Clique nela e veja a resposta (Response)
6. Tire um print e envie

### Opção 3: Forçar Recarregamento

1. Na página de funcionários, pressione:
   - Windows: `Ctrl+F5` ou `Ctrl+Shift+R`
   - Mac: `Cmd+Shift+R`
2. Isso força o navegador a ignorar o cache

## 🔧 Troubleshooting

### Se a lista estiver vazia:

1. **Cache do navegador**: Limpe o cache completamente
2. **Service Worker**: Desabilite service workers em DevTools > Application > Service Workers
3. **Sessão antiga**: Faça logout completo e login novamente
4. **Cache do Vercel**: Aguarde 2-3 minutos para propagação do deploy

### Se aparecer erro 403 ou 401:

1. Faça logout e login novamente
2. Verifique se está logado como o owner (administrador) da loja

## 📞 Suporte

Se após seguir todos os passos o problema persistir:

1. Tire prints do console (F12 > Console)
2. Tire prints da aba Network (F12 > Network > vendedores)
3. Informe qual navegador está usando
4. Informe se testou em modo anônimo

---

**Última atualização**: 2026-03-26 - Deploy v1354 concluído
