# 🧪 TESTAR AGORA - Calendário Cabeleireiro v420

## ✅ CORREÇÃO APLICADA
- Criado componente específico `CalendarioCabeleireiro`
- Usa endpoints corretos: `/cabeleireiro/agendamentos/` e `/cabeleireiro/profissionais/`
- 3 visualizações: Dia, Semana, Mês
- Filtro por profissional
- Deploy v420 realizado com sucesso

---

## 🎯 COMO TESTAR

### 1️⃣ Acessar Dashboard
```
URL: https://lwksistemas.com.br/loja/regiane-5889/dashboard
Usuário: cabelo
```

### 2️⃣ Abrir Calendário
- Clique em **Ações Rápidas**
- Clique no botão **📅 Calendário** (azul)
- ✅ Modal fullscreen deve abrir

### 3️⃣ Verificar Agendamentos
**Resultado esperado**:
- ✅ Agendamentos criados devem aparecer no calendário
- ✅ Cores da loja aplicadas (fundo claro + borda colorida)
- ✅ Informações visíveis:
  - Nome do cliente
  - Serviço
  - Profissional
  - Horário
  - Valor (R$)

### 4️⃣ Testar Visualização DIA
- Clique no botão **Dia**
- ✅ Deve mostrar lista de horários (08:00 - 20:00)
- ✅ Agendamentos aparecem nos horários corretos
- ✅ Horários livres mostram "Horário livre"

### 5️⃣ Testar Visualização SEMANA
- Clique no botão **Semana**
- ✅ Deve mostrar grade 7 dias x 13 horários
- ✅ Cabeçalho mostra dias da semana (Dom, Seg, Ter...)
- ✅ Agendamentos aparecem nas células corretas
- ✅ Scroll horizontal funciona (se necessário)

### 6️⃣ Testar Visualização MÊS
- Clique no botão **Mês**
- ✅ Deve mostrar calendário mensal completo
- ✅ Dias com agendamentos mostram até 2 agendamentos
- ✅ Se houver mais de 2, mostra "+X mais"
- ✅ Agendamentos mostram horário + nome do cliente

### 7️⃣ Testar Filtro por Profissional
- No dropdown, selecione **Felipe Costa** (admin)
- ✅ Calendário deve filtrar apenas agendamentos desse profissional
- Selecione **Todos os profissionais**
- ✅ Calendário deve mostrar todos os agendamentos novamente

### 8️⃣ Testar Navegação
- Clique em **←** (anterior)
  - ✅ Deve voltar 1 dia/semana/mês (dependendo da visualização)
- Clique em **Hoje**
  - ✅ Deve voltar para o período atual
- Clique em **→** (próximo)
  - ✅ Deve avançar 1 dia/semana/mês

### 9️⃣ Fechar Calendário
- Clique no botão **✕ Fechar** (cinza, canto superior direito)
- ✅ Deve voltar ao dashboard

---

## 📊 CENÁRIOS DE TESTE

### Cenário 1: Sem Agendamentos
**Passos**:
1. Abrir calendário
2. Navegar para um dia/semana/mês sem agendamentos

**Resultado esperado**:
- ✅ Calendário vazio (sem erros)
- ✅ Horários livres visíveis
- ✅ Mensagem clara de que não há agendamentos

### Cenário 2: Com Agendamentos
**Passos**:
1. Criar agendamento via modal "Agendamentos"
2. Abrir calendário
3. Verificar se agendamento aparece

**Resultado esperado**:
- ✅ Agendamento aparece no calendário
- ✅ Informações corretas (cliente, serviço, profissional)
- ✅ Cores da loja aplicadas

### Cenário 3: Múltiplos Agendamentos no Mesmo Dia
**Passos**:
1. Criar 3+ agendamentos no mesmo dia
2. Abrir calendário em visualização "Mês"

**Resultado esperado**:
- ✅ Mostra 2 agendamentos
- ✅ Mostra "+1 mais" (ou "+X mais")

### Cenário 4: Filtro por Profissional
**Passos**:
1. Criar agendamentos com profissionais diferentes
2. Filtrar por um profissional específico

**Resultado esperado**:
- ✅ Mostra apenas agendamentos daquele profissional
- ✅ Outros agendamentos ficam ocultos

