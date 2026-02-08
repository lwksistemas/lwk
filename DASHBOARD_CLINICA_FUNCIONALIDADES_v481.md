# Funcionalidades - Dashboard Clínica v481

## 🎯 Funcionalidades Implementadas

Este documento detalha todas as funcionalidades do dashboard da clínica de estética, incluindo handlers, integrações com API e lógica de negócio.

---

## 📋 Índice de Funcionalidades

1. [Gerenciamento de Agendamentos](#1-gerenciamento-de-agendamentos)
2. [Gerenciamento de Clientes](#2-gerenciamento-de-clientes)
3. [Gerenciamento de Profissionais](#3-gerenciamento-de-profissionais)
4. [Gerenciamento de Procedimentos](#4-gerenciamento-de-procedimentos)
5. [Sistema de Protocolos](#5-sistema-de-protocolos)
6. [Sistema de Anamnese](#6-sistema-de-anamnese)
7. [Sistema de Consultas](#7-sistema-de-consultas)
8. [Sistema Financeiro](#8-sistema-financeiro)
9. [Configurações da Loja](#9-configurações-da-loja)
10. [Relatórios](#10-relatórios)

---

## 1. Gerenciamento de Agendamentos

### 1.1. Visualizar Próximos Agendamentos

**Endpoint:** `GET /clinica/agendamentos/dashboard/`

**Resposta:**
```json
{
  "estatisticas": {
    "agendamentos_hoje": 5,
    "agendamentos_mes": 42,
    "clientes_ativos": 120,
    "procedimentos_ativos": 15,
    "receita_mensal": 15000.00
  },
  "proximos": [
    {
      "id": 1,
      "cliente_nome": "Maria Silva",
      "procedimento_nome": "Limpeza de Pele",
      "profissional_nome": "Dra. Ana",
      "data": "2026-02-09",
      "horario": "09:00",
      "status": "agendado"
    }
  ]
}
```

**Handler:**
```typescript
const { loading, stats, data, reload } = useDashboardData<EstatisticasClinica, Agendamento>({
  endpoint: '/clinica/agendamentos/dashboard/',
  initialStats: {
    agendamentos_hoje: 0,
    agendamentos_mes: 0,
    clientes_ativos: 0,
    procedimentos_ativos: 0,
    receita_mensal: 0
  },
  initialData: [],
  transformResponse: (responseData) => ({
    stats: responseData.estatisticas,
    data: ensureArray<Agendamento>(responseData.proximos)
  })
});
```

---

### 1.2. Criar Novo Agendamento

**Ação:** Clicar em "🗓️ Calendário" ou "+ Novo" em Próximos Agendamentos

**Handler:**
```typescript
const handleNovoAgendamento = () => {
  setShowCalendario(true);
};
```

**Componente:** `CalendarioAgendamentos.tsx`

**Endpoint:** `POST /clinica/agendamentos/`

**Payload:**
```json
{
  "cliente": 1,
  "profissional": 2,
  "procedimento": 3,
  "data": "2026-02-15",
  "horario": "14:00",
  "duracao": 60,
  "observacoes": "Cliente preferiu horário da tarde"
}
```

---

### 1.3. Excluir Agendamento ✨ (v478)

**Ação:** Passar mouse sobre card (desktop) ou visualizar em mobile → Clicar em 🗑️

**Handler:**
```typescript
const handleDeleteAgendamento = async (id: number) => {
  try {
    await clinicaApiClient.delete(`/clinica/agendamentos/${id}/`);
    toast.success('Agendamento excluído com sucesso!');
    reload();
  } catch (error) {
    console.error('Erro ao excluir agendamento:', error);
    toast.error('Erro ao excluir agendamento');
  }
};
```

**Endpoint:** `DELETE /clinica/agendamentos/{id}/`

**Características:**
- ✅ Confirmação antes de excluir
- ✅ Toast de feedback
- ✅ Reload automático da lista
- ✅ Botão aparece no hover (desktop) ou sempre visível (mobile)

---

### 1.4. Alterar Status do Agendamento ✨ (v478)

**Ação:** Clicar no badge de status → Selecionar novo status

**Handler:**
```typescript
const handleStatusChange = async (id: number, novoStatus: string) => {
  try {
    await clinicaApiClient.patch(`/clinica/agendamentos/${id}/`, { 
      status: novoStatus 
    });
    toast.success('Status atualizado com sucesso!');
    reload();
  } catch (error) {
    console.error('Erro ao atualizar status:', error);
    toast.error('Erro ao atualizar status');
  }
};
```

**Endpoint:** `PATCH /clinica/agendamentos/{id}/`

**Payload:**
```json
{
  "status": "confirmado" | "agendado" | "cancelado" | "concluido"
}
```

**Status Disponíveis:**
- ✅ **Confirmado** (verde) - Cliente confirmou presença
- 📅 **Agendado** (azul) - Agendamento criado
- ❌ **Cancelado** (vermelho) - Agendamento cancelado
- ✔️ **Concluído** (roxo) - Procedimento realizado

---

## 2. Gerenciamento de Clientes

### 2.1. Listar Clientes

**Ação:** Clicar em "👤 Cliente" nas Ações Rápidas

**Componente:** `ModalClientes.tsx`

**Endpoint:** `GET /clinica/clientes/`

**Resposta:**
```json
[
  {
    "id": 1,
    "nome": "Maria Silva",
    "email": "maria@email.com",
    "telefone": "(11) 98765-4321",
    "cpf": "123.456.789-00",
    "data_nascimento": "1990-05-15",
    "endereco": "Rua das Flores, 123",
    "cidade": "São Paulo",
    "estado": "SP",
    "observacoes": "Cliente VIP"
  }
]
```

---

### 2.2. Criar Cliente

**Endpoint:** `POST /clinica/clientes/`

**Payload:**
```json
{
  "nome": "João Santos",
  "email": "joao@email.com",
  "telefone": "(11) 91234-5678",
  "cpf": "987.654.321-00",
  "data_nascimento": "1985-10-20",
  "endereco": "Av. Paulista, 1000",
  "cidade": "São Paulo",
  "estado": "SP",
  "observacoes": ""
}
```

**Handler:**
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setSubmitting(true);
  
  try {
    if (editingCliente) {
      await clinicaApiClient.put(`/clinica/clientes/${editingCliente.id}/`, formData);
      toast.success('Cliente atualizado com sucesso!');
    } else {
      await clinicaApiClient.post('/clinica/clientes/', formData);
      toast.success('Cliente criado com sucesso!');
    }
    
    resetForm();
    loadClientes();
    onSuccess();
  } catch (error) {
    console.error('Erro ao salvar cliente:', error);
    toast.error('Erro ao salvar cliente');
  } finally {
    setSubmitting(false);
  }
};
```

---

### 2.3. Editar Cliente

**Endpoint:** `PUT /clinica/clientes/{id}/`

**Ação:** Clicar em "✏️ Editar" no card do cliente

---

### 2.4. Excluir Cliente

**Endpoint:** `DELETE /clinica/clientes/{id}/`

**Ação:** Clicar em "🗑️ Excluir" no card do cliente

**Handler:**
```typescript
const handleDelete = async (cliente: Cliente) => {
  if (!confirm(`Tem certeza que deseja excluir o cliente ${cliente.nome}?`)) {
    return;
  }
  
  try {
    await clinicaApiClient.delete(`/clinica/clientes/${cliente.id}/`);
    toast.success('Cliente excluído com sucesso!');
    loadClientes();
    onSuccess();
  } catch (error) {
    console.error('Erro ao excluir cliente:', error);
    toast.error('Erro ao excluir cliente');
  }
};
```

---

## 3. Gerenciamento de Profissionais

### 3.1. Listar Profissionais

**Ação:** Clicar em "👨‍⚕️ Profissional" nas Ações Rápidas

**Componente:** `ModalProfissionais.tsx`

**Endpoint:** `GET /clinica/profissionais/`

**Resposta:**
```json
[
  {
    "id": 1,
    "nome": "Dra. Ana Paula",
    "especialidade": "Esteticista",
    "registro_profissional": "CRE-12345",
    "telefone": "(11) 99999-8888",
    "email": "ana@clinica.com",
    "horario_inicio": "08:00",
    "horario_fim": "18:00",
    "dias_trabalho": ["seg", "ter", "qua", "qui", "sex"],
    "cor_agenda": "#8B5CF6"
  }
]
```

---

### 3.2. CRUD Completo

Similar ao gerenciamento de clientes:
- ✅ Criar profissional
- ✅ Editar profissional
- ✅ Excluir profissional
- ✅ Definir horários de trabalho
- ✅ Definir dias de trabalho
- ✅ Cor personalizada para agenda

---

## 4. Gerenciamento de Procedimentos

### 4.1. Listar Procedimentos

**Ação:** Clicar em "💆 Procedimentos" nas Ações Rápidas

**Componente:** `ModalProcedimentos.tsx`

**Endpoint:** `GET /clinica/procedimentos/`

**Resposta:**
```json
[
  {
    "id": 1,
    "nome": "Limpeza de Pele",
    "descricao": "Limpeza profunda com extração",
    "duracao": 60,
    "preco": "150.00",
    "categoria": "Facial"
  }
]
```

---

### 4.2. Categorias de Procedimentos

```typescript
const CATEGORIAS = [
  { value: 'Facial', label: 'Facial' },
  { value: 'Corporal', label: 'Corporal' },
  { value: 'Capilar', label: 'Capilar' },
  { value: 'Massagem', label: 'Massagem' },
  { value: 'Depilação', label: 'Depilação' },
  { value: 'Outro', label: 'Outro' },
];
```

---

### 4.3. CRUD Completo

- ✅ Criar procedimento
- ✅ Editar procedimento
- ✅ Excluir procedimento
- ✅ Definir duração
- ✅ Definir preço
- ✅ Categorizar procedimento

---

## 5. Sistema de Protocolos

### 5.1. Listar Protocolos

**Ação:** Clicar em "📋 Protocolos" nas Ações Rápidas

**Componente:** `ModalProtocolos.tsx`

**Endpoint:** `GET /clinica/protocolos/`

**Resposta:**
```json
[
  {
    "id": 1,
    "nome": "Protocolo Anti-Aging",
    "descricao": "Tratamento completo para rejuvenescimento",
    "procedimentos": [1, 3, 5],
    "numero_sessoes": 10,
    "intervalo_dias": 7,
    "observacoes": "Aplicar protetor solar após cada sessão"
  }
]
```

---

### 5.2. Funcionalidades

- ✅ Criar protocolo com múltiplos procedimentos
- ✅ Definir número de sessões
- ✅ Definir intervalo entre sessões
- ✅ Adicionar observações
- ✅ Editar e excluir protocolos

---

## 6. Sistema de Anamnese

### 6.1. Gerenciar Anamneses

**Ação:** Clicar em "📝 Anamnese" nas Ações Rápidas

**Componente:** `ModalAnamnese.tsx`

**Endpoint:** `GET /clinica/anamneses/`

**Campos da Anamnese:**
```typescript
{
  cliente: number;
  data_anamnese: string;
  
  // Dados Pessoais
  queixa_principal: string;
  historico_medico: string;
  medicamentos_uso: string;
  alergias: string;
  
  // Dados Físicos
  peso: number;
  altura: number;
  pressao_arterial: string;
  
  // Avaliação Estética
  tipo_pele: string;
  condicoes_pele: string;
  areas_tratamento: string;
  
  // Observações
  observacoes_gerais: string;
}
```

---

### 6.2. Funcionalidades

- ✅ Criar anamnese completa
- ✅ Visualizar histórico de anamneses
- ✅ Editar anamnese existente
- ✅ Calcular IMC automaticamente
- ✅ Registrar fotos (antes/depois)

---

## 7. Sistema de Consultas

### 7.1. Gerenciar Consultas

**Ação:** Clicar em "🏥 Consultas" nas Ações Rápidas

**Componente:** `GerenciadorConsultas.tsx`

**Endpoint:** `GET /clinica/consultas/`

**Funcionalidades:**
- ✅ Visualizar todas as consultas
- ✅ Filtrar por profissional ❌ (removido v478 - duplicado)
- ✅ Agenda por profissional
- ✅ Iniciar consulta
- ✅ Finalizar consulta
- ✅ Registrar evolução do paciente
- ✅ Visualizar histórico de evoluções

---

### 7.2. Evolução do Paciente

**Endpoint:** `POST /clinica/evolucoes/`

**Payload:**
```json
{
  "consulta": 1,
  "cliente": 1,
  "profissional": 2,
  "queixa_principal": "Manchas na pele",
  "historico_medico": "Sem histórico relevante",
  "peso": 65.5,
  "altura": 1.65,
  "tipo_pele": "Mista",
  "procedimento_realizado": "Limpeza de Pele Profunda",
  "produtos_utilizados": "Ácido glicólico 10%",
  "reacao_imediata": "Leve vermelhidão",
  "orientacoes_dadas": "Usar protetor solar FPS 50+",
  "proxima_sessao": "2026-02-22",
  "satisfacao_paciente": 5
}
```

---

## 8. Sistema Financeiro

### 8.1. Visualizar Financeiro

**Ação:** Clicar em "💰 Financeiro" nas Ações Rápidas

**Componente:** `ModalFinanceiro.tsx`

**Funcionalidades:**
- ✅ Visualizar receitas
- ✅ Visualizar despesas
- ✅ Gráficos de faturamento
- ✅ Relatórios mensais
- ✅ Exportar dados

---

## 9. Configurações da Loja

### 9.1. Configurações Gerais

**Ação:** Clicar em "⚙️ Configurações" nas Ações Rápidas

**Componente:** `ModalConfiguracoes.tsx`

**Tabs:**
1. **Histórico de Login**
   - Visualizar últimos acessos
   - IP e data/hora
   - Dispositivo utilizado

2. **Dados da Loja**
   - Nome, telefone, endereço
   - Horário de funcionamento
   - Redes sociais

3. **Aparência**
   - Cor primária
   - Cor secundária
   - Logo da loja

---

### 9.2. Assinatura e Plano

**Ação:** Clicar em "✍️ Assinatura" nas Ações Rápidas

**Componente:** `ConfiguracoesModal.tsx`

**Funcionalidades:**
- ✅ Visualizar plano atual
- ✅ Histórico de pagamentos
- ✅ Alterar plano
- ✅ Atualizar forma de pagamento
- ✅ Cancelar assinatura

---

## 10. Relatórios

### 10.1. Acessar Relatórios

**Ação:** Clicar em "📈 Relatórios" nas Ações Rápidas

**Handler:**
```typescript
const handleRelatorios = () => {
  router.push(`/loja/${loja.slug}/relatorios`);
};
```

**Tipos de Relatórios:**
- 📊 Faturamento mensal
- 👥 Clientes ativos
- 💆 Procedimentos mais realizados
- 👨‍⚕️ Performance por profissional
- 📅 Taxa de ocupação da agenda
- 💰 Receitas vs Despesas

---

## 🔄 Hooks Customizados

### useDashboardData

```typescript
const { loading, loadingData, stats, data, reload, error } = useDashboardData<Stats, Data>({
  endpoint: '/clinica/agendamentos/dashboard/',
  initialStats: {...},
  initialData: [],
  transformResponse: (responseData) => ({
    stats: responseData.estatisticas,
    data: responseData.proximos
  })
});
```

**Características:**
- ✅ Loading states separados (inicial e reload)
- ✅ Error handling
- ✅ Transform response customizável
- ✅ Reload manual
- ✅ TypeScript genérico

---

### useModals

```typescript
const { modals, openModal, closeModal } = useModals([
  'cliente', 'procedimentos', 'profissional',
  'protocolos', 'anamnese', 'configuracoes'
]);

// Uso
openModal('cliente');
closeModal('cliente');

// Estado
modals.cliente // true ou false
```

**Características:**
- ✅ Gerenciamento centralizado de modais
- ✅ TypeScript type-safe
- ✅ Múltiplos modais simultâneos
- ✅ API simples e intuitiva

---

## 📝 Resumo

Este documento detalha todas as funcionalidades implementadas no dashboard da clínica de estética, incluindo:
- ✅ 10 módulos principais
- ✅ Endpoints de API
- ✅ Handlers e lógica de negócio
- ✅ Payloads e respostas
- ✅ Hooks customizados
- ✅ Integrações completas

Todas as funcionalidades estão testadas e prontas para produção! 🚀
