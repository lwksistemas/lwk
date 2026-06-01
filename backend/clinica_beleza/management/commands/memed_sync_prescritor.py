"""
Sincroniza (cria/atualiza) um prescritor na Memed a partir do cadastro de um
profissional de uma loja. Útil para testar o auto-cadastro e confirmar com o
suporte da Memed o formato do endpoint de criação de prescritor.

Uso:
    python manage.py memed_sync_prescritor --slug beleza --professional 4 --force
    python manage.py memed_sync_prescritor --slug beleza --cpf 12345678901 --force

--force ignora a flag MEMED_AUTO_CADASTRO (envia mesmo com ela desligada).
"""
import re

from django.core.management.base import BaseCommand, CommandError

from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db

from clinica_beleza.models import Professional
from clinica_beleza.memed_service import sincronizar_prescritor, external_id_prescritor


class Command(BaseCommand):
    help = 'Cria/atualiza um prescritor na Memed a partir do cadastro do profissional.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', required=True, help='Slug, atalho ou CPF/CNPJ da loja.')
        parser.add_argument('--professional', type=int, help='ID do profissional na loja.')
        parser.add_argument('--cpf', help='CPF do profissional (alternativa ao --professional).')
        parser.add_argument('--force', action='store_true', help='Ignora a flag MEMED_AUTO_CADASTRO.')

    def _resolver_loja(self, ident: str) -> Loja:
        ident = (ident or '').strip()
        loja = (
            Loja.objects.using('default').filter(slug__iexact=ident).first()
            or Loja.objects.using('default').filter(atalho__iexact=ident).first()
        )
        if not loja:
            so_digitos = ''.join(c for c in ident if c.isdigit())
            if so_digitos:
                loja = Loja.objects.using('default').filter(cpf_cnpj=so_digitos).first()
        if not loja:
            raise CommandError(f'Loja não encontrada para "{ident}".')
        return loja

    def handle(self, *args, **options):
        loja = self._resolver_loja(options['slug'])
        if not loja.database_name:
            raise CommandError(f'Loja {loja.slug} não tem schema configurado.')
        ensure_loja_database_config(loja.database_name)
        set_current_loja_id(loja.id)
        set_current_tenant_db(loja.database_name)

        qs = Professional.objects.using(loja.database_name).filter(loja_id=loja.id)
        if options.get('professional'):
            prof = qs.filter(pk=options['professional']).first()
        elif options.get('cpf'):
            cpf = re.sub(r'\D', '', options['cpf'])
            prof = next((p for p in qs if re.sub(r'\D', '', p.cpf or '') == cpf), None)
        else:
            raise CommandError('Informe --professional <id> ou --cpf <cpf>.')

        if not prof:
            raise CommandError('Profissional não encontrado na loja informada.')

        self.stdout.write(f'Profissional: {prof.nome} (id={prof.id}) — external_id={external_id_prescritor(prof)}')
        resultado = sincronizar_prescritor(prof, force=options.get('force', False))
        self.stdout.write(self.style.MIGRATE_HEADING('=== Resultado ==='))
        self.stdout.write(str(resultado))
        if resultado.get('ok'):
            self.stdout.write(self.style.SUCCESS('Prescritor sincronizado com a Memed.'))
        elif resultado.get('skipped'):
            self.stdout.write(self.style.WARNING(f"Ignorado: {resultado['skipped']} (use --force se necessário)."))
        else:
            self.stdout.write(self.style.ERROR('Falha ao sincronizar — veja o detalhe acima.'))