---

## 🐛 SE DER ERRO

### Calendário não abre
**Possível causa**: Erro de JavaScript
**Solução**: 
1. Abra Console do navegador (F12)
2. Verifique mensagens de erro
3. Copie e envie o erro

### Agendamentos não aparecem
**Possível causa**: Endpoint incorreto ou dados vazios
**Solução**:
1. Abra Network (F12 → Network)
2. Procure requisição: `GET /api/cabeleireiro/agendamentos/`
3. Verifique Response:
   - Status 200? ✅
   - Array vazio? Criar agendamentos primeiro
   - Erro 404/500? Problema no backend

### Profissionais não aparecem no filtro
**Possível causa**: Endpoint incorreto
**Solução**:
1. Abra Network (F12 → Network)
2. Procure requisição: `GET /api/cabeleireiro/profissionais/`
3. Verifique Response:
   - Status 200? ✅
   - Array vazio? Cadastrar funcionários primeiro

### Calendário trava ou fica lento
**Possível causa**: Muitos agendamentos
**Solução**: Normal se houver 100+ agendamentos no período

---

## 📝 CHECKLIST COMPLETO

### Funcionalidades Básicas
- [ ] Calendário abre sem erros
- [ ] Botão fechar funciona
- [ ] Título mostra período correto

### Visualizações
- [ ] Visualização Dia funciona
- [ ] Visualização Semana funciona
- [ ] Visualização Mês funciona
- [ ] Alternância entre visualizações é suave

### Dados
- [ ] Agendamentos aparecem no calendário
- [ ] Informações corretas (cliente, serviço, profissional, valor)
- [ ] Cores da loja aplicadas
- [ ] Horários corretos

### Filtros
- [ ] Dropdown de profissionais carrega
- [ ] Filtro por profissional funciona
- [ ] "Todos os profissionais" mostra todos

### Navegação
- [ ] Botão "Anterior" funciona
- [ ] Botão "Hoje" funciona
- [ ] Botão "Próximo" funciona
- [ ] Título atualiza ao navegar

### Responsividade
- [ ] Funciona em desktop
- [ ] Funciona em tablet
- [ ] Funciona em mobile (scroll horizontal se necessário)

---

## 📊 ENDPOINTS USADOS

### Agendamentos
```
GET /api/cabeleireiro/agendamentos/
Params: data_inicio, data_fim, profissional_id (opcional)

Response:
[
  {
    "id": 1,
    "cliente_nome": "João Silva",
    "profissional_nome": "Felipe Costa",
    "servico_nome": "Corte Masculino",
    "data": "2026-02-07",
    "horario": "14:00",
    "status": "agendado",
    "valor": "50.00"
  }
]
```

### Profissionais
```
GET /api/cabeleireiro/profissionais/

Response:
[
  {
    "id": 1,
    "nome": "Felipe Costa"
  }
]
```

---

## 🔍 LOGS DO NAVEGADOR

### Console (F12 → Console)
**Esperado**:
- Sem erros vermelhos
- Possíveis warnings amarelos (normais)

**Se houver erro**:
```
❌ Erro ao carregar agendamentos: ...
❌ Erro ao carregar profissionais: ...
```
→ Copie e envie o erro completo

### Network (F12 → Network)
**Requisições esperadas**:
1. `GET /api/cabeleireiro/profissionais/` → Status 200
2. `GET /api/cabeleireiro/agendamentos/?data_inicio=...&data_fim=...` → Status 200

---

## 💡 DICAS

### Criar Agendamentos de Teste
1. Vá em **Ações Rápidas** → **Agendamento**
2. Preencha:
   - Cliente: Selecione um cliente
   - Profissional: Felipe Costa
   - Serviço: Selecione um serviço
   - Data: Hoje ou amanhã
   - Horário: 14:00
3. Salve
4. Abra o calendário
5. ✅ Agendamento deve aparecer

### Testar Diferentes Períodos
- Crie agendamentos em dias diferentes
- Navegue pelo calendário
- Verifique se todos aparecem corretamente

---

**Documento criado**: 06/02/2026
**Deploy**: v420
**Status**: ✅ Pronto para testar
**URL**: https://lwksistemas.com.br/loja/regiane-5889/dashboard
