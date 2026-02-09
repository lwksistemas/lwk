"""
Comando Django para executar detecção de violações de segurança

Uso:
    python manage.py detect_security_violations
    
Este comando pode ser executado manualmente ou agendado via cron/celery.
"""
from django.core.management.base import BaseCommand
from superadmin.security_detector import SecurityDetector


class Command(BaseCommand):
    help = 'Detecta padrões suspeitos de segurança nos logs de acesso'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando detecção de violações de segurança...'))
        
        detector = SecurityDetector()
        resultados = detector.run_all_detections()
        
        total = sum(resultados.values())
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Detecção concluída!'))
        self.stdout.write(f'\n📊 Resumo:')
        self.stdout.write(f'  - Brute Force: {resultados["brute_force"]} violações')
        self.stdout.write(f'  - Rate Limit: {resultados["rate_limit"]} violações')
        self.stdout.write(f'  - Cross-Tenant: {resultados["cross_tenant"]} violações')
        self.stdout.write(f'  - Privilege Escalation: {resultados["privilege_escalation"]} violações')
        self.stdout.write(f'  - Mass Deletion: {resultados["mass_deletion"]} violações')
        self.stdout.write(f'  - IP Change: {resultados["ip_change"]} violações')
        self.stdout.write(f'\n  TOTAL: {total} violações criadas')
        
        if total > 0:
            self.stdout.write(self.style.WARNING(f'\n⚠️  {total} violações de segurança detectadas!'))
            self.stdout.write('Acesse o dashboard de alertas para mais detalhes.')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Nenhuma violação detectada.'))
