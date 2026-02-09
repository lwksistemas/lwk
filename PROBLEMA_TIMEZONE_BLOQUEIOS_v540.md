# Problema: Data do Bloqueio Aparece 1 Dia Antes

## Situação
- Usuário marca bloqueio para dia 13
- Bloqueio aparece no calendário no dia 12

## Causa Raiz
O problema está na **exibição das datas no frontend**, não no backend.

Quando o backend retorna:
```json
{
  "data_inicio": "2026-02-13",
  "data_fim": "2026-02-13"
}
```

O JavaScript pode interpretar essa string como:
```javascript
new Date("2026-02-13") // Interpreta como 2026-02-13T00:00:00Z (UTC)
```

No Brasil (UTC-3), isso vira:
```javascript
// 2026-02-12T21:00:00-03:00 (21h do dia 12)
```

## Solução
Garantir que o frontend trate as datas como "date only" sem conversão de timezone.

### Opção 1: Usar toLocaleDateString sem conversão
```typescript
// ❌ ERRADO - converte timezone
const data = new Date(bloqueio.data_inicio);

// ✅ CORRETO - trata como string
const data = bloqueio.data_inicio; // "2026-02-13"
```

### Opção 2: Forçar timezone local ao criar Date
```typescript
// ✅ CORRETO - força timezone local
const [ano, mes, dia] = bloqueio.data_inicio.split('-').map(Number);
const data = new Date(ano, mes - 1, dia); // Cria no timezone local
```

## Arquivos Afetados
- `frontend/components/calendario/CalendarioAgendamentos.tsx`
- Qualquer lugar que exiba `bloqueio.data_inicio` ou `bloqueio.data_fim`

## Status
- ✅ Backend: Correto (salva e retorna datas sem timezone)
- ⚠️ Frontend: Precisa ajustar exibição das datas
