# Análise: Sistema de Monitoramento de Storage por Loja

**Data**: 25/02/2026  
**Status**: 📋 Análise Completa

## Situação Atual

### ✅ O que já existe:

1. **Campo `espaco_storage_gb` no modelo `PlanoAssinatura`**:
   - Define o limite de storage por plano (ex: 5GB, 50GB, 200GB)
   - Usado para definir quanto espaço cada loja pode usar

2. **Limitação de 512 MB no middleware** (`backend/tenants/middleware.py`):
   - Implementada apenas para SQLite local (desenvolvimento)
   - Bloqueia escritas quando o arquivo SQLite >= 512 MB
   - **NÃO funciona em produção (PostgreSQL)**

3. **Estrutura multi-tenant**:
   - Cada loja tem seu próprio schema PostgreSQL isolado
   - Schema nomeado como `loja_{slug}` (ex: `loja_clinica_daniel_5889`)

### ❌ O que NÃO existe:

1. **Monitoramento de uso de storage em produção (PostgreSQL)**
2. **Campo para armazenar uso atual de storage**
3. **Sistema de alertas quando atingir limite**
4. **Envio de email para cliente e superadmin**
5. **Comando para calcular tamanho dos schemas**

## Requisitos do Cliente

1. **Limite de storage**: 500 MB por loja (configurável por plano)
2. **Alerta em 80%**: Quando atingir 400 MB (80% de 500 MB)
3. **Email para cliente**: Notificar proprietário da loja
4. **Email para superadmin**: Notificar administrador do sistema
5. **Opção de upgrade**: Cliente pode comprar mais espaço

## Solução Proposta

### 1. Adicionar Campos no Modelo `Loja`

```python
class Loja(models.Model):
    # ... campos existentes ...
    
    # Monitoramento de Storage
    storage_usado_mb = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Espaço em disco usado pela loja (em MB)'
    )
    storage_limite_mb = models.IntegerField(
        default=500,
        help_text='Limite de storage da loja (em MB) - baseado no plano'
    )
    storage_alerta_enviado = models.BooleanField(
        default=False,
        help_text='Indica se alerta de 80% já foi enviado'
    )
    storage_ultima_verificacao = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Data da última verificação de storage'
    )
```

### 2. Criar Comando de Gerenciamento

**Arquivo**: `backend/superadmin/management/commands/verificar_storage_lojas.py`

