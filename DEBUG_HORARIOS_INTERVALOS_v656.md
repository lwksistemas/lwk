# Debug de Horários e Intervalos - v656

## Problema Reportado
Ao mudar para visualização mensal, os intervalos aparecem mas os horários de entrada/saída estão errados para todos os profissionais.

## Análise do Problema

### Estrutura de Dados
1. **Backend (Django)**: `dia_semana` usa valores 0-6 onde:
   - 0 = Segunda-feira
   - 1 = Terça-feira
   - ...
   - 6 = Domingo

2. **JavaScript**: `getDay()` retorna valores 0-6 onde:
   - 0 = Domingo
   - 1 = Segunda-feira
   - ...
   - 6 = Sábado

3. **FullCalendar**: `daysOfWeek` usa valores 0-6 onde:
   - 0 = Domingo
   - 1 = Segunda-feira
   - ...
   - 6 = Sábado

### Conversões Implementadas
- **Backend → FullCalendar**: `fcDay = dia_semana === 6 ? 0 : dia_semana + 1`
- **JavaScript → Backend**: `diaBackend = diaSemana === 0 ? 6 : diaSemana - 1`

## Mudanças Implementadas (v656)

### 1. Logs de Debug Extensivos
Adicionados logs detalhados em todas as funções críticas:

#### `carregarHorarios()`
- Log dos dados RAW retornados pela API em formato JSON
- Permite verificar o formato exato dos campos `hora_entrada`, `hora_saida`, `intervalo_inicio`, `intervalo_fim`

#### `getBusinessHours()`
- Log dos horários de trabalho recebidos
- Log da conversão de cada dia (Backend → FullCalendar)
- Log do resultado final do businessHours

#### `getHiddenDays()`
- Log dos dias ativos no formato FullCalendar
- Log dos dias que serão ocultados

#### `getSlotMinTime()` e `getSlotMaxTime()`
- Log dos horários mínimo e máximo calculados

#### Criação de Intervalos
- Log detalhado para cada dia processado:
  - Data em formato brasileiro
  - Dia da semana em formato JS e Backend
  - Horário encontrado (JSON completo)
  - Intervalo calculado (início e fim)
  - Evento criado
- Log do total de intervalos criados

### 2. Validações de Tipo
Adicionadas verificações `typeof` antes de usar `.slice()` nos horários:
```typescript
const intervaloInicio = typeof horario.intervalo_inicio === 'string' 
  ? horario.intervalo_inicio.slice(0, 5) 
  : '12:00';
```

Isso previne erros caso o Django retorne os horários em formato diferente de string.

### 3. Logs na Criação de Intervalos
Para cada dia dos próximos 30 dias:
- Verifica se há horário configurado
- Se houver intervalo, cria o evento
- Loga cada passo do processo

## Como Testar

### 1. Acessar a Agenda
Acesse: https://lwksistemas.com.br/loja/clinica-luiz-000172/agenda

### 2. Abrir Console do Navegador
- Chrome/Edge: F12 ou Ctrl+Shift+I
- Firefox: F12 ou Ctrl+Shift+K
- Safari: Cmd+Option+I

### 3. Selecionar um Profissional
Ao selecionar um profissional no dropdown, você verá logs como:

