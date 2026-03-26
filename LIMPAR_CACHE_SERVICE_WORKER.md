# Como Limpar Cache do Service Worker (PWA)

## Problema
O navegador está mostrando `Status Code 200 OK (from service worker)`, o que significa que está servindo dados cacheados pelo PWA (Progressive Web App) ao invés de buscar do servidor.

## Solução: Limpar Cache do Service Worker

### Opção 1: Desregistrar Service Worker (Recomendado)

1. Abra o DevTools (F12)
2. Vá para a aba "Application" (Chrome) ou "Armazenamento" (Firefox)
3. No menu lateral esquerdo, clique em "Service Workers"
4. Encontre o service worker de `lwksistemas.com.br`
5. Clique em "Unregister" ou "Cancelar registro"
6. Recarregue a página (F5)

### Opção 2: Limpar Todo o Cache do Site

**Chrome/Edge:**
1. Pressione F12 para abrir DevTools
2. Vá para a aba "Application"
3. No menu lateral, clique em "Clear storage"
4. Marque todas as opções:
   - Local storage
   - Session storage
   - IndexedDB
   - Web SQL
   - Cookies
   - Cache storage
   - Service workers
5. Clique em "Clear site data"
6. Feche e abra o navegador novamente

**Firefox:**
1. Pressione F12 para abrir DevTools
2. Vá para a aba "Armazenamento"
3. Clique com botão direito em cada item e selecione "Limpar tudo"
4. Feche e abra o navegador novamente

### Opção 3: Modo Anônimo/Privado

1. Abra uma janela anônima (Ctrl+Shift+N no Chrome, Ctrl+Shift+P no Firefox)
2. Acesse: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes/funcionarios
3. Faça login
4. Verifique se o vendedor aparece

### Opção 4: Forçar Atualização (Mais Simples)

1. Abra o DevTools (F12)
2. Vá para a aba "Network"
3. Marque a opção "Disable cache"
4. Mantenha o DevTools aberto
5. Recarregue a página (Ctrl+Shift+R ou Ctrl+F5)

## Verificar se Funcionou

Após limpar o cache, você deve ver:
- **LUIZ HENRIQUE FELIX** com badge "Administrador"
- Email: consultorluizfelix@hotmail.com
- Botão "Reenviar senha"

## Por Que Isso Aconteceu?

O PWA (Progressive Web App) cacheia as respostas da API para funcionar offline. Quando fizemos correções no backend, o service worker continuou servindo a resposta antiga cacheada.

## Prevenção Futura

Para desenvolvedores: Ao fazer mudanças críticas na API, considere:
1. Incrementar a versão do service worker
2. Adicionar headers `Cache-Control: no-cache` em endpoints críticos
3. Usar versionamento de API (ex: `/api/v2/...`)
