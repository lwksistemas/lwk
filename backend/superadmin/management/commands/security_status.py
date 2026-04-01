"""
Comando Django para verificar o status do sistema de segurança

Uso:
    python manage.py security_status
    
Exibe estatísticas sobre violações detectadas e status dos componentes de segurança.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from superadmin.models import ViolacaoSeguranca, HistoricoAcessoGlobal


class Command(BaseCommand):
    help = 'Exibe status do sistema de segurança e estatísticas de violações'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔒 STATUS DO SISTEMA DE SEGURANÇA\n'))
        
        # Estatísticas gerais
        self._exibir_estatisticas_gerais()
        
        # Violações por tipo
        self._exibir_violacoes_por_tipo()
        
        # Violações recentes
        self._exibir_violacoes_recentes()
        
        # Status dos componentes
        self._exibir_status_componentes()
    
    def _exibir_estatisticas_gerais(self):
        """Exibe estatísticas gerais de violações"""
        total = ViolacaoSeguranca.objects.count()
        novas = ViolacaoSeguranca.objects.filter(status='nova').count()
        investigando = ViolacaoSeguranca.objects.filter(status='investigando').count()
        resolvidas = ViolacaoSeguranca.objects.filter(status='resolvida').count()
        criticas = ViolacaoSeguranca.objects.filter(criticidade='critica').count()
        
        self.stdout.write('📊 ESTATÍSTICAS GERAIS')
        self.stdout.write(f'  Total de violações: {total}')
        self.stdout.write(f'  Novas: {novas}')
        self.stdout.write(f'  Em investigação: {investigando}')
        self.stdout.write(f'  Resolvidas: {resolvidas}')
        self.stdout.write(f'  Críticas: {criticas}\n')
    
    def _exibir_violacoes_por_tipo(self):
        """Exibe violações agrupadas por tipo"""
        self.stdout.write('📋 VIOLAÇÕES POR TIPO')
        
        tipos = ViolacaoSeguranca.objects.values_list('tipo', flat=True).distinct()
        
        for tipo in tipos:
            count = ViolacaoSeguranca.objects.filter(tipo=tipo).count()
            novas = ViolacaoSeguranca.objects.filter(tipo=tipo, status='nova').count()
            
            tipo_display = dict(ViolacaoSeguranca.TIPO_CHOICES).get(tipo, tipo)
            
            if novas > 0:
                self.stdout.write(f'  {tipo_display}: {count} ({novas} novas)')
            else:
                self.stdout.write(f'  {tipo_display}: {count}')
        
        self.stdout.write('')
    
    def _exibir_violacoes_recentes(self):
        """Exibe violações das últimas 24 horas"""
        cutoff = timezone.now() - timedelta(hours=24)
        recentes = ViolacaoSeguranca.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:5]
        
        self.stdout.write('🕐 VIOLAÇÕES RECENTES (últimas 24h)')
        
        if not recentes:
            self.stdout.write('  Nenhuma violação nas últimas 24 horas\n')
            return
        
        for v in recentes:
            tipo_display = dict(ViolacaoSeguranca.TIPO_CHOICES).get(v.tipo, v.tipo)
            criticidade_display = dict(ViolacaoSeguranca.CRITICIDADE_CHOICES).get(v.criticidade, v.criticidade)
            
            # Emoji baseado na criticidade
            emoji = {
                'critica': '🔴',
                'alta': '🟠',
                'media': '🟡',
                'baixa': '🟢'
            }.get(v.criticidade, '⚪')
            
            self.stdout.write(
                f'  {emoji} {tipo_display} - {criticidade_display} - '
                f'{v.usuario_email} - {v.created_at.strftime("%d/%m/%Y %H:%M")}'
            )
        
        self.stdout.write('')
    
    def _exibir_status_componentes(self):
        """Exibe status dos componentes de segurança"""
        self.stdout.write('⚙️  STATUS DOS COMPONENTES')
        
        # Verificar se há logs recentes (indica que middleware está ativo)
        cutoff = timezone.now() - timedelta(minutes=30)
        logs_recentes = HistoricoAcessoGlobal.objects.filter(created_at__gte=cutoff).count()
        
        if logs_recentes > 0:
            self.stdout.write('  ✅ SecurityLoggingMiddleware: ATIVO')
            self.stdout.write(f'     ({logs_recentes} logs nos últimos 30 minutos)')
        else:
            self.stdout.write('  ⚠️  SecurityLoggingMiddleware: SEM ATIVIDADE RECENTE')
        
        # Verificar última execução do detector
        ultima_deteccao = ViolacaoSeguranca.objects.order_by('-created_at').first()
        
        if ultima_deteccao:
            tempo_desde = timezone.now() - ultima_deteccao.created_at
            minutos = int(tempo_desde.total_seconds() / 60)
            
            if minutos < 15:
                self.stdout.write(f'  ✅ SecurityDetector: ATIVO (última execução há {minutos} minutos)')
            elif minutos < 60:
                self.stdout.write(f'  ⚠️  SecurityDetector: ATIVO (última execução há {minutos} minutos)')
            else:
                horas = int(minutos / 60)
                self.stdout.write(f'  ⚠️  SecurityDetector: INATIVO (última execução há {horas} horas)')
        else:
            self.stdout.write('  ⚠️  SecurityDetector: NUNCA EXECUTADO')
        
        self.stdout.write('')
        
        # Recomendações
        self._exibir_recomendacoes(logs_recentes, ultima_deteccao)
    
    def _exibir_recomendacoes(self, logs_recentes, ultima_deteccao):
        """Exibe recomendações baseadas no status"""
        self.stdout.write('💡 RECOMENDAÇÕES')
        
        if logs_recentes == 0:
            self.stdout.write('  ⚠️  Middleware não está registrando logs. Verifique a configuração.')
        
        if not ultima_deteccao:
            self.stdout.write('  ⚠️  SecurityDetector nunca foi executado.')
            self.stdout.write('     Execute: python manage.py detect_security_violations')
            self.stdout.write('     Configure o Heroku Scheduler para execução automática.')
        else:
            tempo_desde = timezone.now() - ultima_deteccao.created_at
            minutos = int(tempo_desde.total_seconds() / 60)
            
            if minutos > 60:
                self.stdout.write('  ⚠️  SecurityDetector não executa há muito tempo.')
                self.stdout.write('     Verifique se o Heroku Scheduler está configurado.')
        
        # Verificar violações não resolvidas
        nao_resolvidas = ViolacaoSeguranca.objects.filter(
            status__in=['nova', 'investigando'],
            criticidade__in=['critica', 'alta']
        ).count()
        
        if nao_resolvidas > 0:
            self.stdout.write(f'  🚨 {nao_resolvidas} violações críticas/altas não resolvidas!')
            self.stdout.write('     Acesse: https://lwksistemas.com.br/superadmin/dashboard/alertas')
        
        self.stdout.write('')
