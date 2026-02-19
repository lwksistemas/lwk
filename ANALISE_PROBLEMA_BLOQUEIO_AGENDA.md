# 🐛 Análise: Problema de Bloqueio na Agenda

**Data:** 19/02/2026  
**Problema Reportado:** Ao bloquear um período curto (ex: 14h-16h) em vários dias, o sistema bloqueia o dia inteiro

---

## 🔍 Investigação

### 1. Frontend - Modal de Bloqueio
**Arquivo:** `frontend/components/clinica-beleza/ModalBloqueioHorario.tsx`

✅ **CORRETO** - O modal envia corretamente:
```typescript
const body = {
  data_inicio: new Date(dataInicio).toISOString(), // Ex: 2026-02-19T14:00:00.000Z
  data_fim: new Date(dataFim).toISOString(),       // Ex: 2026-02-19T16:00:00.000Z
  motivo: motivoFinal.trim(),
  // ...
};
```

### 2. Backend - API de Bloqueio
**Arquivo:** `backend/clinica_beleza/views.py` (linha 931-960)

✅ **CORRETO** - A API salva exatamente o que recebe:
```python
def post(self, request):
    serializer = BloqueioHorarioSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()  # Salva data_inicio e data_fim como recebido
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### 3. Backend - Serializer
**Arquivo:** `backend/clinica_beleza/serializers.py` (linha 298-310)

✅ **CORRETO** - Retorna os campos sem modificação:
```python
class BloqueioHorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloqueioHorario
        fields = [
            'id', 'professional', 'professional_name',
            'data_inicio', 'data_fim', 'motivo', 'observacoes', 'criado_em',
        ]
```

### 4. Frontend - Exibição no Calendário
**Arquivo:** `frontend/app/(dashboard)/loja/[slug]/agenda/page.tsx` (linha 280-295)

✅ **CORRETO** - Usa as datas diretamente:
```typescript
const bloqueiosAsEvents = bloqueiosList.map((b: BloqueioHorario) => ({
  id: `bloqueio-${b.id}`,
  title: `🚫 ${b.motivo}`,
  start: b.data_inicio,  // Usa diretamente do backend
  end: b.data_fim,       // Usa diretamente do backend
  backgroundColor: COR_BLOQUEIO.bg,
  borderColor: COR_BLOQUEIO.border,
  textColor: "#fff",
  editable: false,
  // ...
}));
```

---

## 🤔 Possíveis Causas

### Hipótese 1: Problema de Timezone
As datas podem estar sendo convertidas incorretamente devido a diferenças de timezone entre:
- Navegador do usuário
- Servidor (Heroku)
- Banco de dados (PostgreSQL)

**Exemplo:**
- Usuário seleciona: `2026-02-19 14:00` (horário local)
- Frontend envia: `2026-02-19T14:00:00.000Z` (UTC)
- Backend salva: `2026-02-19T14:00:00+00:00` (UTC)
- FullCalendar exibe: Pode interpretar como dia inteiro se não tiver hora

### Hipótese 2: FullCalendar allDay
O FullCalendar pode estar interpretando eventos sem hora específica como "dia inteiro".

### Hipótese 3: Formato de Data
O backend pode estar retornando datas sem timezone ou em formato que o FullCalendar não reconhece corretamente.

---

## 🧪 Teste para Confirmar

Vou adicionar logs detalhados para ver exatamente o que está acontecendo:

1. Log no modal antes de enviar
2. Log na resposta da API
3. Log ao formatar para o calendário
4. Log do que o FullCalendar recebe

---

## 💡 Solução Proposta

### Opção 1: Garantir Timezone Correto
Modificar o serializer para sempre retornar datas com timezone explícito:

```python
# backend/clinica_beleza/serializers.py
class BloqueioHorarioSerializer(serializers.ModelSerializer):
    data_inicio = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    data_fim = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
```

### Opção 2: Forçar Formato no Frontend
Garantir que o FullCalendar receba datas no formato correto:

```typescript
const bloqueiosAsEvents = bloqueiosList.map((b: BloqueioHorario) => ({
  id: `bloqueio-${b.id}`,
  title: `🚫 ${b.motivo}`,
  start: new Date(b.data_inicio).toISOString(),
  end: new Date(b.data_fim).toISOString(),
  allDay: false,  // Forçar que não é dia inteiro
  // ...
}));
```

### Opção 3: Adicionar allDay: false Explicitamente
O FullCalendar pode estar inferindo `allDay: true` se não especificado:

```typescript
const bloqueiosAsEvents = bloqueiosList.map((b: BloqueioHorario) => ({
  // ...
  allDay: false,  // ADICIONAR ESTA LINHA
  // ...
}));
```

---

## 🎯 Próximos Passos

1. ✅ Adicionar logs para debug
2. ✅ Testar criação de bloqueio e ver logs
3. ✅ Identificar onde está o problema exato
4. ✅ Aplicar correção
5. ✅ Testar em produção

---

**Status:** 🔍 EM INVESTIGAÇÃO
