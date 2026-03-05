# Sistema de Backup das Lojas - v800

## 📋 Visão Geral

Sistema completo de backup e restauração de dados das lojas, com exportação/importação em CSV e envio automático por email.

## 🎯 Objetivos

1. **Botão de Backup no Dashboard**: Adicionar botões de Importar e Exportar no dashboard de cada loja
2. **Envio Automático por Email**: Configurar horário para envio automático do backup para o email do admin da loja
3. **Formato CSV**: Exportar todos os dados da loja em formato CSV compactado (ZIP)

## 🏗️ Arquitetura

### Backend (Django)

#### 1. Novo Modelo: `ConfiguracaoBackup`
```python
# backend/superadmin/models.py

class ConfiguracaoBackup(models.Model):
    """Configuração de backup automático para cada loja"""
    loja = models.OneToOneField(Loja, on_delete=models.CASCADE, related_name='config_backup')
    
    # Configuração de envio automático
    backup_automatico_ativo = models.BooleanField(default=False)
    horario_envio = models.TimeField(default='03:00:00', help_text='Horário para envio automático (formato 24h)')
    frequencia = models.CharField(
        max_length=20,
        choices=[
            ('diario', 'Diário'),
            ('semanal', 'Semanal'),
            ('mensal', 'Mensal'),
        ],
        default='semanal'
    )
    dia_semana = models.IntegerField(
        null=True, blank=True,
        choices=[(0, 'Segunda'), (1, 'Terça'), (2, 'Quarta'), (3, 'Quinta'), 
                 (4, 'Sexta'), (5, 'Sábado'), (6, 'Domingo')],
        help_text='Dia da semana para backup semanal'
    )
    dia_mes = models.IntegerField(
        null=True, blank=True,
        help_text='Dia do mês para backup mensal (1-28)'
    )
    
    # Histórico
    ultimo_backup = models.DateTimeField(null=True, blank=True)
    ultimo_envio_email = models.DateTimeField(null=True, blank=True)
    total_backups_realizados = models.IntegerField(default=0)
    
    # Configurações adicionais
    incluir_imagens = models.BooleanField(default=False, help_text='Incluir imagens no backup (aumenta tamanho)')
    manter_ultimos_n_backups = models.IntegerField(default=5, help_text='Quantidade de backups a manter no servidor')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração de Backup'
        verbose_name_plural = 'Configurações de Backup'
```

#### 2. Novo Modelo: `HistoricoBackup`
```python
class HistoricoBackup(models.Model):
    """Histórico de backups realizados"""
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='historico_backups')
    
    TIPO_CHOICES = [
        ('manual', 'Manual'),
        ('automatico', 'Automático'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # Informações do backup
    arquivo_nome = models.CharField(max_length=255)
    arquivo_tamanho_mb = models.DecimalField(max_digits=10, decimal_places=2)
    arquivo_path = models.CharField(max_length=500, blank=True)
    
    # Estatísticas
    total_registros = models.IntegerField(default=0)
    tabelas_incluidas = models.JSONField(default=dict, help_text='Dicionário com contagem por tabela')
    
    # Status
    STATUS_CHOICES = [
        ('processando', 'Processando'),
        ('concluido', 'Concluído'),
        ('erro', 'Erro'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processando')
    erro_mensagem = models.TextField(blank=True)
    
    # Email
    email_enviado = models.BooleanField(default=False)
    email_enviado_em = models.DateTimeField(null=True, blank=True)
    
    # Usuário que solicitou (para backups manuais)
    solicitado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Histórico de Backup'
        verbose_name_plural = 'Histórico de Backups'
        ordering = ['-created_at']
```

#### 3. Serviço de Backup: `backup_service.py`
```python
# backend/superadmin/backup_service.py

import csv
import zipfile
import io
from datetime import datetime
from django.db import connections
from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class BackupService:
    """Serviço para gerenciar backups de lojas"""
    
    TABELAS_BACKUP = [
        'clientes',
        'produtos',
        'servicos',
        'profissionais',
        'agendamentos',
        'vendas',
        'itens_venda',
        'pagamentos',
        'estoque',
        'movimentacoes_estoque',
        'categorias',
        'fornecedores',
    ]
    
    def exportar_loja(self, loja_id: int, incluir_imagens: bool = False) -> dict:
        """
        Exporta todos os dados de uma loja em formato CSV compactado
        
        Returns:
            dict com 'success', 'arquivo_nome', 'arquivo_bytes', 'tamanho_mb', 'total_registros'
        """
        pass
    
    def importar_loja(self, loja_id: int, arquivo_zip: bytes) -> dict:
        """
        Importa dados de um arquivo ZIP de backup
        
        Returns:
            dict com 'success', 'message', 'total_registros_importados'
        """
        pass
    
    def enviar_backup_email(self, loja_id: int, historico_backup_id: int) -> bool:
        """
        Envia backup por email para o admin da loja
        """
        pass
```

