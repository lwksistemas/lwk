"""
Comando Django para enviar senha provisória manualmente

Uso:
python manage.py enviar_senha_manual <loja_slug>

Exemplo:
python manage.py enviar_senha_manual clinica-luiz-1845
"""
from django.core.management.base import BaseCommand, CommandError
from superadmin.models import Loja
from superadmin.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envia senha provisória manualmente para o administrador de uma loja'

    def add_arguments(self, parser):
        parser.add_argument(
            'loja_slug',
            type=str,
            help='Slug da loja (ex: clinica-luiz-1845)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o envio mesmo se a senha já foi enviada'
        )

    def handle(self, *args, **options):
        loja_slug = options['loja_slug']
        force = options.get('force', False)
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"ENVIO MANUAL DE SENHA PROVISÓRIA")
        self.stdout.write(f"{'='*80}\n")
        
        try:
            # Buscar loja
            loja = Loja.objects.get(slug=loja_slug)
            financeiro = loja.financeiro
            owner = loja.owner
            
            self.stdout.write(f"Loja: {loja.nome} ({loja.slug})")
            self.stdout.write(f"Owner: {owner.username} ({owner.email})")
            self.stdout.write(f"Status pagamento: {financeiro.status_pagamento}")
            self.stdout.write(f"Senha enviada: {financeiro.senha_enviada}")
            
            if financeiro.senha_enviada and not force:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  Senha já foi enviada em {financeiro.data_envio_senha}"
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        "Use --force para forçar o reenvio"
                    )
                )
                return
            
            # Verificar se pagamento está ativo
            if financeiro.status_pagamento != 'ativo':
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  Status do pagamento não é 'ativo': {financeiro.status_pagamento}"
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        "A senha só deve ser enviada após confirmação do pagamento"
                    )
                )
                resposta = input("Deseja continuar mesmo assim? (s/N): ")
                if resposta.lower() != 's':
                    self.stdout.write(self.style.ERROR("Operação cancelada"))
                    return
            
            # Enviar senha
            self.stdout.write("\n🔄 Enviando senha provisória...")
            
            service = EmailService()
            success = service.enviar_senha_provisoria(loja, owner)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Senha enviada com sucesso para {owner.email}"
                    )
                )
                
                # Verificar se foi atualizado no banco
                financeiro.refresh_from_db()
                self.stdout.write(f"Senha enviada (banco): {financeiro.senha_enviada}")
                self.stdout.write(f"Data envio: {financeiro.data_envio_senha}")
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n❌ Falha ao enviar senha para {owner.email}"
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        "Email registrado para retry automático (EmailRetry)"
                    )
                )
            
            self.stdout.write(f"\n{'='*80}\n")
            
        except Loja.DoesNotExist:
            raise CommandError(f"Loja '{loja_slug}' não encontrada")
        except Exception as e:
            raise CommandError(f"Erro ao enviar senha: {e}")
