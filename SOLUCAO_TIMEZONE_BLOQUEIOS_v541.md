# Solução: Bloqueios Aparecem 1 Dia Antes

## Problema Confirmado
- Backend salva CORRETAMENTE: `data_inicio=2026-02-15`
- Frontend exibe INCORRETAMENTE: dia 14

## Causa Raiz
O frontend está convertendo a string de data para objeto Date com timezone UTC, causando mudança de dia.

```javascript
// ❌ ERRADO - causa conversão de timezone
new Date("2026-02-15") 
// Retorna: 2026-02-15T00:00:00Z (UTC)
// No Brasil (UTC-3): 2026-02-14T21:00:00-03:00 (dia 14!)
```

## Solução
Não converter a string de data para Date. Trabalhar diretamente com strings no formato `YYYY-MM-DD`.

### Opção 1: Comparar strings diretamente (RECOMENDADO)
```typescript
// ✅ CORRETO - compara strings
const dataStr = "2026-02-15";
if (dataStr >= bloqueio.data_inicio && dataStr <= bloqueio.data_fim) {
  // Bloqueio ativo
}
```

### Opção 2: Criar Date no timezone local
```typescript
// ✅ CORRETO - força timezone local
const [ano, mes, dia] = bloqueio.data_inicio.split('-').map(Number);
const data = new Date(ano, mes - 1, dia); // Cria no timezone local
```

## Arquivos a Corrigir
1. `frontend/components/calendario/CalendarioAgendamentos.tsx`
   - Função que renderiza bloqueios no calendário
   - Verificar se usa `new Date()` com strings de data

2. Qualquer componente que exiba datas de bloqueios

## Status
- ✅ Backend: Funcionando perfeitamente
- ⚠️ Frontend: Precisa correção na renderização

## Próximos Passos
1. Localizar onde o calendário renderiza os bloqueios
2. Garantir que não converte strings de data para Date
3. Usar comparação de strings ou Date no timezone local
