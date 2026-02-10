"""
Comando para marcar violações de privilege_escalation como falso positivo
quando são acessos legítimos de donos de loja
"""
from django.core.management.base import BaseCommand
from superadmin.models import ViolacaoSeguranca


class Command(BaseCommand):
    help = 'Marca violações de privilege_escalation como falso positivo quando são acessos legítimos'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Buscando violações de privilege_escalation com status "nova"...')
        
        # Endpoints legítimos para donos de loja
        ENDPOINTS_LEGITIMOS = [
            '/superadmin/lojas/',
            '/superadmin/lojas/info_publica/',
            '/superadmin/lojas/verificar_senha_provisoria/',
            '/superadmin/lojas/debug_senha_status/',
            '/superadmin/usuarios/verificar_senha_provisoria/',
            '/superadmin/usuarios/alterar_senha_primeiro_acesso/',
            '/superadmin/usuarios/recuperar_senha/',
            'alterar_senha_primeiro_acesso',
            'reenviar_senha',
        ]
        
        # Buscar violações de privilege_escalation com status "nova"
        violacoes = ViolacaoSeguranca.objects.filter(
            tipo='privilege_escalation',
            status='nova'
        )
        
        total = violacoes.count()
        self.stdout.write(f'📊 Total de violações encontradas: {total}')
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Nenhuma violação encontrada'))
            return
        
        marcadas = 0
        
        for violacao in violacoes:
            # Verificar se as URLs acessadas são legítimas
            detalhes = violacao.detalhes_tecnicos or {}
            urls_acessadas = detalhes.get('urls_acessadas', [])
            
            # Verificar se TODAS as URLs são legítimas
            todas_legitimas = True
            for url in urls_acessadas:
                is_legitima = any(endpoint in url for endpoint in ENDPOINTS_LEGITIMOS)
                if not is_legitima:
                    todas_legitimas = False
                    break
            
            if todas_legitimas:
                # Marcar como falso positivo
                violacao.status = 'falso_positivo'
                violacao.notas = (
                    f"{violacao.notas or ''}\n\n"
                    f"[AUTO] Marcado como falso positivo automaticamente.\n"
                    f"Motivo: Todas as URLs acessadas são endpoints legítimos para donos de loja.\n"
                    f"URLs: {', '.join(urls_acessadas)}"
                ).strip()
                violacao.save()
                
                marcadas += 1
                self.stdout.write(
                    f'✅ Violação #{violacao.id} marcada como falso positivo: '
                    f'{violacao.usuario_email} ({len(urls_acessadas)} URLs legítimas)'
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Processo concluído!'))
        self.stdout.write(f'📊 Total de violações: {total}')
        self.stdout.write(f'✅ Marcadas como falso positivo: {marcadas}')
        self.stdout.write(f'⚠️  Ainda requerem análise: {total - marcadas}')