#### 4. Task Celery para Backup Automático
```python
# backend/superadmin/tasks.py

from celery import shared_task
from django.utils import timezone
from .models import ConfiguracaoBackup, Loja
from .backup_service import BackupService

@shared_task
def executar_backups_automaticos():
    """
    Task executada periodicamente (a cada hora) para verificar
    se há backups agendados para serem executados
    """
    pass

@shared_task
def processar_backup_loja(loja_id: int, tipo: str = 'automatico', user_id: int = None):
    """
    Task assíncrona para processar backup de uma loja
    """
    pass
```

#### 5. Endpoints da API
```python
# backend/superadmin/views.py - LojaViewSet

@action(detail=True, methods=['post'])
def exportar_backup(self, request, pk=None):
    """Exportar backup manual da loja"""
    pass

@action(detail=True, methods=['post'])
def importar_backup(self, request, pk=None):
    """Importar backup para a loja"""
    pass

@action(detail=True, methods=['get'])
def configuracao_backup(self, request, pk=None):
    """Obter configuração de backup da loja"""
    pass

@action(detail=True, methods=['put', 'patch'])
def atualizar_configuracao_backup(self, request, pk=None):
    """Atualizar configuração de backup"""
    pass

@action(detail=True, methods=['get'])
def historico_backups(self, request, pk=None):
    """Listar histórico de backups da loja"""
    pass

@action(detail=True, methods=['post'])
def reenviar_backup_email(self, request, pk=None):
    """Reenviar último backup por email"""
    pass
```

### Frontend (Next.js)

#### 1. Novo Hook: `useBackup`
```typescript
// frontend/hooks/useBackup.ts

export function useBackup(lojaId: number) {
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState<ConfiguracaoBackup | null>(null);
  const [historico, setHistorico] = useState<HistoricoBackup[]>([]);
  
  const exportarBackup = async () => { /* ... */ };
  const importarBackup = async (file: File) => { /* ... */ };
  const atualizarConfig = async (data: Partial<ConfiguracaoBackup>) => { /* ... */ };
  const carregarHistorico = async () => { /* ... */ };
  
  return { loading, config, historico, exportarBackup, importarBackup, atualizarConfig, carregarHistorico };
}
```

#### 2. Componente: `BackupCard`
```typescript
// frontend/components/superadmin/lojas/BackupCard.tsx

export function BackupCard({ loja }: { loja: Loja }) {
  const { exportarBackup, importarBackup, loading } = useBackup(loja.id);
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">💾 Backup da Loja</h3>
      
      <div className="flex gap-3">
        <button onClick={exportarBackup} disabled={loading}>
          📤 Exportar Backup
        </button>
        
        <label className="btn">
          📥 Importar Backup
          <input type="file" accept=".zip" onChange={(e) => importarBackup(e.target.files[0])} />
        </label>
      </div>
    </div>
  );
}
```

#### 3. Modal: `ModalConfiguracaoBackup`
```typescript
// frontend/components/superadmin/lojas/ModalConfiguracaoBackup.tsx

export function ModalConfiguracaoBackup({ loja, onClose }: Props) {
  const { config, atualizarConfig, historico, carregarHistorico } = useBackup(loja.id);
  
  return (
    <Modal onClose={onClose}>
      <h2>⚙️ Configuração de Backup - {loja.nome}</h2>
      
      {/* Formulário de configuração */}
      <form>
        <label>
          <input type="checkbox" checked={config?.backup_automatico_ativo} />
          Ativar backup automático
        </label>
        
        <select name="frequencia">
          <option value="diario">Diário</option>
          <option value="semanal">Semanal</option>
          <option value="mensal">Mensal</option>
        </select>
        
        <input type="time" name="horario_envio" value={config?.horario_envio} />
        
        {/* ... mais campos ... */}
      </form>
      
      {/* Histórico de backups */}
      <div className="mt-6">
        <h3>📋 Histórico de Backups</h3>
        <table>
          {/* ... lista de backups ... */}
        </table>
      </div>
    </Modal>
  );
}
```

#### 4. Adicionar ao Dashboard da Loja
```typescript
// frontend/app/(dashboard)/superadmin/lojas/page.tsx

// Adicionar botão "Configurar Backup" em cada LojaCard
<button onClick={() => abrirModalBackup(loja)}>
  ⚙️ Backup
</button>
```

