# Instruções para Limpar Cache e Resolver Problema de Permissões

## Problema
O sistema não está mostrando oportunidades e propostas porque o navegador ainda tem dados antigos em cache que identificam você como vendedor ao invés de administrador.

## Solução: Limpar SessionStorage

### Passo 1: Abrir DevTools
1. Pressione **F12** no teclado (ou clique com botão direito → Inspecionar)
2. Isso abrirá as ferramentas de desenvolvedor do navegador

### Passo 2: Ir para Application/Aplicativo
1. No topo do DevTools, clique na aba **Application** (ou **Aplicativo** se estiver em português)
2. Se não aparecer, clique nas setas >> para ver mais abas

### Passo 3: Limpar Session Storage
1. No menu lateral esquerdo, procure por **Session Storage**
2. Clique na setinha para expandir
3. Clique em **https://lwksistemas.com.br**
4. Você verá uma lista de itens armazenados
5. **DELETE TODOS OS ITENS**, especialmente:
   - `is_vendedor`
   - `current_vendedor_id`
   - `user_role`
   - Qualquer outro item relacionado a vendedor

### Passo 4: Limpar Local Storage (opcional mas recomendado)
1. No mesmo menu lateral, procure por **Local Storage**
2. Clique na setinha para expandir
3. Clique em **https://lwksistemas.com.br**
4. **DELETE TODOS OS ITENS**

### Passo 5: Fazer Logout e Login
1. Feche o DevTools (F12)
2. Faça **logout** do sistema
3. Feche o navegador completamente
4. Abra o navegador novamente
5. Acesse https://lwksistemas.com.br
6. Faça **login** novamente com suas credenciais

## Verificação
Após fazer login novamente, verifique:

1. **Configurações**: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes
   - Deve mostrar TODAS as opções (não apenas uma)
   
2. **Pipeline**: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/pipeline
   - Deve mostrar todas as oportunidades
   
3. **Propostas**: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/propostas
   - Deve mostrar todas as propostas

## O que foi corrigido no backend
- Removido o VendedorUsuario vinculado ao owner felix (ID: 106)
- Agora o sistema reconhece você como Administrador da loja
- Você tem acesso total a todos os dados e configurações

## Se ainda não funcionar
Se após seguir todos os passos ainda não funcionar:

1. Tente usar o modo anônimo/privado do navegador
2. Ou tente outro navegador (Chrome, Firefox, Edge)
3. Me avise para investigarmos mais a fundo
