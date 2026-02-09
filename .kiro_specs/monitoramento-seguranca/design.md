# Design Document: Sistema de Monitoramento e Segurança

## Overview

O Sistema de Monitoramento e Segurança é uma solução abrangente para monitorar atividades, detectar violações de segurança e fornecer auditoria completa em um sistema multi-tenant Django. O sistema será implementado como uma extensão do painel SuperAdmin existente em https://lwksistemas.com.br/superadmin/dashboard.

### Objetivos Principais

1. **Corrigir identificação de usuários nos logs**: Resolver o problema crítico onde admin da loja aparece como "SuperAdmin" nos registros de histórico
2. **Fornecer visibilidade de segurança**: Dashboards para visualizar violações e alertas em tempo real
3. **Habilitar auditoria completa**: Ferramentas para análise de logs com gráficos e estatísticas
4. **Detectar ameaças automaticamente**: Sistema de detecção de padrões suspeitos (brute force, rate limit, cross-tenant access)
5. **Facilitar investigações**: Busca avançada e análise de logs estruturados

### Arquitetura Geral

O sistema segue uma arquitetura em camadas:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │  Dashboard   │  │    Busca     │      │
│  │   Alertas    │  │  Auditoria   │  │     Logs     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                    REST API (JWT)
                            │
┌─────────────────────────────────────────────────────────────┐
│              Backend (Django REST Framework)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Violações   │  │  Estatísticas│  │    Busca     │      │
│  │   ViewSet    │  │   ViewSet    │  │   ViewSet    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Detector de Padrões (Background Task)        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │    Middleware de Histórico (CORRIGIDO)               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                  Banco de Dados (SQLite)                     │
│  ┌──────────────────────┐  ┌──────────────────────┐         │
│  │ HistoricoAcessoGlobal│  │ ViolacaoSeguranca    │         │
│  │  (EXISTENTE)         │  │  (NOVO)              │         │
│  └──────────────────────┘  └──────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Architecture

### Componentes Principais

#### 1. Middleware de Histórico (Corrigido)

**Localização**: `backend/superadmin/historico_middleware.py`

**Problema Identificado**: O middleware atual registra ações após o `TenantMiddleware` limpar o contexto da loja, resultando em identificação incorreta de usuários.

**Solução**: Capturar `loja_id` ANTES de processar a resposta e armazená-lo no objeto `request` para uso posterior.

**Fluxo Corrigido**:
```python
def __call__(self, request):
    # 1. CAPTURAR loja_id ANTES da resposta (contexto ainda existe)
    from tenants.middleware import get_current_loja_id
    loja_id_contexto = get_current_loja_id()
    request._historico_loja_id = loja_id_contexto
    
    # 2. Processar requisição
    response = self.get_response(request)
    
    # 3. Registrar ação (usando loja_id capturado)
    self._registrar_acao(request, response)
    
    return response
```

**Modificações Necessárias**:
- Adicionar captura de `loja_id` no início do `__call__`
- Modificar `_registrar_acao` para usar `request._historico_loja_id`
- Adicionar logging para debug de captura de contexto

#### 2. Modelo de Violação de Segurança

**Localização**: `backend/superadmin/models.py` (novo modelo)

