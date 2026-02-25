"""
Django management command para reprocessar emails falhados

✅ NOVO v719: Comando para retry manual de emails

Uso:
    python manage.py reprocessar_emails_falhados
    python manage.py reprocessar_emails_falhados --limit 10
    python manage.py reprocessar_emails_falhados --loja minha-loja
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F
from superadmin.models import EmailRetry
from superadmin.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reprocessa emails falhados que estão aguardando retry'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limita o número de emails a processar'
        )
        parser.add_argument(
            '--loja',
            type=str,
            default=None,
            help='Processa apenas emails de uma loja específica (slug)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força reprocessamento mesmo se proxima_tentativa ainda não chegou'
        )
    
    def handle(self, *args, **options):
        limit = options.get('limit')
        loja_slug = options.get('loja')
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('🔄 Iniciando reprocessamento de emails falhados...'))
        
        # Buscar emails pendentes
        queryset = EmailRetry.objects.filter(
            enviado=False,
            tentativas__lt=F('max_tentativas')
        )
        
        # Filtrar por loja se especificado
        if loja_slug:
            queryset = queryset.filter(loja__slug=loja_slug)
            self.stdout.write(f"   Filtrando por loja: {loja_slug}")
        
        # Filtrar por proxima_tentativa se não for force
        if not force:
            queryset = queryset.filter(proxima_tentativa__lte=timezone.now())
        else:
            self.stdout.write(self.style.WARNING('   ⚠️ Modo FORCE ativado - ignorando proxima_tentativa'))
        
        # Aplicar limit se especificado
        if limit:
            queryset = queryset[:limit]
            self.stdout.write(f"   Limitando a {limit} emails")
        
        # Ordenar por prioridade
        emails = queryset.order_by('tentativas', 'proxima_tentativa')
        
        total = emails.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('   Nenhum email pendente para reprocessar'))
            return
        
        self.stdout.write(f"   Encontrados {total} emails para reprocessar\n")
        
        # Reprocessar emails
        service = EmailService()
        sucesso = 0
        falha = 0
        
        for email in emails:
            self.stdout.write(f"   Processando email {email.id}...")
            self.stdout.write(f"      Para: {email.destinatario}")
            self.stdout.write(f"      Assunto: {email.assunto[:50]}...")
            self.stdout.write(f"      Tentativas: {email.tentativas}/{email.max_tentativas}")
            
            if service.reenviar_email(email.id):
                sucesso += 1
                self.stdout.write(self.style.SUCCESS(f"      ✅ Enviado com sucesso"))
            else:
                falha += 1
                self.stdout.write(self.style.ERROR(f"      ❌ Falha ao enviar"))
            
            self.stdout.write("")  # Linha em branco
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'✅ Reprocessamento concluído!'))
        self.stdout.write(self.style.SUCCESS(f'   Total processados: {total}'))
        self.stdout.write(self.style.SUCCESS(f'   Enviados com sucesso: {sucesso}'))
        
        if falha > 0:
            self.stdout.write(self.style.ERROR(f'   Falhas: {falha}'))
        
        self.stdout.write(self.style.SUCCESS('='*60))
        
        # Estatísticas adicionais
        pendentes_restantes = EmailRetry.objects.filter(
            enviado=False,
            tentativas__lt=F('max_tentativas')
        ).count()
        
        falhados_definitivos = EmailRetry.objects.filter(
            enviado=False,
            tentativas__gte=F('max_tentativas')
        ).count()
        
        self.stdout.write(f'\n📊 Estatísticas:')
        self.stdout.write(f'   Emails pendentes restantes: {pendentes_restantes}')
        self.stdout.write(f'   Emails falhados definitivamente: {falhados_definitivos}')
        
        if falhados_definitivos > 0:
            self.stdout.write(self.style.WARNING(
                f'\n⚠️ {falhados_definitivos} email(s) atingiram o máximo de tentativas.'
            ))
            self.stdout.write(self.style.WARNING(
                '   Verifique os logs e considere reenvio manual ou correção do problema.'
            ))
