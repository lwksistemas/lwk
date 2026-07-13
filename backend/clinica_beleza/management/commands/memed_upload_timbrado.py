"""
Salva o PDF timbrado da loja e aplica na Memed aos prescritores.

Uso:
    python manage.py memed_upload_timbrado --slug beleza --file "/caminho/Timbrado A4.pdf"
    python manage.py memed_upload_timbrado --slug beleza --file timbrado.pdf --aplicar
"""
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from clinica_beleza.memed_impressao import aplicar_timbrado_loja_a_profissionais
from clinica_beleza.models import MemedTimbrado, Professional
from core.db_config import ensure_loja_database_config
from superadmin.models import Loja
from tenants.middleware import set_current_loja_id, set_current_tenant_db


class Command(BaseCommand):
    help = 'Armazena o PDF timbrado da loja e aplica na Memed aos prescritores.'

    def add_arguments(self, parser):
        parser.add_argument('--slug', required=True, help='Slug, atalho ou CPF/CNPJ da loja.')
        parser.add_argument('--file', required=True, help='Caminho do PDF timbrado A4.')
        parser.add_argument(
            '--aplicar', action='store_true',
            help='Aplica imediatamente a todos os profissionais com CPF cadastrado.',
        )

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
        path = Path(options['file']).expanduser()
        if not path.is_file():
            raise CommandError(f'Arquivo não encontrado: {path}')
        if path.suffix.lower() != '.pdf':
            raise CommandError('Informe um arquivo .pdf')

        pdf_bytes = path.read_bytes()
        if len(pdf_bytes) < 100:
            raise CommandError('Arquivo PDF inválido ou vazio.')
        if len(pdf_bytes) > 5 * 1024 * 1024:
            raise CommandError('PDF muito grande (máx. 5 MB).')

        loja = self._resolver_loja(options['slug'])
        if not loja.database_name:
            raise CommandError(f'Loja {loja.slug} sem schema configurado.')
        ensure_loja_database_config(loja.database_name)
        set_current_loja_id(loja.id)
        set_current_tenant_db(loja.database_name)

        timbrado, _ = MemedTimbrado.objects.update_or_create(
            loja_id=loja.id,
            defaults={'pdf': pdf_bytes, 'pdf_nome': path.name},
        )
        self.stdout.write(self.style.SUCCESS(
            f'Timbrado salvo: {timbrado.pdf_nome} ({len(pdf_bytes)} bytes) — loja {loja.nome}'
        ))

        if not options.get('aplicar'):
            self.stdout.write('Use --aplicar para enviar à Memed agora.')
            return

        profs = [
            p for p in Professional.objects.filter(loja_id=loja.id, is_active=True)
            if len(re.sub(r'\D', '', p.cpf or '')) == 11
        ]
        if not profs:
            raise CommandError('Nenhum profissional ativo com CPF na loja.')

        resultado = aplicar_timbrado_loja_a_profissionais(pdf_bytes, path.name, profs)
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Aplicados: {resultado['aplicados']}/{resultado['total']}"
        ))
        for det in resultado.get('detalhes') or []:
            pid = det.get('professional_id')
            if det.get('ok'):
                self.stdout.write(self.style.SUCCESS(f'  OK prof {pid}'))
            else:
                self.stdout.write(self.style.WARNING(f'  prof {pid}: {det.get("error")} {det.get("detail", "")[:120]}'))