**Estrutura**:
```python
class ViolacaoSeguranca(models.Model):
    """
    Registra violações de segurança detectadas automaticamente
    """
    TIPO_CHOICES = [
        ('acesso_cross_tenant', 'Acesso Cross-Tenant'),
        ('brute_force', 'Tentativa de Brute Force'),
        ('rate_limit_exceeded', 'Rate Limit Excedido'),
        ('privilege_escalation', 'Escalação de Privilégios'),
        ('mass_deletion', 'Exclusão em Massa'),
        ('ip_change', 'Mudança de IP'),
        ('suspicious_pattern', 'Padrão Suspeito'),
    ]
    
    CRITICIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    
    STATUS_CHOICES = [
        ('nova', 'Nova'),
        ('investigando', 'Investigando'),
        ('resolvida', 'Resolvida'),
        ('falso_positivo', 'Falso Positivo'),
    ]
    
    # Identificação
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, db_index=True)
    criticidade = models.CharField(max_length=20, choices=CRITICIDADE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='nova', db_index=True)
    
    # Contexto
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    usuario_email = models.EmailField()
    usuario_nome = models.CharField(max_length=200)
    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, null=True, blank=True)
    loja_nome = models.CharField(max_length=200, blank=True)
    
    # Detalhes
    descricao = models.TextField()
    detalhes_tecnicos = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    
    # Logs relacionados
    logs_relacionados = models.ManyToManyField(HistoricoAcessoGlobal, related_name='violacoes')
    
    # Gestão
    resolvido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='violacoes_resolvidas')
    resolvido_em = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True)
    
    # Notificação
    notificado = models.BooleanField(default=False)
    notificado_em = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Índices**:
- `tipo + created_at`: Buscar violações por tipo
- `criticidade + status`: Filtrar violações críticas não resolvidas
- `user + created_at`: Histórico de violações por usuário
- `loja + created_at`: Violações por loja

#### 3. Detector de Padrões

**Localização**: `backend/superadmin/security_detector.py` (novo arquivo)

**Responsabilidade**: Analisar logs periodicamente e detectar padrões suspeitos.

**Padrões Detectados**:

1. **Brute Force**: Mais de 5 falhas de login em 10 minutos
2. **Rate Limit**: Mais de 100 ações em 1 minuto
3. **Cross-Tenant**: Tentativa de acessar recursos de outra loja
4. **Privilege Escalation**: Acesso a endpoints de SuperAdmin sem permissão
5. **Mass Deletion**: Mais de 10 exclusões em 5 minutos
6. **IP Change**: Acesso de IP diferente do habitual

**Implementação**:
```python
class SecurityDetector:
    """
    Detecta padrões suspeitos nos logs de acesso
    """
    
    def detect_brute_force(self, time_window_minutes=10, max_attempts=5):
        """Detecta tentativas de brute force"""
        cutoff_time = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Agrupar falhas de login por usuário
        failed_logins = HistoricoAcessoGlobal.objects.filter(
            acao='login',
            sucesso=False,
            created_at__gte=cutoff_time
        ).values('usuario_email').annotate(
            count=Count('id'),
            ips=ArrayAgg('ip_address', distinct=True)
        ).filter(count__gte=max_attempts)
        
        # Criar violações
        for login in failed_logins:
            self._create_violation(
                tipo='brute_force',
                criticidade='alta',
                usuario_email=login['usuario_email'],
                descricao=f"Detectadas {login['count']} tentativas de login falhadas em {time_window_minutes} minutos",
                detalhes={'ips': login['ips'], 'tentativas': login['count']}
            )
    
    def detect_rate_limit(self, time_window_minutes=1, max_actions=100):
        """Detecta excesso de requisições"""
        # Similar ao brute force, mas para qualquer ação
        pass
    
    def detect_cross_tenant(self):
        """Detecta tentativas de acesso cross-tenant"""
        # Analisar logs onde usuário de uma loja tenta acessar recursos de outra
        pass
    
    def detect_privilege_escalation(self):
        """Detecta tentativas de escalação de privilégios"""
        # Analisar logs onde usuário não-superadmin acessa endpoints de superadmin
        pass
    
    def detect_mass_deletion(self, time_window_minutes=5, max_deletions=10):
        """Detecta exclusões em massa"""
        pass
    
    def detect_ip_change(self):
        """Detecta mudanças suspeitas de IP"""
        # Comparar IP atual com IPs históricos do usuário
        pass
    
    def run_all_detections(self):
        """Executa todas as detecções"""
        self.detect_brute_force()
        self.detect_rate_limit()
        self.detect_cross_tenant()
        self.detect_privilege_escalation()
        self.detect_mass_deletion()
        self.detect_ip_change()
