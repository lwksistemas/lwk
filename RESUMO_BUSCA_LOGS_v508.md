# Busca de Logs - v508

## 📋 Resumo

Implementada a página de Busca Avançada de Logs no frontend, permitindo busca detalhada, exportação, análise de contexto temporal e salvamento de buscas favoritas.

## ✅ Implementação Concluída

### Arquivo Criado
- **Caminho**: `frontend/app/(dashboard)/superadmin/dashboard/logs/page.tsx`
- **Rota**: `/superadmin/dashboard/logs`
- **Linhas de código**: ~350 linhas
- **Tecnologias**: Next.js 15, React 19, TypeScript, Tailwind CSS

### Funcionalidades Implementadas

#### 1. Formulário de Busca Avançada ✅
- **Campos de filtro** (7):
  1. **Busca por texto livre**: Busca em todos os campos simultaneamente
  2. **Data início**: Filtro por data inicial
  3. **Data fim**: Filtro por data final
  4. **Loja**: Filtro por nome da loja
  5. **Email do usuário**: Filtro por email
  6. **Ação**: Filtro por tipo de ação
  7. **Status**: Filtro por sucesso/erro

- **Botões de ação**:
  - 🔍 Buscar: Executa a busca
  - 🔄 Limpar: Limpa todos os filtros
  - 📥 CSV: Exporta resultados em CSV
  - 📥 JSON: Exporta resultados em JSON
  - 💾 Salvar Busca: Salva filtros atuais
  - 📋 Buscas Salvas: Dropdown com buscas salvas

#### 2. Tabela de Resultados ✅
- **Colunas exibidas** (8):
  - Data/Hora (formatada em pt-BR)
  - Usuário (nome + email)
  - Loja
  - Ação (badge colorido)
  - Recurso
  - Status (sucesso/erro com cores)
  - IP Address
  - Ações (botão "Ver Detalhes")

- **Recursos**:
  - Highlight de termos de busca (fundo amarelo)
  - Hover effect nas linhas
  - Scroll horizontal se necessário
  - Contador de resultados
  - Estado vazio com mensagem

#### 3. Modal de Detalhes do Log ✅
- **Informações exibidas**:
  - Data/Hora completa
  - Status com código HTTP
  - Usuário (nome + email)
  - Loja
  - Ação e Recurso
  - URL completa com método HTTP
  - IP Address
  - User Agent
  - Detalhes JSON formatados

- **Recursos**:
  - Modal responsivo (max 90vh)
  - Scroll interno
  - Header fixo
  - Botão de fechar (×)
  - JSON com syntax highlighting

#### 4. Contexto Temporal ✅
- **Visualização em timeline**:
  - **Ações Anteriores** (até 10):
    - Fundo azul claro
    - Ícone ⬆️
    - Hora, ação, recurso, usuário, loja
  
  - **Log Atual**:
    - Fundo roxo com borda
    - Ícone 📍
    - Destaque visual
  
  - **Ações Posteriores** (até 10):
    - Fundo verde claro
    - Ícone ⬇️
    - Hora, ação, recurso, usuário, loja

- **Carregamento automático**: Ao abrir detalhes do log

#### 5. Buscas Salvas ✅
- **Funcionalidades**:
  - Salvar busca com nome customizado
  - Armazenamento em localStorage
  - Dropdown com lista de buscas salvas
  - Carregar busca com um clique
  - Excluir busca (ícone 🗑️)
  - Contador de buscas salvas

- **Modal de salvamento**:
  - Input para nome da busca
  - Botões Cancelar/Salvar
  - Validação (nome obrigatório)
  - Auto-focus no input

#### 6. Exportação de Dados ✅
- **Formato CSV**:
  - Endpoint: `/api/superadmin/historico-acesso-global/exportar/`
  - Download automático
  - Nome do arquivo: `logs_[timestamp].csv`
  - Aplica filtros ativos

- **Formato JSON**:
  - Endpoint: `/api/superadmin/historico-acesso-global/exportar_json/`
  - Download automático
  - Nome do arquivo: `logs_[timestamp].json`
  - Formatação com indentação (2 espaços)
  - Aplica filtros ativos

- **Limite**: 10.000 registros por exportação

#### 7. Highlight de Termos de Busca ✅
- **Campos com highlight**:
  - Nome do usuário
  - Email do usuário
  - Nome da loja
  - Ação
  - Recurso

