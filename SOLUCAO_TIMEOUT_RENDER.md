# Solução: Timeout ao Trocar para Servidor Render

## 🐛 Problema

```
Erro: timeout of 10000ms exceeded
Erro: 503 Service Unavailable
```

**Causa:** Servidor Render (plano Free) está dormindo e demora 30-90s para acordar completamente (servidor + banco de dados), mas o frontend tem timeout de 10s.

## ✅ Solução Implementada

### Acordar Servidor Antes de Trocar

O sistema agora acorda o servidor Render automaticamente antes de trocar:

**Características:**
- ✅ 18 tentativas de verificação (até 120 segundos)
- ✅ Detecta status 503 (servidor acordando) e aguarda mais tempo
- ✅ Verifica se banco de dados está pronto (status 200)
- ✅ Modal com barra de progresso e mensagens informativas
- ✅ Tratamento especial para erro 503 (aguarda 8s ao invés de 5s)

**Fluxo:**
1. Usuário clica em "Trocar para Render"
2. Sistema mostra modal "Acordando servidor..."
3. Faz requisições de health check até servidor responder 200 OK
4. Aguarda 2 segundos extras para garantir estabilidade
5. Troca o servidor e recarrega a página

## 🔧 Detalhes Técnicos

### Tratamento de Status HTTP

O sistema trata diferentes respostas do servidor:

- **200 OK**: Servidor pronto, pode trocar
- **503 Service Unavailable**: Servidor acordando, aguarda 8s e tenta novamente
- **Timeout/Network Error**: Servidor dormindo, aguarda 5s e tenta novamente
- **Outros erros**: Continua tentando até limite de tentativas

### Configuração Atual

```typescript
const MAX_ATTEMPTS = 18;              // 18 tentativas
const ATTEMPT_INTERVAL = 5000;        // 5s entre tentativas normais
const ATTEMPT_INTERVAL_503 = 8000;    // 8s quando receber 503
const TOTAL_TIMEOUT = 120000;         // 120s total (2 minutos)
```

### Mensagens para o Usuário

- **Checking**: "Verificando status do servidor..."
- **Waking (normal)**: "Acordando servidor... (tentativa X/18)"
- **Waking (503)**: "Servidor acordando, inicializando banco de dados... (tentativa X/18)"
- **Ready**: "Servidor acordado e pronto!"
- **Error**: "Servidor não respondeu após várias tentativas"

## 📊 Tempo de Espera Esperado

| Situação | Tempo Aproximado |
|----------|------------------|
| Servidor já acordado | < 2 segundos |
| Servidor dormindo (cold start) | 30-60 segundos |
| Servidor + banco inicializando | 60-90 segundos |
| Timeout máximo | 120 segundos |

## 🎯 Arquivos Modificados

1. **frontend/lib/wake-up-render.ts**
   - Aumentado tentativas de 12 para 18
   - Aumentado timeout de 70s para 120s
   - Adicionado tratamento especial para status 503
   - Melhoradas mensagens de progresso

2. **frontend/components/SeletorServidorBackend.tsx**
   - Atualizada mensagem de tempo de espera (60s → 90s)
   - Modal com feedback visual melhorado

## 🚀 Como Usar

1. Acesse https://lwksistemas.com.br/superadmin/dashboard
2. Clique no botão de servidor (canto superior direito)
3. Selecione "Render"
4. Aguarde o modal de "Acordando servidor..." (pode demorar até 90s)
5. Sistema troca automaticamente quando pronto

## ⚠️ Observações Importantes

- **Plano Free**: Servidor dorme após 15 minutos de inatividade
- **Primeira requisição**: Sempre demora mais (cold start)
- **Requisições seguintes**: Rápidas se usadas dentro de 15 minutos
- **Upgrade para Starter ($25/mês)**: Elimina o problema (servidor sempre ativo)
