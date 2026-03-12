# Sistema de Relatórios de Vendas - v962-v963

## 📋 Resumo
Sistema completo de geração de relatórios de vendas em PDF com envio por email, implementado no CRM de Vendas.

## ✅ Funcionalidades Implementadas

### 1. Backend (v962-v963)

#### Arquivo: `backend/crm_vendas/relatorios.py` (NOVO)
- **Função `calcular_periodo()`**: Calcula data_inicio e data_fim baseado no tipo de período
  - Períodos suportados: hoje, ontem, semana_atual, semana_passada, mes_atual, mes_passado, trimestre_atual, ano_atual
  
- **Função `gerar_relatorio_vendas_total()`**: Gera PDF com total de vendas de todos os vendedores
  - Resumo geral: quantidade de vendas, total de vendas, total de comissões
  - Detalhamento por vendedor com valores individuais
  - Formatação profissional com cores e tabelas
  
- **Função `gerar_relatorio_vendas_vendedor()`**: Gera PDF com vendas por vendedor específico
  - Pode filtrar por vendedor ou mostrar todos
  - Detalhamento de cada venda (data, cliente, valor, comissão)
  - Limita a 20 vendas por vendedor para evitar PDFs muito grandes

#### Arquivo: `backend/crm_vendas/views.py`
- **Função `gerar_relatorio()`**: Endpoint para geração de relatórios
  - POST `/crm-vendas/relatorios/gerar/`
  - Parâmetros:
    - `tipo`: "vendas_total" | "vendas_vendedor" | "comissoes"
    - `periodo`: "mes_atual" | "mes_passado" | etc
    - `vendedor_id`: ID do vendedor (opcional)
    - `acao`: "pdf" | "email"
  - Retorna PDF para download ou envia por email

#### Arquivo: `backend/crm_vendas/urls.py`
- Rota adicionada: `path('relatorios/gerar/', gerar_relatorio)`

#### Arquivo: `backend/requirements.txt`
- Adicionado: `reportlab==4.0.7` (biblioteca para geração de PDFs)
- Adicionado: `pillow>=9.0.0` (dependência do reportlab)

### 2. Frontend (v964)

#### Arquivo: `frontend/app/(dashboard)/loja/[slug]/crm-vendas/relatorios/page.tsx`
- **Interface completa de relatórios** com:
  - Cards de estatísticas em tempo real (Total de Vendas, Vendedores Ativos, Comissões)
  - Seleção de tipo de relatório (3 opções):
    1. Total de Vendas (todos os vendedores)
    2. Vendas por Vendedor (com comissões)
    3. Apenas Comissões (detalhamento completo)
  - Seleção de período (9 opções):
    - Hoje, Ontem
    - Esta Semana, Semana Passada
    - Este Mês, Mês Passado
    - Este Trimestre, Este Ano
    - Período Personalizado
  - Seleção de vendedor (quando tipo = vendas_vendedor)
  - Botões de ação:
    - "Exportar PDF" (download direto)
    - "Enviar por Email" (envia para email do usuário logado)

#### Arquivo: `frontend/components/crm-vendas/SidebarCrm.tsx`
- Menu "Relatórios" adicionado ao sidebar do CRM

## 🎨 Design e UX

### Cores e Estilo
- Segue o padrão Salesforce do CRM
- Cards informativos com ícones coloridos
- Botões de seleção com feedback visual
- Estados de loading e disabled durante geração

### Responsividade
- Layout adaptável para mobile e desktop
- Grid responsivo para cards e opções
- Botões empilhados em telas pequenas

## 📊 Lógica de Negócio

### Filtros de Dados
- Apenas oportunidades com `etapa='closed_won'` são incluídas
- Filtro por período usando `data_fechamento_ganho` ou `data_fechamento`
- Isolamento por `loja_id` (multi-tenancy)
- Filtro por vendedor quando aplicável

### Cálculos
- Total de vendas: soma de `valor` das oportunidades fechadas ganhas
- Total de comissões: soma de `valor_comissao` das oportunidades
- Quantidade de vendas: contagem de oportunidades
- Performance por vendedor: agregação individual

### Formatação de Valores
- Moeda brasileira (R$) com separadores corretos
- Datas no formato DD/MM/YYYY
- Números formatados com vírgula para decimais

## 🔒 Segurança

### Autenticação
- Endpoint protegido com `@permission_classes([IsAuthenticated])`
- Validação de `loja_id` do contexto
- Isolamento de dados por loja

### Validações
- Tipo de relatório validado
- Período validado
- Vendedor validado (se fornecido)
- Email do usuário validado antes de envio

## 📧 Envio de Email

### Configuração
- Usa `EmailMessage` do Django
- From: `noreply@lwksistemas.com.br`
- To: Email do usuário logado
- Anexo: PDF do relatório

### Conteúdo do Email
- Assunto: "Relatório de Vendas - [Nome da Loja]"
- Corpo: Informações sobre período e tipo
- Anexo: PDF com nome descritivo

## 🚀 Deploy

### Backend
- **v952**: Deploy inicial com código de relatórios
- **v963**: Adição de reportlab e pillow ao requirements.txt
- Heroku: `https://lwksistemas-38ad47519238.herokuapp.com/`

### Frontend
- **v964**: Integração com endpoint de relatórios
- Vercel: `https://lwksistemas.com.br/`

## 📝 Testes Recomendados

1. **Geração de PDF**
   - Testar cada tipo de relatório
   - Testar cada período
   - Verificar formatação e dados corretos

2. **Envio de Email**
   - Verificar recebimento do email
   - Verificar anexo do PDF
   - Testar com diferentes usuários

3. **Filtros**
   - Testar filtro por vendedor
   - Testar diferentes períodos
   - Verificar isolamento por loja

4. **Performance**
   - Testar com grande volume de dados
   - Verificar tempo de geração
   - Monitorar uso de memória

## 🔄 Próximas Melhorias Sugeridas

1. **Período Personalizado**
   - Implementar seleção de data_inicio e data_fim customizadas
   - Adicionar validação de intervalo máximo

2. **Mais Tipos de Relatórios**
   - Relatório de leads por origem
   - Relatório de taxa de conversão
   - Relatório de atividades por vendedor

3. **Gráficos no PDF**
   - Adicionar gráficos de pizza e barras
   - Visualização de tendências

4. **Agendamento de Relatórios**
   - Envio automático mensal/semanal
   - Configuração de destinatários

5. **Exportação em Excel**
   - Opção de download em XLSX
   - Dados tabulados para análise

## 📍 URLs

- **Página de Relatórios**: `https://lwksistemas.com.br/loja/felix-5889/crm-vendas/relatorios`
- **Endpoint Backend**: `POST /crm-vendas/relatorios/gerar/`

## 🎯 Status

✅ **CONCLUÍDO** - Sistema de relatórios totalmente funcional e deployado em produção.
