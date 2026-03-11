# Correção Timezone e Criação de Tarefas Mobile - Deploy v933

**Data**: 11/03/2026  
**Deploy Frontend**: v918 (Vercel)  
**Status**: ✅ Concluído

## Problemas Identificados

### 1. Fuso Horário Incorreto
- **Problema**: Ao clicar em um horário no calendário (ex: 16:00), o modal mostrava 3 horas a mais (19:00)
- **Causa**: FullCalendar retorna datas em UTC, mas o input datetime-local espera horário local
- **Diferença**: UTC vs America/Sao_Paulo = 3 horas

### 2. Criar Tarefas no Celular
- **Problema**: No mobile, não era possível criar tarefas clicando no calendário
- **Causa**: Faltava configuração de toque longo (long press) para dispositivos touch
- **Limitação**: Usuário só conseguia criar tarefas pelo botão flutuante

## Soluções Implementadas

### 1. Correção de Timezone

#### handleSelect (clicar em horário vazio)
```typescript
const handleSelect = useCallback((arg: { start: Date; end: Date }) => {
  // Corrigir timezone: FullCalendar retorna em UTC, precisamos converter para local
  const localDate = new Date(arg.start.getTime() - arg.start.getTimezoneOffset() * 60000);
  setModalAtividade(null);
  setForm({
    titulo: '',
    tipo: 'task',
    data: localDate.toISOString().slice(0, 16), // Agora mostra horário correto
    duracao_minutos: 60,
    observacoes: '',
  });
  setModalOpen(true);
  setError(null);
}, []);
```

#### handleEventClick (clicar em tarefa existente)
```typescript
const handleEventClick = useCallback((arg: { event: { extendedProps?: { atividade?: Atividade } }; jsEvent: MouseEvent }) => {
  arg.jsEvent.preventDefault();
  const a = arg.event.extendedProps?.atividade;
  if (!a) return;
  
  // Converter data UTC para local manualmente
  const dataUTC = new Date(a.data);
  const year = dataUTC.getFullYear();
  const month = String(dataUTC.getMonth() + 1).padStart(2, '0');
  const day = String(dataUTC.getDate()).padStart(2, '0');
  const hours = String(dataUTC.getHours()).padStart(2, '0');
  const minutes = String(dataUTC.getMinutes()).padStart(2, '0');
  const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
  
  setModalAtividade(a);
  setForm({
    titulo: a.titulo,
    tipo: a.tipo,
    data: localDateTime, // Horário correto
    duracao_minutos: a.duracao_minutos ?? 60,
    observacoes: a.observacoes || '',
  });
  setModalOpen(true);
  setError(null);
}, []);
```

#### openNovaAtividade (botão flutuante)
```typescript
const openNovaAtividade = useCallback(() => {
  const now = new Date();
  const start = new Date(now);
  start.setMinutes(Math.ceil(start.getMinutes() / 15) * 15);
  start.setSeconds(0, 0);
  
  // Converter para formato local sem ajuste de timezone
  const year = start.getFullYear();
  const month = String(start.getMonth() + 1).padStart(2, '0');
  const day = String(start.getDate()).padStart(2, '0');
  const hours = String(start.getHours()).padStart(2, '0');
  const minutes = String(start.getMinutes()).padStart(2, '0');
  const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
  
  setModalAtividade(null);
  setForm({
    titulo: '',
    tipo: 'task',
    data: localDateTime,
    duracao_minutos: 60,
    observacoes: '',
  });
  setModalOpen(true);
  setError(null);
}, []);
```

### 2. Suporte a Toque Simples no Mobile (Android/iOS)

Implementado evento `dateClick` do FullCalendar que funciona com toque simples:

```typescript
const handleDateClick = useCallback((arg: { date: Date; dateStr: string; allDay: boolean }) => {
  // Função para criar tarefa ao clicar em um dia/horário vazio
  // Funciona tanto no desktop quanto no mobile
  const clickedDate = arg.date;
  
  // Se for all-day, usar 9:00 como padrão
  if (arg.allDay) {
    clickedDate.setHours(9, 0, 0, 0);
  }
  
  // Converter para formato local
  const year = clickedDate.getFullYear();
  const month = String(clickedDate.getMonth() + 1).padStart(2, '0');
  const day = String(clickedDate.getDate()).padStart(2, '0');
  const hours = String(clickedDate.getHours()).padStart(2, '0');
  const minutes = String(clickedDate.getMinutes()).padStart(2, '0');
  const localDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
  
  setModalAtividade(null);
  setForm({
    titulo: '',
    tipo: 'task',
    data: localDateTime,
    duracao_minutos: 60,
    observacoes: '',
  });
  setModalOpen(true);
  setError(null);
}, []);
```

Configuração do FullCalendar:

```typescript
<FullCalendar
  // ... outras props
  dateClick={handleDateClick}  // Toque simples para criar tarefa
  eventClick={handleEventClick} // Toque simples para editar tarefa
  // ...
/>
```

## Como Funciona Agora

### Desktop:
1. Clique em um horário vazio → Modal abre com horário correto
2. Clique em uma tarefa existente → Modal abre com horário correto
3. Arraste tarefas → Funciona normalmente

### Mobile (Android/iOS):
1. **Toque simples em horário vazio** → Modal abre para criar tarefa ✅
2. **Toque simples em tarefa existente** → Modal abre para editar ✅
3. **Arrastar tarefas** → Funciona normalmente (toque e arraste) ✅
4. **Botão flutuante (+)** → Continua funcionando como alternativa ✅

## Testes Recomendados

### Desktop:
1. Clicar às 16:00 → Deve mostrar 16:00 no modal ✅
2. Editar tarefa existente → Deve mostrar horário correto ✅
3. Criar pelo botão → Deve usar horário atual arredondado ✅

### Mobile (Android):
1. Tocar em horário vazio → Deve abrir modal para criar tarefa ✅
2. Tocar em tarefa existente → Deve abrir modal para editar ✅
3. Arrastar tarefa → Deve permitir mover para outro horário ✅
4. Botão flutuante → Deve continuar funcionando ✅

## Arquivos Modificados

- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/calendario/page.tsx`
  - Função `handleDateClick`: Nova função para toque simples em horário vazio
  - Função `handleSelect`: Corrigido timezone
  - Função `handleEventClick`: Corrigido timezone
  - Função `openNovaAtividade`: Corrigido timezone
  - Props do FullCalendar: Adicionado `dateClick` para toque simples

## Notas Técnicas

- **Timezone**: Brasil usa America/Sao_Paulo (UTC-3)
- **FullCalendar**: Retorna datas em UTC por padrão
- **Input datetime-local**: Espera formato local sem timezone (YYYY-MM-DDTHH:mm)
- **Conversão**: `getTimezoneOffset()` retorna diferença em minutos entre UTC e local
- **dateClick**: Evento mais confiável para dispositivos touch do que long press
- **Android**: Toque simples funciona melhor que toque longo para criar tarefas

## Resultado

- Horários agora aparecem corretamente no modal (sem diferença de 3 horas)
- Usuários mobile podem criar tarefas tocando e segurando no calendário
- Experiência consistente entre desktop e mobile
- Mantém compatibilidade com todas as funcionalidades existentes
