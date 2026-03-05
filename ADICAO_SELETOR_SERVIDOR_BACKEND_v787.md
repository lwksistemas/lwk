# Adição de Seletor de Servidor Backend - v787

**Data:** 2026-03-02  
**Status:** ✅ Concluído  
**Deploy:** https://lwksistemas.com.br

## 📋 Resumo

Adicionado componente no dashboard do superadmin que permite visualizar qual servidor backend está ativo (Heroku ou Render) e trocar entre eles manualmente. O componente também mostra o status online/offline de cada servidor em tempo real.

## 🎯 Objetivo

Permitir que o superadmin visualize e troque facilmente entre os servidores backend (Heroku principal e Render redundância) diretamente do dashboard, sem precisar alterar variáveis de ambiente ou código.

## ✅ Funcionalidades Implementadas

### 1. Componente SeletorServidorBackend

Novo componente com as seguintes funcionalidades:

- **Visualização do servidor ativo**: Mostra qual servidor está sendo usado (Heroku 🟣 ou Render 🔵)
- **Status em tempo real**: Indicador visual (verde/vermelho/amarelo) do status de cada servidor
- **Troca manual**: Permite trocar entre servidores com um clique
- **Verificação de saúde**: Verifica se o servidor está online antes de trocar
- **Persistência**: Salva a escolha no localStorage
- **Menu dropdown**: Interface limpa com menu que abre ao clicar

### 2. Integração com api-client

Atualizações no `api-client.ts`:

- **Função `getInitialAPI()`**: Carrega o servidor salvo no localStorage ao iniciar
- **Função `setBackendServer()`**: Permite trocar o servidor backend dinamicamente
- **Persistência automática**: Mantém a escolha entre recarregamentos

### 3. Health Check

Utiliza o endpoint existente `/api/superadmin/health/` para:
- Verificar se os servidores estão online
- Validar antes de trocar de servidor
- Atualizar status em tempo real

## 🎨 Interface

### Botão Principal
```
┌─────────────────────┐
│ 🟣  Backend         │
│     Heroku      🟢  │
└─────────────────────┘
```

### Menu Dropdown
```
┌──────────────────────────────────┐
│ Selecionar Servidor Backend     │
│ Escolha qual servidor usar       │
├──────────────────────────────────┤
│ 🟣 Heroku                   🟢   │
│    lwksistemas-...heroku...      │
│    [Ativo]                       │
├──────────────────────────────────┤
│ 🔵 Render                   🟢   │
│    lwksistemas.onrender.com      │
│                                  │
├──────────────────────────────────┤
│ 🔄 Verificar Status Novamente    │
└──────────────────────────────────┘
```

### Indicadores de Status
- 🟢 Verde: Servidor online
- 🔴 Vermelho: Servidor offline
- 🟡 Amarelo pulsante: Verificando...

## 📁 Arquivos Criados/Modificados

### Criados
1. `frontend/components/SeletorServidorBackend.tsx`
   - Componente completo com UI e lógica

### Modificados
1. `frontend/app/(dashboard)/superadmin/dashboard/page.tsx`
   - Importado e adicionado componente ao lado de NotificacoesSeguranca

2. `frontend/lib/api-client.ts`
   - Adicionada função `getInitialAPI()` para carregar servidor salvo
   - Adicionada função `setBackendServer()` para trocar servidor
   - Atualizado `currentAPI` para usar servidor salvo

## 🔄 Fluxo de Funcionamento

### Ao Carregar a Página
1. Componente verifica localStorage para servidor salvo
2. Se encontrado, atualiza `currentAPI` no api-client
3. Verifica status de ambos os servidores em paralelo
4. Exibe servidor ativo e status

### Ao Trocar de Servidor
1. Usuário clica no servidor desejado
2. Sistema verifica se servidor está online (timeout 5s)
3. Se online:
   - Salva escolha no localStorage
   - Atualiza `currentAPI` via `setBackendServer()`
   - Recarrega página para aplicar mudanças
4. Se offline:
   - Mostra alerta de erro
   - Mantém servidor atual

### Verificação de Status
1. Usuário clica em "Verificar Status Novamente"
2. Sistema faz requisições paralelas para ambos servidores
3. Atualiza indicadores visuais

## 🔧 Configuração

### Variáveis de Ambiente
```env
NEXT_PUBLIC_API_URL=https://lwksistemas-38ad47519238.herokuapp.com
NEXT_PUBLIC_API_BACKUP_URL=https://lwksistemas.onrender.com
```

### Servidores Configurados
```typescript
const SERVIDORES = {
  heroku: {
    nome: 'Heroku',
    url: process.env.NEXT_PUBLIC_API_URL,
    icone: '🟣',
  },
  render: {
    nome: 'Render',
    url: process.env.NEXT_PUBLIC_API_BACKUP_URL,
    icone: '🔵',
  },
};
```

## 🧪 Testes Necessários

1. ✅ Visualizar servidor ativo no dashboard
2. ✅ Ver status online/offline de cada servidor
3. ✅ Trocar de Heroku para Render
4. ✅ Trocar de Render para Heroku
5. ✅ Verificar que escolha persiste após reload
6. ✅ Tentar trocar para servidor offline (deve bloquear)
7. ✅ Verificar status manualmente
8. ✅ Verificar que requisições usam servidor correto

## 📊 Benefícios

- **Visibilidade**: Saber qual servidor está sendo usado
- **Controle**: Trocar manualmente em caso de problemas
- **Monitoramento**: Ver status de ambos servidores
- **Redundância**: Facilita uso do servidor backup
- **UX**: Interface simples e intuitiva
- **Persistência**: Mantém escolha entre sessões

## 🎯 Casos de Uso

1. **Manutenção do Heroku**: Trocar para Render temporariamente
2. **Problemas de performance**: Testar servidor alternativo
3. **Debugging**: Verificar se problema é específico de um servidor
4. **Monitoramento**: Acompanhar saúde de ambos servidores
5. **Failover manual**: Trocar rapidamente em caso de falha

## 🚀 Deploy

**Versão:** v787  
**URL:** https://lwksistemas.com.br  
**Data:** 2026-03-02

## 📝 Notas Técnicas

- Componente usa `localStorage` para persistência
- Health check tem timeout de 5 segundos
- Verificação de status é paralela (Promise.all)
- Recarrega página após trocar para garantir consistência
- Usa endpoint público `/api/superadmin/health/` (sem autenticação)
- Dark mode totalmente suportado
- Responsivo e acessível
