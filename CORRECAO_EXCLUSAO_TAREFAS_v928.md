# Correção: Exclusão de Tarefas do Google Calendar (v928)

## Problema Identificado

Tarefas eram deletadas do banco de dados local mas voltavam após sincronizar com o Google Calendar, pois o evento não estava sendo removido do Google Calendar.

## Causa Raiz

O método `perform_destroy` na classe `AtividadeViewSet` não estava deletando o evento do Google Calendar antes de deletar do banco local.

## Correções Implementadas

### Deploy v926 (Primeira Tentativa)
- Adicionado código para deletar do Google Calendar
- **ERRO**: `ModuleNotFoundError: No module named 'crm_vendas.google_calendar'`

### Deploy v927 (Segunda Tentativa)
- Corrigido import de `GoogleCalendarService` (classe inexistente)
- Adicionado `import logging` e `logger`
- **ERRO**: Import ainda incorreto, tentando usar classe ao invés de função

### Deploy v928 (Correção Final) ✅
- Corrigido import para usar a função `delete_google_event` ao invés de classe
- Função correta: `from crm_vendas.google_calendar_service import delete_google_event`
- Lógica implementada:
  1. Verifica se a atividade tem `google_event_id`
  2. Busca a conexão ativa do Google Calendar da loja
  3. Chama `delete_google_event(connection, event_id)`
  4. Loga sucesso ou falha
  5. Continua com a exclusão do banco mesmo se falhar no Google Calendar

## Código Corrigido

```python
def perform_destroy(self, instance):
    """
    Deleta atividade e remove do Google Calendar se tiver google_event_id
    """
    # Se tem google_event_id, deletar do Google Calendar
    if instance.google_event_id:
        try:
            from superadmin.models import GoogleCalendarConnection
            from crm_vendas.google_calendar_service import delete_google_event
            loja_id = get_current_loja_id()
            
            # Buscar conexão do Google Calendar
            connection = GoogleCalendarConnection.objects.filter(
                loja_id=loja_id,
                is_active=True
            ).first()
            
            if connection:
                success = delete_google_event(connection, instance.google_event_id)
                if success:
                    logger.info(f"✅ Evento deletado do Google Calendar: {instance.google_event_id}")
                else:
                    logger.warning(f"⚠️ Falha ao deletar evento do Google Calendar: {instance.google_event_id}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao deletar evento do Google Calendar: {e}")
            # Continuar com a exclusão mesmo se falhar no Google Calendar
    
    super().perform_destroy(instance)
    CRMCacheManager.invalidate_atividades(get_current_loja_id())
```

## Arquivos Modificados

- `backend/crm_vendas/views.py` (método `perform_destroy` na classe `AtividadeViewSet`)

## Módulo Utilizado

- `backend/crm_vendas/google_calendar_service.py` - Contém funções standalone para integração com Google Calendar API
- Função utilizada: `delete_google_event(connection, event_id, calendar_id=None)`

## Status

✅ **RESOLVIDO** - Deploy v928 realizado com sucesso no Heroku

## Como Testar

1. Acessar o CRM Vendas em https://lwksistemas.com.br/
2. Criar uma tarefa sincronizada com Google Calendar
3. Deletar a tarefa no sistema
4. Verificar que o evento foi removido do Google Calendar
5. Sincronizar novamente - a tarefa não deve voltar

## Data

11 de março de 2026