```python
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
from superadmin.models import Loja
from superadmin.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica uso de storage de todas as lojas e envia alertas'

    def handle(self, *args, **options):
        lojas = Loja.objects.filter(is_active=True)
        
        for loja in lojas:
            try:
                # Calcular tamanho do schema PostgreSQL
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))::text as size_pretty,
                               pg_database_size(current_database()) as size_bytes
                        FROM pg_database
                        WHERE datname = current_database()
                    """)
                    result = cursor.fetchone()
                    
                    if result:
                        size_bytes = result[1]
                        size_mb = size_bytes / (1024 * 1024)
                        
                        # Atualizar loja
                        loja.storage_usado_mb = round(size_mb, 2)
                        loja.storage_ultima_verificacao = timezone.now()
                        
                        # Calcular limite baseado no plano
                        limite_gb = loja.plano.espaco_storage_gb
                        limite_mb = limite_gb * 1024
                        loja.storage_limite_mb = limite_mb
                        
                        # Verificar se atingiu 80% (alerta)
                        percentual = (size_mb / limite_mb) * 100
                        
                        if percentual >= 80 and not loja.storage_alerta_enviado:
                            # Enviar alerta
                            self._enviar_alerta(loja, size_mb, limite_mb, percentual)
                            loja.storage_alerta_enviado = True
                        
                        # Verificar se atingiu 100% (bloquear)
                        if percentual >= 100:
                            loja.is_blocked = True
                            loja.blocked_reason = f'Limite de storage atingido ({size_mb:.2f} MB / {limite_mb} MB)'
                            loja.blocked_at = timezone.now()
                            self._enviar_alerta_bloqueio(loja, size_mb, limite_mb)
                        
                        loja.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ {loja.nome}: {size_mb:.2f} MB / {limite_mb} MB ({percentual:.1f}%)'
                            )
                        )
                
            except Exception as e:
                logger.error(f'Erro ao verificar storage da loja {loja.nome}: {e}')
                self.stdout.write(
                    self.style.ERROR(f'❌ {loja.nome}: {e}')
                )
    
    def _enviar_alerta(self, loja, usado_mb, limite_mb, percentual):
        """Envia alerta de 80% de uso"""
        email_service = EmailService()
        
        # Email para o cliente
        email_service.enviar_alerta_storage_cliente(
            loja=loja,
            usado_mb=usado_mb,
            limite_mb=limite_mb,
            percentual=percentual
        )
        
        # Email para o superadmin
        email_service.enviar_alerta_storage_admin(
            loja=loja,
            usado_mb=usado_mb,
            limite_mb=limite_mb,
            percentual=percentual
        )
    
    def _enviar_alerta_bloqueio(self, loja, usado_mb, limite_mb):
        """Envia alerta de bloqueio por limite atingido"""
        email_service = EmailService()
        
        # Email para o cliente
        email_service.enviar_alerta_bloqueio_storage_cliente(
            loja=loja,
            usado_mb=usado_mb,
            limite_mb=limite_mb
        )
        
        # Email para o superadmin
        email_service.enviar_alerta_bloqueio_storage_admin(
            loja=loja,
            usado_mb=usado_mb,
            limite_mb=limite_mb
        )
```

### 3. Adicionar Métodos no EmailService

**Arquivo**: `backend/superadmin/email_service.py`

```python
def enviar_alerta_storage_cliente(self, loja, usado_mb, limite_mb, percentual):
    """Envia alerta de 80% de uso de storage para o cliente"""
    assunto = f'⚠️ {loja.nome} - Espaço em disco atingindo o limite'
    
    mensagem = f"""
    Olá {loja.owner.get_full_name() or loja.owner.username},
    
    Seu sistema {loja.nome} está utilizando {percentual:.1f}% do espaço em disco contratado.
    
    📊 Uso atual: {usado_mb:.2f} MB de {limite_mb} MB
    📦 Plano: {loja.plano.nome} ({loja.plano.espaco_storage_gb} GB)
    
    ⚠️ ATENÇÃO: Quando atingir 100% do limite, o sistema será bloqueado automaticamente
    para evitar perda de dados.
    
    💡 SOLUÇÃO: Entre em contato conosco para fazer upgrade do seu plano e aumentar
    o espaço disponível.
    
    📞 Suporte: suporte@lwksistemas.com.br
    🌐 Painel: https://lwksistemas.com.br/loja/{loja.slug}/dashboard
    
    Atenciosamente,
    Equipe LWK Sistemas
    """
    
    return self._enviar_email(
        destinatario=loja.owner.email,
        assunto=assunto,
        mensagem=mensagem
    )

def enviar_alerta_storage_admin(self, loja, usado_mb, limite_mb, percentual):
    """Envia alerta de 80% de uso de storage para o superadmin"""
    assunto = f'⚠️ ADMIN - {loja.nome} atingiu {percentual:.1f}% do storage'
    
    mensagem = f"""
    ALERTA DE STORAGE
    
    Loja: {loja.nome}
    Proprietário: {loja.owner.get_full_name()} ({loja.owner.email})
    Plano: {loja.plano.nome}
    
    📊 Uso: {usado_mb:.2f} MB / {limite_mb} MB ({percentual:.1f}%)
    📦 Limite do plano: {loja.plano.espaco_storage_gb} GB
    
    ⚠️ Ação necessária: Entrar em contato com o cliente para oferecer upgrade.
    
    🔗 Painel Admin: https://lwksistemas.com.br/superadmin/lojas/{loja.id}
    """
    
    # Enviar para todos os superadmins
    from django.contrib.auth import get_user_model
    User = get_user_model()
    superadmins = User.objects.filter(is_superuser=True)
    
    for admin in superadmins:
        self._enviar_email(
            destinatario=admin.email,
            assunto=assunto,
            mensagem=mensagem
        )
```

