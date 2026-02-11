# 📅 API DE AGENDA - CLÍNICA DA BELEZA (v570)

**Data:** 11/02/2026  
**Deploy Backend:** v570  
**Base URL:** `https://lwksistemas.com.br/api/clinica-beleza/`

---

## 🎯 ENDPOINTS DA AGENDA

### 1. Listar Eventos do Calendário

**GET** `/api/clinica-beleza/agenda/`

**Parâmetros Query:**
- `start` (opcional): Data inicial no formato `YYYY-MM-DD`
- `end` (opcional): Data final no formato `YYYY-MM-DD`
- `professional` (opcional): ID do profissional para filtrar

**Exemplo de Request:**
```bash
GET /api/clinica-beleza/agenda/?start=2026-02-01&end=2026-02-28&professional=1
Authorization: Bearer {token}
```

**Exemplo de Response:**
```json
[
  {
    "id": 1,
    "title": "Mariana Lopes - Limpeza de Pele",
    "start": "2026-02-11T09:00:00Z",
    "end": "2026-02-11T10:00:00Z",
    "backgroundColor": "#10b981",
    "borderColor": "#10b981",
    "textColor": "#ffffff",
    "status": "CONFIRMED",
    "notes": "",
    "patient": 1,
    "patient_name": "Mariana Lopes",
    "patient_phone": "(11) 91234-5678",
    "professional": 2,
    "professional_name": "Dra. Julia Santos",
    "professional_id": 2,
    "procedure": 1,
    "procedure_name": "Limpeza de Pele",
    "procedure_duration": 60,
    "procedure_price": "150.00"
  }
]
```

---

### 2. Criar Novo Agendamento

**POST** `/api/clinica-beleza/agenda/create/`

**Body:**
```json
{
  "date": "2026-02-15T14:00:00Z",
  "status": "SCHEDULED",
  "patient": 1,
  "professional": 2,
  "procedure": 3,
  "notes": "Primeira sessão"
}
```

**Response:** Retorna o evento criado no formato da agenda

---

### 3. Atualizar Data/Hora (Drag & Drop)

**PATCH** `/api/clinica-beleza/agenda/{id}/update/`

**Body:**
```json
{
  "date": "2026-02-15T15:30:00Z"
}
```

**Uso:** Quando o usuário arrasta um evento no calendário

---

### 4. Deletar Agendamento

**DELETE** `/api/clinica-beleza/agenda/{id}/delete/`

**Response:** `204 No Content`

---

## 🎨 CORES POR STATUS

| Status | Cor | Hex |
|--------|-----|-----|
| ✅ Confirmado | Verde | `#10b981` |
| ⚠️ Pendente | Amarelo | `#f59e0b` |
| 📅 Agendado | Azul | `#3b82f6` |
| 🔄 Em Atendimento | Roxo | `#8b5cf6` |
| ✔️ Concluído | Cinza | `#6b7280` |
| ❌ Cancelado | Vermelho | `#ef4444` |
| 🚫 Faltou | Vermelho Escuro | `#dc2626` |

---

## 📊 FORMATO DOS EVENTOS

Os eventos são retornados no formato compatível com **FullCalendar**:

```typescript
interface AgendaEvent {
  // Campos do FullCalendar
  id: number;
  title: string;              // "Paciente - Procedimento"
  start: string;              // ISO 8601 datetime
  end: string;                // Calculado: start + duration
  backgroundColor: string;    // Cor baseada no status
  borderColor: string;
  textColor: string;
  
  // Dados extras
  status: string;
  notes: string;
  
  // Paciente
  patient: number;
  patient_name: string;
  patient_phone: string;
  
  // Profissional
  professional: number;
  professional_name: string;
  professional_id: number;
  
  // Procedimento
  procedure: number;
  procedure_name: string;
  procedure_duration: number;  // minutos
  procedure_price: string;     // decimal
}
```

---

## 🔧 FUNCIONALIDADES IMPLEMENTADAS

### ✅ Backend Pronto

1. **Listagem de Eventos**
   - Filtro por período (start/end)
   - Filtro por profissional
   - Formato FullCalendar

2. **CRUD Completo**
   - Criar agendamento
   - Atualizar data/hora (drag & drop)
   - Deletar agendamento

3. **Cálculo Automático**
   - Horário de fim baseado na duração do procedimento
   - Cores automáticas baseadas no status

4. **Dados Relacionados**
   - Paciente (nome, telefone)
   - Profissional (nome, especialidade)
   - Procedimento (nome, duração, preço)

---

## 🚀 PRÓXIMOS PASSOS (Frontend)

Aguardando códigos do frontend para implementar:

1. **Calendário Visual**
   - Visualização mensal/semanal/diária
   - Drag & drop para reagendar
   - Clique para ver detalhes

2. **Modal de Criação**
   - Formulário para novo agendamento
   - Seleção de paciente, profissional, procedimento
   - Validação de horários disponíveis

3. **Modal de Edição**
   - Editar detalhes do agendamento
   - Alterar status
   - Adicionar observações

4. **Filtros**
   - Por profissional
   - Por status
   - Por período

5. **Responsividade**
   - Mobile-first
   - Visualização adaptada para celular

---

## 📝 EXEMPLO DE USO

### Buscar eventos de fevereiro de 2026

```javascript
const response = await fetch(
  'https://lwksistemas.com.br/api/clinica-beleza/agenda/?start=2026-02-01&end=2026-02-28',
  {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }
);

const events = await response.json();
```

### Criar novo agendamento

```javascript
const response = await fetch(
  'https://lwksistemas.com.br/api/clinica-beleza/agenda/create/',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      date: '2026-02-15T14:00:00Z',
      status: 'SCHEDULED',
      patient: 1,
      professional: 2,
      procedure: 3
    })
  }
);

const newEvent = await response.json();
```

### Atualizar data (drag & drop)

```javascript
const response = await fetch(
  `https://lwksistemas.com.br/api/clinica-beleza/agenda/${eventId}/update/`,
  {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      date: '2026-02-15T15:30:00Z'
    })
  }
);

const updatedEvent = await response.json();
```

---

## ✅ STATUS

- ✅ Backend API completo
- ✅ Serializers com formato FullCalendar
- ✅ Suporte a drag & drop
- ✅ Filtros por período e profissional
- ✅ Cálculo automático de horário de fim
- ✅ Cores automáticas por status
- ⏳ Aguardando códigos do frontend

**Pronto para receber os códigos do frontend!** 🚀