- **Implementação**:
  - Busca case-insensitive
  - Fundo amarelo (`bg-yellow-200`)
  - Preserva formatação original

### Integração com Backend

#### Endpoints Utilizados
1. **Busca Avançada**:
   - `GET /api/superadmin/historico-acesso-global/busca_avancada/`
   - Parâmetros: `q`, `data_inicio`, `data_fim`, `loja_nome`, `usuario_email`, `acao`, `sucesso`
   - Retorna: Lista paginada de logs

2. **Listagem Padrão**:
   - `GET /api/superadmin/historico-acesso-global/`
   - Parâmetros: Mesmos da busca avançada (exceto `q`)
   - Retorna: Lista paginada de logs

3. **Exportação CSV**:
   - `GET /api/superadmin/historico-acesso-global/exportar/`
   - Parâmetros: Filtros aplicados
   - Retorna: Arquivo CSV

4. **Exportação JSON**:
   - `GET /api/superadmin/historico-acesso-global/exportar_json/`
   - Parâmetros: Filtros aplicados
   - Retorna: JSON estruturado

5. **Contexto Temporal**:
   - `GET /api/superadmin/historico-acesso-global/{id}/contexto_temporal/`
   - Parâmetros: `antes=10`, `depois=10`
   - Retorna: `{ antes: Log[], depois: Log[] }`

### Layout e Design

#### Estrutura da Página
```
┌─────────────────────────────────────────────┐
│ Header (Título + Botão Voltar)             │
├─────────────────────────────────────────────┤
│ Formulário de Busca                         │
│ ├─ 7 campos de filtro (grid 3 colunas)     │
│ └─ 6 botões de ação                         │
├─────────────────────────────────────────────┤
│ Tabela de Resultados                        │
│ ├─ Header com 8 colunas                     │
│ └─ Linhas com dados + highlight             │
└─────────────────────────────────────────────┘

Modal de Detalhes:
┌─────────────────────────────────────────────┐
│ Header (Título + Botão Fechar)             │
├─────────────────────────────────────────────┤
│ Informações Principais (grid 2 colunas)    │
├─────────────────────────────────────────────┤
│ Detalhes JSON (formatado)                  │
├─────────────────────────────────────────────┤
│ Contexto Temporal (timeline)                │
│ ├─ Ações Anteriores (azul)                 │
│ ├─ Log Atual (roxo)                         │
│ └─ Ações Posteriores (verde)               │
└─────────────────────────────────────────────┘
```

#### Responsividade
- **Desktop**: Grid de 3 colunas para filtros
- **Tablet**: Grid de 2 colunas
- **Mobile**: Grid de 1 coluna, scroll horizontal na tabela

#### Cores e Estilo
- **Background**: Cinza claro (`bg-gray-50`)
- **Cards**: Branco com sombra (`bg-white shadow`)
- **Header**: Roxo (`bg-purple-900`)
- **Botões**:
  - Buscar: Roxo (`bg-purple-600`)
  - Limpar: Cinza (`bg-gray-500`)
  - CSV: Verde (`bg-green-600`)
  - JSON: Azul (`bg-blue-600`)
  - Salvar: Verde (`bg-green-600`)
- **Status**:
  - Sucesso: Verde (`bg-green-100 text-green-800`)
  - Erro: Vermelho (`bg-red-100 text-red-800`)
- **Highlight**: Amarelo (`bg-yellow-200`)

### Estados da Interface

#### Loading
- Exibe "Carregando..." na área de resultados
- Botão "Buscar" desabilitado com texto "Buscando..."
- Mantém filtros visíveis

#### Sem Resultados
- Mensagem: "Nenhum log encontrado. Use os filtros acima para buscar."
- Botões de exportação desabilitados
- Filtros permanecem ativos

#### Com Resultados
- Tabela completa com todos os logs
- Contador de resultados no header
- Botões de exportação habilitados
- Highlight de termos de busca

#### Modal Aberto
- Overlay escuro (50% opacidade)
- Modal centralizado
- Scroll interno se necessário
- Contexto temporal carregando automaticamente

### Integração com Dashboard Principal

#### Card Adicionado
- **Título**: "Busca de Logs"
- **Descrição**: "Busca avançada e análise detalhada de logs"
- **Ícone**: 🔍
- **Cor**: Indigo (azul-roxo)
- **Link**: `/superadmin/dashboard/logs`

#### Posicionamento
- Localizado após "Dashboard de Auditoria"
- Antes de "Configuração Asaas"
- Grid responsivo de 3 colunas