## 📊 Fluxo de Dados

### Exportação Manual
1. Admin clica em "Exportar Backup" no dashboard
2. Frontend chama `POST /api/superadmin/lojas/{id}/exportar_backup/`
3. Backend cria task Celery assíncrona
4. Task conecta no banco isolado da loja
5. Exporta cada tabela para CSV
6. Compacta todos os CSVs em um ZIP
7. Salva registro em `HistoricoBackup`
8. Retorna arquivo ZIP para download

### Importação Manual
1. Admin faz upload do arquivo ZIP
2. Frontend chama `POST /api/superadmin/lojas/{id}/importar_backup/`
3. Backend valida estrutura do ZIP
4. Cria backup de segurança antes de importar
5. Importa dados tabela por tabela
6. Valida integridade referencial
7. Retorna resultado da importação

### Backup Automático
1. Celery Beat executa task `executar_backups_automaticos` a cada hora
2. Task verifica todas as `ConfiguracaoBackup` ativas
3. Para cada loja que deve fazer backup naquele horário:
   - Cria task assíncrona `processar_backup_loja`
   - Task exporta dados para ZIP
   - Salva arquivo no storage
   - Envia email com anexo para admin da loja
   - Atualiza `ConfiguracaoBackup.ultimo_backup`
   - Limpa backups antigos (mantém últimos N)

## 🔐 Segurança

1. **Permissões**: Apenas SuperAdmin e Owner da loja podem fazer backup/restore
2. **Validação**: Verificar integridade do ZIP antes de importar
3. **Backup de Segurança**: Criar snapshot antes de qualquer importação
4. **Logs**: Registrar todas as operações em `HistoricoAcessoGlobal`
5. **Limite de Tamanho**: Máximo 500MB por arquivo de backup
6. **Rate Limiting**: Máximo 1 backup manual por hora por loja

## 📧 Template de Email

```
Assunto: Backup Automático - {loja.nome} - {data}

Olá {owner.first_name},

Segue em anexo o backup automático da sua loja "{loja.nome}".

📊 Informações do Backup:
- Data/Hora: {datetime.now()}
- Total de Registros: {total_registros}
- Tamanho do Arquivo: {tamanho_mb} MB
- Tabelas Incluídas: {lista_tabelas}

⚠️ IMPORTANTE:
- Guarde este arquivo em local seguro
- Use este backup apenas em caso de necessidade
- Para restaurar, acesse o painel de administração

Atenciosamente,
Equipe {settings.SITE_NAME}
```

## 🚀 Implementação por Fases

### Fase 1: Backend - Modelos e Serviço Base
- [ ] Criar modelos `ConfiguracaoBackup` e `HistoricoBackup`
- [ ] Implementar `BackupService.exportar_loja()`
- [ ] Implementar `BackupService.importar_loja()`
- [ ] Criar migrations

### Fase 2: Backend - API Endpoints
- [ ] Endpoint `exportar_backup`
- [ ] Endpoint `importar_backup`
- [ ] Endpoint `configuracao_backup`
- [ ] Endpoint `atualizar_configuracao_backup`
- [ ] Endpoint `historico_backups`

### Fase 3: Backend - Automação
- [ ] Implementar task Celery `executar_backups_automaticos`
- [ ] Implementar task `processar_backup_loja`
- [ ] Configurar Celery Beat schedule
- [ ] Implementar `BackupService.enviar_backup_email()`

### Fase 4: Frontend - Componentes Base
- [ ] Criar hook `useBackup`
- [ ] Criar componente `BackupCard`
- [ ] Adicionar botões no `LojaCard`

### Fase 5: Frontend - Configuração
- [ ] Criar `ModalConfiguracaoBackup`
- [ ] Implementar formulário de configuração
- [ ] Implementar visualização de histórico

### Fase 6: Testes e Ajustes
- [ ] Testar exportação manual
- [ ] Testar importação manual
- [ ] Testar backup automático
- [ ] Testar envio de email
- [ ] Ajustar performance para lojas grandes

## 📝 Notas Técnicas

### Otimizações
- Usar `select_related` e `prefetch_related` nas queries
- Processar CSVs em chunks para lojas grandes
- Usar streaming para download de arquivos grandes
- Implementar cache para configurações de backup

### Monitoramento
- Adicionar métricas no dashboard: total de backups, taxa de sucesso, tamanho médio
- Alertas para backups falhados
- Logs detalhados de cada operação

### Escalabilidade
- Usar storage externo (S3) para arquivos de backup
- Implementar compressão adicional para lojas grandes
- Considerar backup incremental no futuro