### 4. Configurar Heroku Scheduler

**Comando para executar a cada 6 horas**:
```bash
python backend/manage.py verificar_storage_lojas
```

### 5. Adicionar Endpoint para Verificação Manual

**Arquivo**: `backend/superadmin/views.py`

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verificar_storage_loja(request, loja_id):
    """Verifica storage de uma loja específica (manual)"""
    if not request.user.is_superuser:
        return Response({'error': 'Apenas superadmin'}, status=403)
    
    try:
        loja = Loja.objects.get(id=loja_id)
        
        # Executar verificação
        from django.core.management import call_command
        call_command('verificar_storage_lojas')
        
        # Retornar dados atualizados
        loja.refresh_from_db()
        
        return Response({
            'loja': loja.nome,
            'storage_usado_mb': float(loja.storage_usado_mb),
            'storage_limite_mb': loja.storage_limite_mb,
            'percentual': (float(loja.storage_usado_mb) / loja.storage_limite_mb) * 100,
            'alerta_enviado': loja.storage_alerta_enviado,
            'ultima_verificacao': loja.storage_ultima_verificacao
        })
    
    except Loja.DoesNotExist:
        return Response({'error': 'Loja não encontrada'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
```

### 6. Adicionar Dashboard de Storage no Frontend

**Componente**: `frontend/app/(dashboard)/superadmin/storage/page.tsx`

```tsx
// Dashboard mostrando uso de storage de todas as lojas
// Com gráficos, alertas e opção de upgrade
```

## Implementação

### Ordem de Implementação:

1. ✅ **Migration**: Adicionar campos no modelo `Loja`
2. ✅ **Comando**: Criar `verificar_storage_lojas.py`
3. ✅ **EmailService**: Adicionar métodos de alerta
4. ✅ **Endpoint**: Criar endpoint de verificação manual
5. ✅ **Heroku Scheduler**: Configurar execução automática
6. ✅ **Frontend**: Dashboard de storage (opcional)
7. ✅ **Testes**: Testar com loja real

### Estimativa de Tempo:

- Backend (migration + comando + email): 2-3 horas
- Endpoint + testes: 1 hora
- Frontend (dashboard): 2-3 horas
- **Total**: 5-7 horas

## Observações Importantes

1. **PostgreSQL vs SQLite**:
   - Em produção (PostgreSQL), cada loja tem um schema separado
   - Comando deve calcular tamanho do schema, não do banco inteiro
   - Query correta: `pg_total_relation_size('schema_name')`

2. **Performance**:
   - Verificação pode ser lenta para muitas lojas
   - Executar em background (Heroku Scheduler)
   - Não executar em horário de pico

3. **Limites por Plano**:
   - Básico: 5 GB (5120 MB)
   - Premium: 50 GB (51200 MB)
   - Enterprise: 200 GB (204800 MB)
   - Alerta em 80%: 4 GB, 40 GB, 160 GB respectivamente

4. **Bloqueio Automático**:
   - Quando atingir 100%, bloquear loja automaticamente
   - Enviar email urgente para cliente e admin
   - Cliente deve fazer upgrade para desbloquear

## Próximos Passos

Deseja que eu implemente este sistema completo de monitoramento de storage?

1. Criar migration para adicionar campos
2. Criar comando de verificação
3. Adicionar métodos no EmailService
4. Criar endpoint de verificação manual
5. Documentar configuração do Heroku Scheduler
