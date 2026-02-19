# Diagnóstico - Horários Dra. Marina Souza

## Configuração Esperada

**Profissional**: Dra. Marina Souza

**Horários configurados**:
- **Terça-feira**: 09:00 - 18:00 | Intervalo: 12:00 - 13:00
- **Quarta-feira**: 08:00 - 18:00 | Intervalo: 12:00 - 13:00

## Como Diagnosticar

### Passo 1: Abrir o Console do Navegador

1. Acesse: https://lwksistemas.com.br/loja/clinica-luiz-000172/agenda
2. Pressione **F12** (ou Ctrl+Shift+I no Windows/Linux, Cmd+Option+I no Mac)
3. Clique na aba **Console**

### Passo 2: Selecionar a Profissional

1. No dropdown "Profissional", selecione **Dra. Marina Souza**
2. Aguarde alguns segundos
3. Observe os logs que aparecem no console

### Passo 3: Analisar os Logs

Você deve ver logs como estes:

```
📅 Horários de trabalho carregados (RAW): [
  {
    "id": 123,
    "professional": 45,
    "dia_semana": 1,
    "dia_semana_display": "Terça-feira",
    "hora_entrada": "09:00:00",
    "hora_saida": "18:00:00",
    "intervalo_inicio": "12:00:00",
    "intervalo_fim": "13:00:00",
    "ativo": true
  },
  {
    "id": 124,
    "professional": 45,
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
  Dia backend 1 → FC day 2: 09:00 - 18:00
  Dia backend 2 → FC day 3: 08:00 - 18:00

🚫 Dias ativos (FC): [2, 3]
🚫 Dias ocultos (FC): [0, 1, 4, 5, 6]

⏰ Horário mínimo calculado: 08:00
⏰ Horário máximo calculado: 18:00

🍽️ Criando intervalos para profissional: 45
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
✅ Horário encontrado para dia 1: {...}
⏰ Intervalo: 12:00 - 13:00
✅ Intervalo criado para 2026-02-24: {...}

📅 Data: 25/02/2026, JS day: 3, Backend day: 2
✅ Horário encontrado para dia 2: {...}
⏰ Intervalo: 12:00 - 13:00
✅ Intervalo criado para 2026-02-25: {...}

📊 Total de intervalos criados: 8
```

## O Que Verificar

### 1. Horários RAW da API

**Verifique**:
- ✅ `dia_semana: 1` = Terça-feira
- ✅ `dia_semana: 2` = Quarta-feira
- ✅ `hora_entrada`, `hora_saida`, `intervalo_inicio`, `intervalo_fim` estão corretos
- ✅ `ativo: true` para ambos os dias

**Se estiver errado**:
- Os horários não foram salvos corretamente
- Volte em "Horários de trabalho" e salve novamente

### 2. Conversão de Dias

**Verifique**:
- ✅ Dia backend 1 → FC day 2 (Terça-feira)
- ✅ Dia backend 2 → FC day 3 (Quarta-feira)

**Tabela de Conversão**:
```
Backend → FullCalendar → Dia da Semana
0       → 1            → Segunda-feira
1       → 2            → Terça-feira
2       → 3            → Quarta-feira
3       → 4            → Quinta-feira
4       → 5            → Sexta-feira
5       → 6            → Sábado
6       → 0            → Domingo
```

### 3. Dias Ocultos

**Verifique**:
- ✅ Dias ativos: [2, 3] = Terça e Quarta
- ✅ Dias ocultos: [0, 1, 4, 5, 6] = Domingo, Segunda, Quinta, Sexta, Sábado

**Se estiver errado**:
- A conversão de dias está incorreta
- Copie os logs e envie para análise

### 4. Horários Min/Max

**Verifique**:
- ✅ Horário mínimo: 08:00 (menor horário de entrada)
- ✅ Horário máximo: 18:00 (maior horário de saída)

**Se estiver errado**:
- Os horários não estão sendo lidos corretamente
- Copie os logs e envie para análise

### 5. Intervalos Criados

**Verifique**:
- ✅ Para cada terça-feira nos próximos 30 dias: intervalo 12:00-13:00
- ✅ Para cada quarta-feira nos próximos 30 dias: intervalo 12:00-13:00
- ✅ Total de intervalos = número de terças + quartas nos próximos 30 dias

**Se estiver errado**:
- Verifique qual dia está dando "❌ Nenhum horário encontrado"
- Compare o `Backend day` com o `dia_semana` nos horários RAW

## Visualizações do Calendário

### Visualização Diária (timeGridDay)

**O que deve aparecer**:
- Se for terça-feira: horário 09:00-18:00, intervalo 12:00-13:00
- Se for quarta-feira: horário 08:00-18:00, intervalo 12:00-13:00
- Outros dias: não deve aparecer (dia oculto)

### Visualização Semanal (timeGridWeek)

