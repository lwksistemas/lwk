"""
Vincular owner da loja ao cadastro de profissionais (Clínica da Beleza).

Use quando uma loja Clínica da Beleza foi criada mas o admin não apareceu
em Profissionais. Cria Professional no schema da loja e ProfissionalUsuario
com perfil Administrador.

Uso:
  python manage.py vincular_owner_profissional_clinica_beleza
  python manage.py vincular_owner_profissional_clinica_beleza --slug linda-1845
"""
import os
import django
from django.core.management.base import BaseCommand
from django.conf import settings
from superadmin.models import Loja, ProfissionalUsuario

class Command(BaseCommand):
    help = 'Vincula o owner da loja ao cadastro de profissionais (Clínica da Beleza)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            default=None,
            help='Slug da loja (ex: linda-1845). Se não informado, processa todas as Clínica da Beleza.',
        )

    def _ensure_database_in_settings(self, loja):
        from core.db_config import ensure_loja_database_config
        db_name = loja.database_name
        if not db_name:
            return False
        if not ensure_loja_database_config(db_name, conn_max_age=600):
            self.stdout.write(self.style.ERROR('   DATABASE_URL não definido ou banco não configurado'))
            return False
        return True

    def handle(self, *args, **options):
        slug = options.get('slug')
        self.stdout.write(self.style.SUCCESS('Vincular owner → Profissionais (Clínica da Beleza)'))

        if slug:
            lojas = Loja.objects.filter(slug=slug, is_active=True).select_related('tipo_loja', 'owner')
            if not lojas.exists():
                self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada.'))
                return
        else:
            lojas = Loja.objects.filter(
                is_active=True,
                tipo_loja__nome='Clínica da Beleza',
                database_created=True,
            ).select_related('tipo_loja', 'owner')

        for loja in lojas:
            if loja.tipo_loja.nome != 'Clínica da Beleza':
                self.stdout.write(self.style.WARNING(f'   Loja {loja.slug} não é Clínica da Beleza, pulando.'))
                continue
            if not loja.database_created or not loja.database_name:
                self.stdout.write(self.style.WARNING(f'   Loja {loja.slug}: schema não criado. Rode setup_loja_schema primeiro.'))
                continue

            self.stdout.write(f'\nLoja: {loja.nome} (slug={loja.slug})')
            owner = loja.owner
            if ProfissionalUsuario.objects.filter(loja=loja, user=owner).exists():
                self.stdout.write(self.style.WARNING('   Owner já vinculado como profissional.'))
                continue

            if not self._ensure_database_in_settings(loja):
                continue

            # Garantir que o schema tem as migrations (ex.: loja_id) aplicadas
            try:
                from django.core.management import call_command
                for app in ['stores', 'products', 'clinica_beleza']:
                    call_command('migrate', app, '--database', loja.database_name, verbosity=0)
            except Exception as e_mig:
                self.stdout.write(self.style.WARNING(f'   Migrations: {e_mig}'))

            try:
                from clinica_beleza.models import Professional
                owner_name = (owner.get_full_name() or owner.username or '').strip() or owner.username
                owner_phone = (getattr(loja, 'owner_telefone', None) or '').strip()
                try:
                    prof = Professional.objects.using(loja.database_name).create(
                        name=owner_name,
                        email=owner.email or '',
                        phone=owner_phone,
                        specialty='Administrador',
                        active=True,
                        loja_id=loja.id,
                    )
                except Exception as e_create:
                    if 'loja_id' in str(e_create) and 'does not exist' in str(e_create):
                        # Schema antigo sem coluna loja_id: adicionar via SQL no schema da loja
                        from django.db import connections
                        conn = connections[loja.database_name]
                        with conn.cursor() as cursor:
                            cursor.execute(
                                'ALTER TABLE clinica_beleza_professional '
                                'ADD COLUMN IF NOT EXISTS loja_id INTEGER NOT NULL DEFAULT 0'
                            )
                            cursor.execute(
                                'CREATE INDEX IF NOT EXISTS clinica_bel_loja_id_prof_idx '
                                'ON clinica_beleza_professional (loja_id)'
                            )
                        prof = Professional.objects.using(loja.database_name).create(
                            name=owner_name,
                            email=owner.email or '',
                            phone=owner_phone,
                            specialty='Administrador',
                            active=True,
                            loja_id=loja.id,
                        )
                    else:
                        raise
                ProfissionalUsuario.objects.create(
                    user=owner,
                    loja=loja,
                    professional_id=prof.id,
                    perfil=ProfissionalUsuario.PERFIL_ADMINISTRADOR,
                    precisa_trocar_senha=False,
                )
                self.stdout.write(self.style.SUCCESS(f'   Profissional criado e vinculado (perfil Administrador) para {owner.email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Erro: {e}'))
                import traceback
                traceback.print_exc()

        self.stdout.write('')
