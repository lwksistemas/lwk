"""
Diagnóstico das credenciais da Memed (homologação e/ou produção).

Testa a api-key/secret-key fazendo uma chamada real à API da Memed e relata se
as chaves são válidas e se o prescritor informado é encontrado. Útil para validar
as credenciais assim que forem cadastradas, sem depender da interface.

Uso:
    python manage.py memed_check
    python manage.py memed_check --env production
    python manage.py memed_check --prescritor 12345SP
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from clinica_beleza.memed_config import MEMED_ENDPOINTS
from clinica_beleza.memed_config import memed_credentials as _memed_credentials

PLACEHOLDER_MARK = 'COLE_AQUI'


class Command(BaseCommand):
    help = 'Testa as credenciais da Memed (homologação/produção) contra a API.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--env', choices=['integration', 'production', 'both'], default='both',
            help='Ambiente a testar (padrão: both).',
        )
        parser.add_argument(
            '--prescritor', type=str, default='',
            help='Identificador do prescritor (CPF, external_id ou registro+UF, ex.: 12345SP).',
        )

    def handle(self, *args, **options):
        env_opt = options['env']
        prescritor_cli = (options.get('prescritor') or '').strip()
        ambientes = ['integration', 'production'] if env_opt == 'both' else [env_opt]

        for env in ambientes:
            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING(f'== Ambiente: {env} =='))
            self._check_env(env, prescritor_cli)

    def _check_env(self, env, prescritor_cli):
        endpoints = MEMED_ENDPOINTS[env]
        api_key, secret_key = _memed_credentials(env)

        if not api_key or not secret_key:
            self.stdout.write(self.style.WARNING('Chaves ausentes (api-key/secret-key não configuradas).'))
            return
        if PLACEHOLDER_MARK in api_key or PLACEHOLDER_MARK in secret_key:
            self.stdout.write(self.style.WARNING('Chaves ainda são placeholders — substitua pelos valores reais.'))
            return

        prescritor = prescritor_cli
        if not prescritor:
            if env == 'production':
                prescritor = getattr(settings, 'MEMED_PRESCRITOR_ID_PROD', '') or ''
            prescritor = prescritor or getattr(settings, 'MEMED_PRESCRITOR_ID', '') or ''
        prescritor = (prescritor or '').strip()
        if not prescritor:
            self.stdout.write(self.style.WARNING(
                'Sem prescritor para testar. Informe --prescritor ou configure MEMED_PRESCRITOR_ID.'
            ))
            return

        url = f"{endpoints['api']}/sinapse-prescricao/usuarios/{prescritor}"
        self.stdout.write(f'Chaves: {self._mask(api_key)} / {self._mask(secret_key)}')
        self.stdout.write(f'Testando prescritor "{prescritor}"...')
        try:
            resp = requests.get(
                url,
                params={'api-key': api_key, 'secret-key': secret_key},
                headers={
                    'Accept': 'application/vnd.api+json',
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                },
                timeout=30,
            )
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'FALHA de conexão: {e}'))
            return

        if resp.status_code in (401, 403):
            self.stdout.write(self.style.ERROR(f'Chaves inválidas (HTTP {resp.status_code}).'))
            return
        if resp.status_code == 404:
            self.stdout.write(self.style.WARNING(
                f'Chaves OK, mas prescritor "{prescritor}" não existe na Memed (HTTP 404). '
                'Cadastre o prescritor neste ambiente.'
            ))
            return
        if not resp.ok:
            self.stdout.write(self.style.ERROR(f'Resposta inesperada (HTTP {resp.status_code}): {resp.text[:300]}'))
            return

        attrs = ((resp.json() or {}).get('data') or {}).get('attributes') or {}
        token = attrs.get('token')
        nome = (f"{attrs.get('nome', '')} {attrs.get('sobrenome', '')}").strip()
        if token:
            self.stdout.write(self.style.SUCCESS(
                f'OK! Credenciais válidas e prescritor encontrado: {nome or prescritor} '
                f'(CRM {attrs.get("crm", "?")}/{attrs.get("uf", "?")}). Token recebido.'
            ))
        else:
            self.stdout.write(self.style.WARNING('Chaves OK, mas a Memed não retornou token para esse prescritor.'))

    @staticmethod
    def _mask(value: str) -> str:
        if not value:
            return '(vazio)'
        return f'{value[:4]}…{value[-4:]}' if len(value) > 10 else '****'
