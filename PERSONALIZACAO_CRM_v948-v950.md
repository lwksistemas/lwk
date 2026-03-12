# Sistema de Personalização do CRM - Deploy v948-v952

## 📋 Resumo

Implementado sistema completo de personalização do CRM, permitindo ao administrador configurar o sistema de acordo com suas necessidades.

**IMPORTANTE**: A página de personalização foi movida para `/configuracoes/personalizar` para não substituir os botões originais de configuração (Assinatura, Login, Funcionários, WhatsApp).

---

## ✅ Funcionalidades Implementadas

### 1. Gerenciar Origens de Leads (v948)

**Backend**:
- Modelo `CRMConfig` para armazenar configurações por loja
- Endpoint `/api/crm-vendas/config/` (GET e PATCH)
- Migration `0009_crmconfig.py`

**Frontend**:
- Página `/loja/{slug}/crm-vendas/configuracoes`
- Interface para:
  - ✅ Adicionar novas origens (ex: "LinkedIn", "Evento", "Cold Call")
  - ✅ Editar nome das origens existentes
  - ✅ Ativar/desativar origens (checkbox)
  - ✅ Remover origens não utilizadas

**Origens Padrão**:
- WhatsApp, Facebook, Instagram, Site, Indicação, Outro

---

### 2. Ocultar Módulos Não Utilizados (v949)

**Frontend**:
- Context `CRMConfigProvider` para compartilhar configurações
- Interface para ativar/desativar módulos:
  - Leads (sempre ativo)
  - Contas (pode desabilitar)
  - Contatos (pode desabilitar)
  - Pipeline (sempre ativo)
  - Atividades/Calendário (sempre ativo)
- Sidebar atualizado para ocultar módulos desabilitados

---

### 3. Personalizar Etapas do Pipeline (v950)

**Frontend**:
- Interface para gerenciar etapas:
  - ✅ Ativar/desativar etapas (ex: desabilitar "Qualificação")
  - ✅ Renomear etapas
  - ✅ Reordenar etapas (botões ↑ ↓)
  - ⚠️ Etapas de fechamento (ganho/perdido) são obrigatórias
- Context atualizado com funções `etapasAtivas()` e `origensAtivas()`

**Etapas Padrão**:
1. Prospecção
2. Qualificação
3. Proposta
4. Negociação
5. Fechado (ganho) - obrigatória
6. Fechado (perdido) - obrigatória

---

### 4. Configurar Colunas Visíveis nos Leads (v951)

**Frontend**:
- Interface para gerenciar colunas da listagem:
  - ✅ Ativar/desativar colunas (mínimo 3 colunas)
  - ✅ Reordenar colunas (botões ↑ ↓)
  - ✅ Indicador de posição mostrando ordem atual
- Context atualizado com função `colunasLeadsVisiveis()`
- Componente `LeadsTable` atualizado para aceitar colunas configuráveis
- Função `renderCelula()` para renderizar dinamicamente cada tipo de coluna

**Colunas Disponíveis**:
- Nome (com avatar)
- Empresa
- E-mail
- Telefone
- Origem (badge colorido)
- Status (badge colorido)
- Valor Estimado (formatado em R$)
- Data de Criação (formatada)

**Colunas Padrão**:
Nome, Empresa, Telefone, E-mail, Origem, Status, Valor Estimado

---

## 🎯 Próximas Funcionalidades (Não Implementadas)

Todas as funcionalidades planejadas foram implementadas com sucesso!

---

## 📊 Deploy Status

| Deploy | Componente | Descrição |
|---|---|---|
| v948 | Backend | Modelo CRMConfig + endpoint |
| v948 | Frontend | Gerenciar origens de leads |
| v949 | Frontend | Ocultar módulos não utilizados |
| v950 | Frontend | Personalizar etapas do pipeline |
| v951 | Frontend | Configurar colunas visíveis nos leads |
| v952 | Frontend | Correção: restaurar página de configurações original + novo botão |

---

## 🧪 Como Testar

1. Acesse: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/configuracoes
2. Verifique que existem 5 botões:
   - Pagar assinatura
   - Configurar tela de login
   - Cadastrar funcionários
   - Configurar WhatsApp
   - **Personalizar CRM** (NOVO)
3. Clique em "Personalizar CRM"
4. Teste cada seção:
   - **Origens**: Adicione "LinkedIn", desabilite "Facebook"
   - **Módulos**: Desabilite "Contas" e veja sumir do menu
   - **Etapas**: Desabilite "Qualificação", reordene etapas
   - **Colunas de Leads**: Desabilite "Empresa", reordene colunas visíveis
5. Acesse: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/leads
6. Verifique se as colunas configuradas aparecem na ordem correta

---

## 🔧 Estrutura Técnica

**Backend**:
```
backend/crm_vendas/
├── models_config.py          # Modelo CRMConfig
├── migrations/
│   └── 0009_crmconfig.py     # Migration
├── serializers.py            # CRMConfigSerializer
├── views.py                  # crm_config endpoint
└── urls.py                   # Rota /config/
```

**Frontend**:
```
frontend/
├── contexts/
│   └── CRMConfigContext.tsx  # Provider de configurações
├── app/(dashboard)/loja/[slug]/crm-vendas/
│   ├── layout.tsx            # Wrapper com CRMConfigProvider
│   ├── configuracoes/
│   │   ├── page.tsx          # Página principal com 5 botões
│   │   ├── personalizar/
│   │   │   └── page.tsx      # Página de personalização do CRM
│   │   ├── login/
│   │   ├── funcionarios/
│   │   └── whatsapp/
│   └── leads/
│       └── page.tsx          # Usa colunasLeadsVisiveis()
└── components/crm-vendas/
    ├── SidebarCrm.tsx        # Menu com módulos dinâmicos
    └── LeadsTable.tsx        # Tabela com colunas configuráveis
```

---

## 📝 Notas Importantes

- Apenas o proprietário da loja pode acessar configurações
- Vendedores não veem o menu "Configurações"
- Configurações são salvas automaticamente ao alterar
- Cache do dashboard é invalidado ao mudar configurações
- Módulos principais (Leads, Pipeline, Atividades) sempre ativos
- Etapas de fechamento (ganho/perdido) não podem ser desabilitadas

---

## 🔗 URLs

- Configurações Principal: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/configuracoes
- Personalizar CRM: https://lwksistemas.com.br/loja/felix-5889/crm-vendas/configuracoes/personalizar
- API Config: https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/config/