```
📅 Horários de trabalho carregados (RAW): [
  {
    "id": 123,
    "professional": 72,
    "dia_semana": 2,
    "dia_semana_display": "Quarta-feira",
    "hora_entrada": "08:00:00",
    "hora_saida": "18:00:00",
    "intervalo_inicio": "12:00:00",
    "intervalo_fim": "13:00:00",
    "ativo": true
  }
]

🏢 Calculando businessHours com horários: [...]
  Dia backend 2 → FC day 3: 08:00 - 18:00

🚫 Dias ativos (FC): [3]
🚫 Dias ocultos (FC): [0, 1, 2, 4, 5, 6]

⏰ Horário mínimo calculado: 08:00
⏰ Horário máximo calculado: 18:00

🍽️ Criando intervalos para profissional: 72
📋 Horários disponíveis: [...]
📅 Data: 19/02/2026, JS day: 4, Backend day: 3
❌ Nenhum horário encontrado para dia 3
📅 Data: 20/02/2026, JS day: 5, Backend day: 4
❌ Nenhum horário encontrado para dia 4
📅 Data: 21/02/2026, JS day: 6, Backend day: 5
❌ Nenhum horário encontrado para dia 5
📅 Data: 22/02/2026, JS day: 0, Backend day: 6
❌ Nenhum horário encontrado para dia 6
📅 Data: 23/02/2026, JS day: 1, Backend day: 0
❌ Nenhum horário encontrado para dia 0
📅 Data: 24/02/2026, JS day: 2, Backend day: 1
❌ Nenhum horário encontrado para dia 1
📅 Data: 25/02/2026, JS day: 3, Backend day: 2
✅ Horário encontrado para dia 2: {...}
⏰ Intervalo: 12:00 - 13:00
✅ Intervalo criado para 2026-02-25: {...}

📊 Total de intervalos criados: 4
```

### 4. O Que Verificar nos Logs

#### A. Formato dos Horários
Verifique se `hora_entrada`, `hora_saida`, `intervalo_inicio`, `intervalo_fim` estão no formato:
- ✅ Correto: `"08:00:00"` ou `"08:00"`
- ❌ Incorreto: Objeto, null quando deveria ter valor, etc.

#### B. Conversão de Dias
Para cada dia, verifique se a conversão está correta:
- Se o profissional trabalha na Quarta-feira (dia_semana=2 no backend)
- O log deve mostrar: `Dia backend 2 → FC day 3`
- E ao processar datas, quarta-feira deve ter `JS day: 3, Backend day: 2`

#### C. Intervalos Criados
- Verifique se os intervalos estão sendo criados para os dias corretos
- Verifique se os horários dos intervalos estão corretos
- Compare com a configuração em "Horários de trabalho" do profissional

### 5. Testar Diferentes Visualizações
- Visualização Semanal (timeGridWeek)
- Visualização Diária (timeGridDay)
- Visualização Mensal (dayGridMonth)

Em cada visualização, verifique:
- Os dias corretos aparecem
- Os horários de início/fim estão corretos
- Os intervalos aparecem nos horários corretos

## Possíveis Problemas e Soluções

### Problema 1: Horários em Formato Errado
**Sintoma**: Logs mostram horários como objetos ou formato diferente de string

**Solução**: Ajustar o serializer no backend para garantir formato string "HH:MM:SS"

### Problema 2: Conversão de Dias Incorreta
**Sintoma**: Profissional configurado para Quarta mas aparece em outro dia

**Solução**: Verificar a lógica de conversão:
- Backend → FullCalendar: `dia_semana === 6 ? 0 : dia_semana + 1`
- JavaScript → Backend: `diaSemana === 0 ? 6 : diaSemana - 1`

### Problema 3: Intervalos Não Aparecem
**Sintoma**: Log mostra "Nenhum horário encontrado" para dias que deveriam ter

**Solução**: Verificar se:
- O horário está marcado como `ativo: true`
- O `dia_semana` está correto no banco de dados
- O profissional tem `intervalo_inicio` e `intervalo_fim` configurados

### Problema 4: Horários Min/Max Errados
**Sintoma**: Calendário mostra horários fora do período de trabalho

**Solução**: Verificar logs de `getSlotMinTime()` e `getSlotMaxTime()` e comparar com horários configurados

## Próximos Passos

1. **Coletar Logs**: Selecione cada profissional e copie os logs do console
2. **Analisar Dados**: Verifique se os dados estão no formato esperado
3. **Identificar Padrão**: Se o problema ocorre com todos ou apenas alguns profissionais
4. **Reportar**: Envie os logs para análise detalhada

## Deploy Realizado

- **Frontend**: v656 - Deploy concluído no Vercel
- **URL**: https://lwksistemas.com.br
- **Data**: 19/02/2026

## Arquivos Modificados

- `frontend/app/(dashboard)/loja/[slug]/agenda/page.tsx`
  - Adicionados logs extensivos em todas as funções de horários
  - Adicionadas validações de tipo para prevenir erros
  - Melhorada a lógica de criação de intervalos com logs detalhados