## 📊 Exemplos de Uso

### Busca por Texto Livre
1. Acessar `/superadmin/dashboard/logs`
2. Digitar termo no campo "Busca por Texto"
3. Clicar em "🔍 Buscar"
4. Visualizar resultados com highlight

### Busca por Período
1. Selecionar "Data Início" e "Data Fim"
2. Clicar em "🔍 Buscar"
3. Visualizar logs do período

### Busca Combinada
1. Preencher múltiplos filtros (ex: loja + ação + status)
2. Clicar em "🔍 Buscar"
3. Visualizar logs que atendem todos os critérios

### Análise de Contexto
1. Buscar logs
2. Clicar em "Ver Detalhes" em um log
3. Visualizar contexto temporal (antes/depois)
4. Identificar sequência de ações

### Salvar Busca Favorita
1. Configurar filtros desejados
2. Clicar em "💾 Salvar Busca"
3. Digitar nome da busca
4. Clicar em "Salvar"
5. Busca disponível em "📋 Buscas Salvas"

### Exportar Dados
1. Realizar busca
2. Clicar em "📥 CSV" ou "📥 JSON"
3. Arquivo baixado automaticamente

## 🔧 Configuração

### Dependências
- `@/lib/api-client`: Cliente HTTP customizado
- `@/lib/auth`: Serviço de autenticação
- `localStorage`: Armazenamento de buscas salvas

### Permissões
- Requer autenticação como SuperAdmin
- Redirecionamento automático se não autenticado
- Validação no backend via `IsSuperAdmin`

### Limites
- **Resultados por página**: Definido pelo backend (paginação)
- **Exportação**: Máximo 10.000 registros
- **Contexto temporal**: 10 logs antes + 10 depois
- **Buscas salvas**: Ilimitado (localStorage)

## 📈 Métricas e Performance

### Otimizações Implementadas
- **Highlight seletivo**: Apenas quando há termo de busca
- **Lazy loading**: Modal carrega contexto apenas quando aberto
- **LocalStorage**: Buscas salvas sem requisição ao servidor
- **Blob download**: Exportação eficiente de arquivos

### Casos de Uso Cobertos
1. ✅ Investigação de incidentes de segurança
2. ✅ Auditoria de ações de usuários específicos
3. ✅ Análise de padrões de uso por loja
4. ✅ Identificação de erros recorrentes
5. ✅ Exportação para análise externa
6. ✅ Buscas frequentes salvas para reuso

## 🎯 Próximos Passos

### Tarefa 15: Sistema de Notificações
- [ ] 15.1 Criar serviço de notificações
- [ ] 15.2 Integrar com detector
- [ ] 15.3 Notificações em tempo real no frontend

### Melhorias Futuras (Opcional)
- [ ] Paginação na tabela de resultados
- [ ] Ordenação por colunas (clique no header)
- [ ] Filtros avançados (regex, operadores lógicos)
- [ ] Compartilhamento de buscas entre usuários
- [ ] Gráficos de distribuição de logs
- [ ] Alertas automáticos baseados em buscas

## 📝 Notas Técnicas

1. **Highlight**: Usa regex case-insensitive para busca e `<mark>` para destaque
2. **Exportação**: Usa Blob API para download sem recarregar página
3. **LocalStorage**: Chave `buscas_logs_salvas` armazena array de objetos
4. **Contexto Temporal**: Carregado assincronamente ao abrir modal
5. **TypeScript**: Interfaces tipadas para Log, BuscaSalva e FiltrosBusca

## ✅ Checklist de Conclusão

- [x] Página criada e funcional
- [x] Formulário de busca com 7 filtros
- [x] Tabela de resultados com highlight
- [x] Modal de detalhes completo
- [x] Contexto temporal (timeline)
- [x] Buscas salvas (localStorage)
- [x] Exportação CSV e JSON
- [x] Integração com backend completa
- [x] Design responsivo
- [x] Card adicionado ao dashboard principal
- [x] Tarefa 14 marcada como concluída
- [x] Documentação criada

## 🎉 Resultado

Página de Busca de Logs totalmente funcional, permitindo ao SuperAdmin:
- Buscar logs com múltiplos filtros combinados
- Visualizar detalhes completos de cada log
- Analisar contexto temporal (ações antes/depois)
- Salvar buscas frequentes para reuso
- Exportar dados para análise externa (CSV/JSON)
- Investigar incidentes de segurança de forma eficiente