```

**Execução**: Task agendada (Celery ou Django-Q) executando a cada 5 minutos.

#### 4. ViewSets de API

**Localização**: `backend/superadmin/views.py`

##### ViolacaoSegurancaViewSet

```python
class ViolacaoSegurancaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar violações de segurança
    """
    permission_classes = [IsSuperAdmin]
    serializer_class = ViolacaoSegurancaSerializer
    
    def get_queryset(self):
        queryset = ViolacaoSeguranca.objects.all().select_related(
            'user', 'loja', 'resolvido_por'
        ).prefetch_related('logs_relacionados')
        
        # Filtros
        status = self.request.query_params.get('status')
        criticidade = self.request.query_params.get('criticidade')
        tipo = self.request.query_params.get('tipo')
        loja_id = self.request.query_params.get('loja_id')
        
        if status:
            queryset = queryset.filter(status=status)
        if criticidade:
            queryset = queryset.filter(criticidade=criticidade)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Marca violação como resolvida"""
        violacao = self.get_object()
        violacao.status = 'resolvida'
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get('notas', '')
        violacao.save()
        return Response({'status': 'resolvida'})
    
    @action(detail=True, methods=['post'])
    def marcar_falso_positivo(self, request, pk=None):
        """Marca violação como falso positivo"""
        violacao = self.get_object()
        violacao.status = 'falso_positivo'
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get('notas', '')
        violacao.save()
        return Response({'status': 'falso_positivo'})
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas de violações"""
        total = ViolacaoSeguranca.objects.count()
        por_status = ViolacaoSeguranca.objects.values('status').annotate(count=Count('id'))
        por_criticidade = ViolacaoSeguranca.objects.values('criticidade').annotate(count=Count('id'))
        por_tipo = ViolacaoSeguranca.objects.values('tipo').annotate(count=Count('id'))
        
        return Response({
            'total': total,
            'por_status': list(por_status),
            'por_criticidade': list(por_criticidade),
            'por_tipo': list(por_tipo)
        })
```

##### EstatisticasAuditoriaViewSet

```python
class EstatisticasAuditoriaViewSet(viewsets.ViewSet):
    """
    ViewSet para estatísticas de auditoria
    """
    permission_classes = [IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def acoes_por_dia(self, request):
        """Gráfico de ações por dia (últimos 30 dias)"""
        dias = int(request.query_params.get('dias', 30))
        data_inicio = timezone.now() - timedelta(days=dias)
        
        acoes = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio
        ).annotate(
            dia=TruncDate('created_at')
        ).values('dia').annotate(
            count=Count('id')
        ).order_by('dia')
        
        return Response(list(acoes))
    
    @action(detail=False, methods=['get'])
    def acoes_por_tipo(self, request):
        """Distribuição de ações por tipo"""
        acoes = HistoricoAcessoGlobal.objects.values('acao').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response(list(acoes))
    
    @action(detail=False, methods=['get'])
    def lojas_mais_ativas(self, request):
        """Ranking de lojas mais ativas"""
        limit = int(request.query_params.get('limit', 10))
        
        lojas = HistoricoAcessoGlobal.objects.exclude(
            loja__isnull=True
        ).values('loja_id', 'loja_nome').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        return Response(list(lojas))
    
    @action(detail=False, methods=['get'])
    def usuarios_mais_ativos(self, request):
        """Ranking de usuários mais ativos"""
        limit = int(request.query_params.get('limit', 10))
        
        usuarios = HistoricoAcessoGlobal.objects.values(
            'usuario_email', 'usuario_nome'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        return Response(list(usuarios))
    
    @action(detail=False, methods=['get'])
    def horarios_pico(self, request):
        """Distribuição de ações por hora do dia"""
        acoes = HistoricoAcessoGlobal.objects.annotate(
            hora=TruncHour('created_at')
        ).values('hora').annotate(
            count=Count('id')
        ).order_by('hora')
        
        return Response(list(acoes))
    
    @action(detail=False, methods=['get'])
    def taxa_sucesso(self, request):
        """Taxa de sucesso vs falha"""
        total = HistoricoAcessoGlobal.objects.count()
        sucessos = HistoricoAcessoGlobal.objects.filter(sucesso=True).count()
        falhas = total - sucessos
        
        return Response({
            'total': total,
            'sucessos': sucessos,
            'falhas': falhas,
            'taxa_sucesso': (sucessos / total * 100) if total > 0 else 0
        })
```

## Components and Interfaces

### Backend Components

#### 1. Models

**ViolacaoSeguranca** (novo):
- Campos: tipo, criticidade, status, user, loja, descricao, detalhes_tecnicos, ip_address, logs_relacionados, resolvido_por, resolvido_em, notas, notificado, created_at, updated_at
- Métodos: `__str__`, `get_criticidade_color`, `get_tipo_display_friendly`

**HistoricoAcessoGlobal** (existente, sem modificações):
- Já possui todos os campos necessários
- Índices já otimizados

#### 2. Serializers

**ViolacaoSegurancaSerializer**:
```python
class ViolacaoSegurancaSerializer(serializers.ModelSerializer):
    logs_relacionados_count = serializers.IntegerField(read_only=True)
    resolvido_por_nome = serializers.CharField(source='resolvido_por.get_full_name', read_only=True)
    
    class Meta:
        model = ViolacaoSeguranca
        fields = '__all__'
```

**HistoricoAcessoGlobalSerializer** (existente, sem modificações)

#### 3. ViewSets

- **ViolacaoSegurancaViewSet**: CRUD de violações + ações (resolver, marcar_falso_positivo, estatisticas)
- **EstatisticasAuditoriaViewSet**: Endpoints de estatísticas (acoes_por_dia, acoes_por_tipo, lojas_mais_ativas, etc.)
- **HistoricoAcessoGlobalViewSet** (existente): Busca e listagem de logs

#### 4. Middleware

**HistoricoAcessoMiddleware** (modificado):
- Captura `loja_id` antes de processar resposta
- Armazena em `request._historico_loja_id`
- Usa valor capturado ao registrar ação

#### 5. Background Tasks

**SecurityDetectorTask**:
- Executa `SecurityDetector.run_all_detections()` a cada 5 minutos
- Implementação: Django-Q ou Celery (preferência por Django-Q por simplicidade)

### Frontend Components

#### 1. Dashboard de Alertas

**Localização**: `frontend/app/superadmin/dashboard/alertas/page.tsx`

**Componentes**:
- `AlertasList`: Lista de violações com filtros
- `AlertaCard`: Card individual de violação
- `AlertaDetalhes`: Modal com detalhes completos
- `FiltrosAlertas`: Filtros (status, criticidade, tipo, período)

**Features**:
- Atualização automática a cada 30 segundos
- Contador de violações não lidas
- Cores por criticidade (vermelho=crítica, amarelo=média, verde=baixa)
- Ações rápidas (resolver, marcar falso positivo)

#### 2. Dashboard de Auditoria

**Localização**: `frontend/app/superadmin/dashboard/auditoria/page.tsx`

**Componentes**:
- `GraficoAcoesPorDia`: Gráfico de linha (Chart.js ou Recharts)
- `GraficoAcoesPorTipo`: Gráfico de pizza
- `RankingLojas`: Tabela com lojas mais ativas
- `RankingUsuarios`: Tabela com usuários mais ativos
- `GraficoHorariosPico`: Gráfico de barras
- `TaxaSucesso`: Indicador visual de taxa de sucesso

**Features**:
- Seletor de período (7 dias, 30 dias, 90 dias, customizado)
- Drill-down: Click em qualquer métrica abre logs detalhados
- Exportação de gráficos (PNG)
- Atualização de cache a cada 5 minutos

#### 3. Busca de Logs

**Localização**: `frontend/app/superadmin/dashboard/logs/page.tsx`

**Componentes**:
- `BuscaAvancada`: Formulário com múltiplos filtros
- `ResultadosLogs`: Tabela de resultados
- `LogDetalhes`: Modal com detalhes completos de um log
- `ContextoTemporal`: Timeline de ações antes/depois

**Features**:
- Busca por texto livre
- Filtros combinados (loja, usuário, ação, recurso, período, sucesso/falha)
- Highlight de termos de busca
- Exportação (CSV, JSON)
- Buscas salvas

## Data Models

### ViolacaoSeguranca

```python
{
    "id": 1,
    "tipo": "brute_force",
    "criticidade": "alta",
    "status": "nova",
    "user_id": 123,
    "usuario_email": "usuario@example.com",
    "usuario_nome": "João Silva",
    "loja_id": 45,
    "loja_nome": "Clínica Exemplo",
    "descricao": "Detectadas 7 tentativas de login falhadas em 10 minutos",
    "detalhes_tecnicos": {
        "ips": ["192.168.1.1", "192.168.1.2"],
        "tentativas": 7,
        "periodo": "10 minutos"
    },
    "ip_address": "192.168.1.1",
    "logs_relacionados": [101, 102, 103, 104, 105, 106, 107],
    "resolvido_por_id": null,
    "resolvido_em": null,
    "notas": "",
    "notificado": false,
    "notificado_em": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### HistoricoAcessoGlobal (existente)

```python
{
    "id": 101,
    "user_id": 123,
    "usuario_email": "admin@loja.com",
    "usuario_nome": "Admin Loja",
    "loja_id": 45,
    "loja_nome": "Clínica Exemplo",
    "loja_slug": "clinica-exemplo",
    "acao": "criar",
    "recurso": "Cliente",
    "recurso_id": 789,
    "detalhes": "{\"authenticated\": true, \"is_superuser\": false}",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "metodo_http": "POST",
    "url": "/api/clinica/clientes/",
    "sucesso": true,
    "erro": "",
    "created_at": "2024-01-15T10:25:00Z"
}
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Correção de Identificação de Loja em Logs

*For any* ação realizada por um Admin_Loja, o registro criado no HistoricoAcessoGlobal deve conter loja_id, loja_nome e loja_slug corretos e consistentes com a loja do usuário.

**Validates: Requirements 1.1, 1.3**

### Property 2: Distinção entre SuperAdmin e Admin_Loja

*For any* log no sistema, se o usuário é SuperAdmin, então loja deve ser null; se o usuário é Admin_Loja, então loja deve ser não-null e corresponder à loja do usuário.

**Validates: Requirements 1.4**

### Property 3: Ordenação de Violações

*For any* consulta ao endpoint de violações sem parâmetros de ordenação customizados, os resultados devem estar ordenados primeiro por criticidade (crítica > alta > média > baixa) e depois por data (mais recente primeiro).

**Validates: Requirements 2.2**

### Property 4: Filtros de Violações

*For any* combinação válida de filtros (tipo, loja, usuário, período), a API deve retornar apenas violações que atendem a TODOS os filtros aplicados.

**Validates: Requirements 2.4**

### Property 5: Atualização de Status de Violação

*For any* violação marcada como resolvida, os campos status, resolvido_por e resolvido_em devem ser atualizados corretamente, e resolvido_por deve ser o usuário que executou a ação.

**Validates: Requirements 2.7, 6.5**

### Property 6: Agrupamento de Ações por Dia

*For any* período de consulta, a API de estatísticas deve retornar ações agrupadas por dia, com cada dia contendo a contagem correta de ações daquele dia.

**Validates: Requirements 3.1**

### Property 7: Agrupamento de Ações por Tipo

*For any* consulta de ações por tipo, a soma das contagens de todos os tipos deve ser igual ao total de ações no período.

**Validates: Requirements 3.2**

### Property 8: Ranking de Lojas Ativas

*For any* consulta de ranking de lojas, as lojas devem estar ordenadas por número de ações (decrescente), e a contagem deve ser precisa.

**Validates: Requirements 3.3**

### Property 9: Ranking de Usuários Ativos

*For any* consulta de ranking de usuários, os usuários devem estar ordenados por número de ações (decrescente), e a contagem deve ser precisa.

**Validates: Requirements 3.4**

### Property 10: Agrupamento por Horário

*For any* consulta de horários de pico, as ações devem estar agrupadas por hora do dia, e a soma de todas as horas deve ser igual ao total de ações.

**Validates: Requirements 3.5**

### Property 11: Cálculo de Taxa de Sucesso

*For any* período, a taxa de sucesso calculada deve ser igual a (sucessos / total) * 100, onde sucessos + falhas = total.

**Validates: Requirements 3.7**

### Property 12: Busca por Texto Livre

*For any* termo de busca, todos os logs retornados devem conter o termo em pelo menos um dos campos: usuario_nome, usuario_email, acao, recurso, ou detalhes.

**Validates: Requirements 4.1**

### Property 13: Filtros Combinados de Logs

*For any* conjunto de filtros aplicados simultaneamente, um log só deve aparecer nos resultados se atender a TODOS os filtros.

**Validates: Requirements 4.2**

### Property 14: Exportação de Dados

*For any* conjunto de resultados exportados em CSV ou JSON, o arquivo gerado deve conter exatamente os mesmos dados retornados pela API, sem perda ou corrupção.

**Validates: Requirements 4.4**

### Property 15: Contexto Temporal de Logs

*For any* log selecionado, o contexto temporal deve retornar N logs anteriores e N logs posteriores do mesmo usuário, ordenados por timestamp.

**Validates: Requirements 4.6**

### Property 16: Persistência de Buscas Salvas

*For any* busca salva, recuperá-la deve retornar exatamente os mesmos filtros que foram salvos.

**Validates: Requirements 4.7**

### Property 17: Detecção de Cross-Tenant Access

*For any* tentativa de um usuário de loja A acessar recursos de loja B, o sistema deve criar uma ViolacaoSeguranca de tipo "acesso_cross_tenant".

**Validates: Requirements 5.1**

### Property 18: Detecção de Brute Force

*For any* usuário com mais de 5 falhas de login em 10 minutos, o sistema deve criar uma ViolacaoSeguranca de tipo "brute_force".

**Validates: Requirements 5.2**

### Property 19: Detecção de Rate Limit

*For any* usuário com mais de 100 ações em 1 minuto, o sistema deve criar uma ViolacaoSeguranca de tipo "rate_limit_exceeded".

**Validates: Requirements 5.3**

### Property 20: Detecção de Privilege Escalation

*For any* usuário não-SuperAdmin que acessa endpoints de SuperAdmin, o sistema deve criar uma ViolacaoSeguranca de tipo "privilege_escalation".

**Validates: Requirements 5.4**

### Property 21: Detecção de Mass Deletion

*For any* usuário que exclui mais de 10 registros em 5 minutos, o sistema deve criar uma ViolacaoSeguranca de tipo "mass_deletion".

**Validates: Requirements 5.5**

### Property 22: Detecção de Mudança de IP

*For any* usuário que acessa de um IP diferente dos últimos 10 acessos, o sistema deve criar um alerta de tipo "ip_change".

**Validates: Requirements 5.6**

### Property 23: Configuração de Thresholds

*For any* threshold configurado para um tipo de detecção, alterar o threshold deve afetar a detecção de violações daquele tipo.

**Validates: Requirements 5.8**

### Property 24: Campos Obrigatórios de Violações

*For any* ViolacaoSeguranca criada, os campos tipo, criticidade, status, usuario_email, usuario_nome, descricao, ip_address e created_at devem estar presentes e não-vazios.

**Validates: Requirements 6.1**

### Property 25: Criticidade Automática

*For any* tipo de violação, a criticidade atribuída automaticamente deve seguir o mapeamento: brute_force=alta, rate_limit_exceeded=média, acesso_cross_tenant=crítica, privilege_escalation=crítica, mass_deletion=alta, ip_change=baixa.

**Validates: Requirements 6.2**

### Property 26: Adição de Notas

*For any* violação, adicionar notas deve atualizar o campo notas sem afetar outros campos.

**Validates: Requirements 6.3**

### Property 27: Alteração de Status

*For any* violação, alterar o status deve atualizar o campo status e updated_at, mantendo outros campos inalterados.

**Validates: Requirements 6.4**

### Property 28: Bloqueio de Usuário

*For any* violação, bloquear o usuário associado deve desativar o usuário e registrar a ação no histórico.

**Validates: Requirements 6.6**

### Property 29: Histórico de Mudanças de Status

*For any* mudança de status de uma violação, o sistema deve registrar a mudança com timestamp, usuário que fez a mudança, e status anterior/novo.

**Validates: Requirements 6.7**

### Property 30: Notificação de Violações Críticas

*For any* ViolacaoSeguranca com criticidade "crítica", o sistema deve enviar notificação por email ao SuperAdmin.

**Validates: Requirements 7.1**

### Property 31: Agrupamento de Notificações

*For any* conjunto de violações do mesmo tipo criadas em um intervalo de 15 minutos, apenas uma notificação deve ser enviada.

**Validates: Requirements 7.2**

### Property 32: Configuração de Notificações

*For any* tipo de violação configurado para não notificar, violações daquele tipo não devem gerar notificações.

**Validates: Requirements 7.4**

### Property 33: Paginação de Logs

*For any* endpoint de listagem de logs, os resultados devem ser paginados com tamanho de página configurável e links para próxima/anterior página.

**Validates: Requirements 8.3**

### Property 34: Limpeza de Logs Antigos

*For any* execução do comando de limpeza, logs com created_at anterior a 90 dias devem ser removidos, e logs mais recentes devem ser mantidos.

**Validates: Requirements 8.4**

### Property 35: Arquivamento de Logs

*For any* situação onde o total de logs excede 1 milhão, logs com mais de 30 dias devem ser arquivados em arquivo separado.

**Validates: Requirements 8.5**

### Property 36: Permissões de SuperAdmin

*For any* endpoint do sistema de monitoramento, apenas usuários com is_superuser=True devem ter acesso.

**Validates: Requirements 9.7**

## Error Handling

### Middleware de Histórico

**Erro: Contexto de loja não disponível**
- Comportamento: Registrar ação com loja=null
- Log: Warning indicando que contexto não estava disponível
- Não deve quebrar a requisição

**Erro: Falha ao criar registro de histórico**
- Comportamento: Logar erro mas não interromper requisição
- Log: Error com stack trace completo
- Notificar administrador se erro persistir

### Detector de Padrões

**Erro: Falha ao detectar padrão específico**
- Comportamento: Logar erro e continuar com outras detecções
- Log: Error com detalhes do padrão que falhou
- Não deve interromper outras detecções

**Erro: Falha ao criar violação**
- Comportamento: Logar erro e continuar
- Log: Error com detalhes da violação que falhou
- Tentar novamente na próxima execução

### APIs

**Erro: Parâmetros inválidos**
- Status: 400 Bad Request
- Response: `{"error": "Parâmetro X inválido", "details": {...}}`

**Erro: Permissão negada**
- Status: 403 Forbidden
- Response: `{"error": "Apenas SuperAdmin pode acessar este recurso"}`

**Erro: Recurso não encontrado**
- Status: 404 Not Found
- Response: `{"error": "Violação não encontrada"}`

**Erro: Erro interno**
- Status: 500 Internal Server Error
- Response: `{"error": "Erro interno do servidor"}`
- Log: Error com stack trace completo
- Notificar administrador

### Frontend

**Erro: Falha ao carregar dados**
- Comportamento: Exibir mensagem de erro amigável
- Ação: Botão para tentar novamente
- Log: Console error com detalhes

**Erro: Timeout de requisição**
- Comportamento: Exibir mensagem indicando timeout
- Ação: Botão para tentar novamente
- Timeout: 30 segundos

**Erro: Sessão expirada**
- Comportamento: Redirecionar para login
- Mensagem: "Sua sessão expirou, faça login novamente"

## Testing Strategy

### Dual Testing Approach

O sistema utilizará uma abordagem dual de testes:

1. **Unit Tests**: Verificar exemplos específicos, edge cases e condições de erro
2. **Property Tests**: Verificar propriedades universais através de múltiplas entradas geradas

Ambos são complementares e necessários para cobertura abrangente.

### Unit Testing

**Foco**:
- Exemplos específicos que demonstram comportamento correto
- Edge cases (contexto de loja ausente, usuário anônimo, etc.)
- Condições de erro (falha ao criar registro, permissão negada, etc.)
- Integração entre componentes

**Exemplos**:
```python
def test_middleware_registra_acao_admin_loja():
    """Testa que middleware registra corretamente ação de admin de loja"""
    # Criar usuário admin de loja
    # Simular requisição com contexto de loja
    # Verificar que registro foi criado com loja_id correto

def test_middleware_sem_contexto_loja():
    """Edge case: middleware sem contexto de loja"""
    # Simular requisição sem contexto de loja
    # Verificar que registro foi criado com loja=null

def test_detector_brute_force_threshold():
    """Testa detecção de brute force no threshold exato"""
    # Criar exatamente 5 falhas de login em 10 minutos
    # Verificar que violação NÃO foi criada
    # Criar 6ª falha
    # Verificar que violação FOI criada
```

### Property-Based Testing

**Biblioteca**: `hypothesis` (Python) ou `fast-check` (TypeScript)

**Configuração**: Mínimo 100 iterações por teste

**Foco**:
- Propriedades universais que devem valer para todas as entradas
- Cobertura ampla através de geração aleatória de dados
- Invariantes do sistema

**Exemplos**:
```python
from hypothesis import given, strategies as st

@given(
    usuario=st.builds(User),
    loja=st.builds(Loja),
    acao=st.sampled_from(['criar', 'editar', 'excluir'])
)
def test_property_logs_admin_loja_tem_loja_id(usuario, loja, acao):
    """
    Feature: monitoramento-seguranca, Property 1: Correção de Identificação de Loja em Logs
    
    For any ação realizada por um Admin_Loja, o registro criado no 
    HistoricoAcessoGlobal deve conter loja_id, loja_nome e loja_slug corretos.
    """
    # Configurar usuário como admin da loja
    usuario.loja = loja
    
    # Simular ação
    registro = simular_acao(usuario, loja, acao)
    
    # Verificar propriedade
    assert registro.loja_id == loja.id
    assert registro.loja_nome == loja.nome
    assert registro.loja_slug == loja.slug

@given(
    violacoes=st.lists(st.builds(ViolacaoSeguranca), min_size=10, max_size=100)
)
def test_property_ordenacao_violacoes(violacoes):
    """
    Feature: monitoramento-seguranca, Property 3: Ordenação de Violações
    
    For any consulta ao endpoint de violações, os resultados devem estar 
    ordenados por criticidade e data.
    """
    # Salvar violações no banco
    for v in violacoes:
        v.save()
    
    # Consultar API
    response = api_client.get('/api/superadmin/violacoes/')
    resultados = response.json()['results']
    
    # Verificar ordenação
    for i in range(len(resultados) - 1):
        atual = resultados[i]
        proximo = resultados[i + 1]
        
        # Criticidade deve ser >= (crítica > alta > média > baixa)
        assert criticidade_valor(atual['criticidade']) >= criticidade_valor(proximo['criticidade'])
        
        # Se criticidade igual, data deve ser >=
        if atual['criticidade'] == proximo['criticidade']:
            assert atual['created_at'] >= proximo['created_at']

@given(
    logs=st.lists(st.builds(HistoricoAcessoGlobal), min_size=50, max_size=200),
    filtros=st.fixed_dictionaries({
        'loja_id': st.integers(min_value=1, max_value=10),
        'acao': st.sampled_from(['criar', 'editar', 'excluir']),
        'sucesso': st.booleans()
    })
)
def test_property_filtros_combinados(logs, filtros):
    """
    Feature: monitoramento-seguranca, Property 13: Filtros Combinados de Logs
    
    For any conjunto de filtros aplicados simultaneamente, um log só deve 
    aparecer nos resultados se atender a TODOS os filtros.
    """
    # Salvar logs
    for log in logs:
        log.save()
    
    # Aplicar filtros
    response = api_client.get('/api/superadmin/historico-acessos/', params=filtros)
    resultados = response.json()['results']
    
    # Verificar que todos os resultados atendem aos filtros
    for resultado in resultados:
        assert resultado['loja_id'] == filtros['loja_id']
        assert resultado['acao'] == filtros['acao']
        assert resultado['sucesso'] == filtros['sucesso']
```

### Integration Testing

**Foco**:
- Fluxos completos end-to-end
- Integração entre middleware, detector e APIs
- Integração entre backend e frontend

**Exemplos**:
```python
def test_fluxo_completo_deteccao_brute_force():
    """Testa fluxo completo de detecção de brute force"""
    # 1. Simular 6 falhas de login
    for i in range(6):
        simular_login_falho(usuario='teste@example.com')
    
    # 2. Executar detector
    detector = SecurityDetector()
    detector.detect_brute_force()
    
    # 3. Verificar que violação foi criada
    violacao = ViolacaoSeguranca.objects.filter(
        tipo='brute_force',
        usuario_email='teste@example.com'
    ).first()
    assert violacao is not None
    
    # 4. Verificar que notificação foi enviada
    assert len(mail.outbox) == 1
    assert 'brute force' in mail.outbox[0].subject.lower()
    
    # 5. Verificar que violação aparece na API
    response = api_client.get('/api/superadmin/violacoes/')
    assert any(v['id'] == violacao.id for v in response.json()['results'])
```

### Performance Testing

**Foco**:
- Latência do middleware (< 50ms)
- Tempo de resposta de APIs com grandes volumes (< 2s para 100k registros)
- Eficiência do detector de padrões

**Ferramentas**: `pytest-benchmark`, `locust`

### Test Coverage

**Meta**: Mínimo 80% de cobertura de código

**Áreas críticas** (meta 95%+):
- Middleware de histórico
- Detector de padrões
- ViewSets de API
- Serializers

**Comando**:
```bash
pytest --cov=superadmin --cov-report=html --cov-report=term
```

### Continuous Integration

**Pipeline**:
1. Lint (flake8, black, mypy)
2. Unit tests
3. Property tests (100 iterações)
4. Integration tests
5. Coverage report
6. Deploy (se todos os testes passarem)

**Ferramentas**: GitHub Actions, GitLab CI, ou Jenkins
