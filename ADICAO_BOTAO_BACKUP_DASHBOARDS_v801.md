# Adição do Botão de Backup nos Dashboards das Lojas - v801

## Data: 05/03/2026

## Objetivo
Adicionar o botão de backup em todos os dashboards das lojas para permitir que os administradores das lojas façam backup e restauração dos seus dados.

## Implementação Realizada

### 1. Correção do BackupButton
- **Arquivo**: `frontend/components/loja/BackupButton.tsx`
- **Problema**: Uso incorreto do hook `useToast` (tentava usar métodos `.success()`, `.error()` que não existem)
- **Solução**: Corrigido para usar `addToast()` com objeto contendo `tipo`, `titulo` e `mensagem`
- **Status**: ✅ Corrigido e testado

### 2. Dashboards Atualizados

#### 2.1. Dashboard Clínica da Beleza
- **Arquivo**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/clinica-beleza.tsx`
- **Localização**: Header, ao lado do NotificationBell
- **Status**: ✅ Implementado (já estava feito anteriormente)

#### 2.2. Dashboard CRM Vendas
- **Arquivo**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/crm-vendas.tsx`
- **Localização**: Header, ao lado do ThemeToggle
- **Alterações**:
  - Importado `BackupButton`
  - Adicionado no header dentro de uma div flex com gap-2
- **Status**: ✅ Implementado

#### 2.3. Dashboard Restaurante
- **Arquivo**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/restaurante.tsx`
- **Localização**: Header, ao lado do ThemeToggle
- **Alterações**:
  - Importado `BackupButton`
  - Adicionado no header dentro de uma div flex com gap-2
- **Status**: ✅ Implementado

#### 2.4. Dashboard Serviços
- **Arquivo**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/servicos.tsx`
- **Localização**: Header, ao lado do ThemeToggle
- **Alterações**:
  - Importado `BackupButton`
  - Adicionado no header dentro de uma div flex com gap-2
- **Status**: ✅ Implementado

#### 2.5. Dashboard Clínica Estética
- **Arquivo**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/clinica-estetica.tsx`
- **Localização**: Novo header criado com título e botões
- **Alterações**:
  - Importado `BackupButton` e `ThemeToggle`
  - Criado header com título "Dashboard - {loja.nome}"
  - Adicionado BackupButton e ThemeToggle no header
- **Status**: ✅ Implementado

#### 2.6. Dashboard Cabeleireiro
- **Arquivo**: `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/dashboard-cabeleireiro-novo.tsx`
- **Componente**: `frontend/components/cabeleireiro/dashboard/DashboardHeader.tsx`
- **Alterações**:
  - Modificado `DashboardHeader` para aceitar `lojaId` e `lojaNome` (opcionais)
  - Adicionado `BackupButton` no header quando os props são fornecidos
  - Atualizado uso do componente no dashboard para passar os props
- **Status**: ✅ Implementado

### 3. Funcionalidades do Botão de Backup

O botão oferece 3 opções via menu dropdown:

1. **📤 Exportar Backup**
   - Gera arquivo ZIP com todos os dados da loja
   - Download automático do arquivo
   - Nome do arquivo: `backup_{nome_loja}_{data}.zip`

2. **📥 Importar Backup**
   - Permite selecionar arquivo ZIP de backup
   - Validação de formato e tamanho (máx 500MB)
   - Confirmação antes de substituir dados
   - Recarrega página após importação bem-sucedida

3. **⚙️ Configurar Automático**
   - Placeholder para futura implementação
   - Permitirá configurar backups automáticos por email

### 4. Regras de Exibição

- ✅ Botão aparece APENAS nos dashboards das lojas individuais
- ❌ Botão NÃO aparece no dashboard do SuperAdmin
- ✅ Cada loja vê apenas seu próprio botão de backup
- ✅ Backup é isolado por loja (tenant)

## Deploy

### Git
```bash
git add -A
git commit -m "feat: adicionar botão de backup em todos os dashboards das lojas"
git push origin master
```
- **Commit**: da3ca2a4
- **Status**: ✅ Pushed

### Vercel
- **Status**: Auto-deploy configurado
- **URL**: https://lwksistemas.com.br
- **Último deploy bem-sucedido**: 12 minutos atrás

### Heroku
- **App**: lwksistemas
- **Status**: Backend já estava deployado com endpoints de backup

## Arquivos Modificados

1. `frontend/components/loja/BackupButton.tsx` - Corrigido uso do toast
2. `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/crm-vendas.tsx` - Adicionado botão
3. `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/restaurante.tsx` - Adicionado botão
4. `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/servicos.tsx` - Adicionado botão
5. `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/clinica-estetica.tsx` - Adicionado header e botão
6. `frontend/components/cabeleireiro/dashboard/DashboardHeader.tsx` - Modificado para aceitar props de backup
7. `frontend/app/(dashboard)/loja/[slug]/dashboard/templates/dashboard-cabeleireiro-novo.tsx` - Passado props para header

## Próximos Passos (Futuro)

1. **Modal de Configuração de Backup Automático**
   - Interface para configurar horário de envio
   - Configuração de email de destino
   - Frequência (diária, semanal, mensal)

2. **Histórico de Backups**
   - Listar backups anteriores
   - Download de backups antigos
   - Informações sobre cada backup (data, tamanho, registros)

3. **Notificações**
   - Notificar quando backup automático for realizado
   - Alertar em caso de falha no backup
   - Lembrete para fazer backup manual

## Observações

- O botão usa a classe `hidden sm:flex` em alguns dashboards para não aparecer em telas muito pequenas
- Todos os toasts seguem o padrão do sistema (tipo, titulo, mensagem)
- O componente é reutilizável e pode ser facilmente adicionado em novos dashboards
- Backend já estava pronto com todos os endpoints necessários

## Conclusão

✅ Botão de backup implementado com sucesso em todos os dashboards das lojas
✅ Sistema de backup completo e funcional
✅ Deploy realizado no Vercel (auto-deploy)
✅ Código segue boas práticas e padrões do projeto