**O que deve aparecer**:
- Apenas colunas de Terça e Quarta
- Terça: horário 09:00-18:00, intervalo 12:00-13:00 (bloco laranja)
- Quarta: horário 08:00-18:00, intervalo 12:00-13:00 (bloco laranja)
- Outros dias: ocultos

### Visualização Mensal (dayGridMonth)

**O que deve aparecer**:
- Apenas terças e quartas com cor de fundo diferente (businessHours)
- Intervalos aparecem como eventos "🍽️ Intervalo" nas terças e quartas
- Outros dias: sem cor de fundo

## Problemas Comuns

### Problema 1: Nenhum Dia Aparece

**Sintoma**: Calendário vazio ou todos os dias ocultos

**Causa**: Horários não foram salvos ou `ativo: false`

**Solução**:
1. Verifique os logs RAW
2. Se não houver horários, configure novamente
3. Certifique-se de clicar em "Salvar"

### Problema 2: Dias Errados Aparecem

**Sintoma**: Segunda aparece ao invés de Terça

**Causa**: Conversão de dias incorreta

**Solução**:
1. Verifique os logs de conversão
2. Compare `dia_semana` (backend) com `FC day` (FullCalendar)
3. Copie os logs e envie para análise

### Problema 3: Intervalos Não Aparecem

**Sintoma**: Horários corretos mas sem bloco laranja de intervalo

**Causa**: `intervalo_inicio` ou `intervalo_fim` null/vazio

**Solução**:
1. Verifique os logs RAW
2. Se `intervalo_inicio: null`, configure novamente
3. Certifique-se de preencher os campos de intervalo

### Problema 4: Horários Min/Max Errados

**Sintoma**: Calendário mostra 07:00-20:00 ao invés de 08:00-18:00

**Causa**: Horários não estão sendo lidos corretamente

**Solução**:
1. Verifique os logs de cálculo
2. Verifique se `hora_entrada` e `hora_saida` estão no formato correto
3. Copie os logs e envie para análise

## Exemplo de Logs Corretos

```
📅 Horários de trabalho carregados (RAW): [
  {
    "id": 123,
    "professional": 45,
    "dia_semana": 1,
    "dia_semana_display": "Terça-feira",
    "hora_entrada": "09:00:00",
    "hora_saida": "18:00:00",
    "intervalo_inicio": "12:00:00",
    "intervalo_fim": "13:00:00",
    "ativo": true
  },
  {
    "id": 124,
    "professional": 45,
    "dia_semana": 2,
    "dia_semana_display": "Quarta-feira",
    "hora_entrada": "08:00:00",
    "hora_saida": "18:00:00",
    "intervalo_inicio": "12:00:00",
    "intervalo_fim": "13:00:00",
    "ativo": true
  }
]

🏢 Calculando businessHours com horários: [
  {
    "id": 123,
    "professional": 45,
    "dia_semana": 1,
    "dia_semana_display": "Terça-feira",
    "hora_entrada": "09:00:00",
    "hora_saida": "18:00:00",
    "intervalo_inicio": "12:00:00",
    "intervalo_fim": "13:00:00",
    "ativo": true
  },
  {
    "id": 124,
    "professional": 45,
    "dia_semana": 2,
    "dia_semana_display": "Quarta-feira",
    "hora_entrada": "08:00:00",
    "hora_saida": "18:00:00",
    "intervalo_inicio": "12:00:00",
    "intervalo_fim": "13:00:00",
    "ativo": true
  }
]
  Dia backend 1 → FC day 2: 09:00 - 18:00
  Dia backend 2 → FC day 3: 08:00 - 18:00
🏢 BusinessHours final: [
  {
    "daysOfWeek": [2],
    "startTime": "09:00",
    "endTime": "18:00"
  },
  {
    "daysOfWeek": [3],
    "startTime": "08:00",
    "endTime": "18:00"
  }
]

🚫 Dias ativos (FC): [2, 3]
🚫 Dias ocultos (FC): [0, 1, 4, 5, 6]

⏰ Horário mínimo calculado: 08:00
⏰ Horário máximo calculado: 18:00

🍽️ Criando intervalos para profissional: 45
📋 Horários disponíveis: [...]

[... logs de criação de intervalos para cada dia ...]

📊 Total de intervalos criados: 8
```

## Próximos Passos

1. ✅ Abra o console (F12)
2. ✅ Selecione Dra. Marina Souza
3. ✅ Copie TODOS os logs que aparecem
4. ✅ Cole os logs em um arquivo de texto
5. ✅ Envie para análise

Com os logs, poderei identificar exatamente onde está o problema!

## Teste Rápido

Para testar rapidamente se está funcionando:

1. Acesse a agenda
2. Selecione Dra. Marina Souza
3. Mude para visualização **Semanal** (botão "timeGridWeek")
4. Você deve ver:
   - Apenas 2 colunas: Terça e Quarta
   - Terça: 09:00-18:00 com bloco laranja 12:00-13:00
   - Quarta: 08:00-18:00 com bloco laranja 12:00-13:00

Se não estiver assim, copie os logs do console e envie!
