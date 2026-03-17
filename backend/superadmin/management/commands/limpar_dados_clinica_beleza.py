"""
Limpa dados de teste da Clínica da Beleza no schema de uma loja.

Uso:
  python manage.py limpar_dados_clinica_beleza --slug clinica-luiz-000172
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from superadmin.models import Loja

class Command(BaseCommand):
    help = 'Limpa pacientes, profissionais, procedimentos, agendamentos e pagamentos da loja (Clínica da Beleza)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            required=True,
            help='Slug da loja (ex: clinica-luiz-000172)',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Não pedir confirmação',
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
        slug = options['slug'].strip()
        no_input = options.get('no_input', False)

        loja = Loja.objects.filter(slug=slug, is_active=True).select_related('tipo_loja').first()
        if not loja:
            self.stdout.write(self.style.ERROR(f'Loja com slug "{slug}" não encontrada.'))
            return
        if loja.tipo_loja.nome != 'Clínica da Beleza':
            self.stdout.write(self.style.ERROR(f'Loja "{slug}" não é do tipo Clínica da Beleza.'))
            return
        if not loja.database_created or not loja.database_name:
            self.stdout.write(self.style.ERROR(f'Schema da loja não está criado. Rode o setup da loja primeiro.'))
            return

        if not no_input:
            confirm = input(f'Limpar TODOS os dados da loja "{loja.nome}" (slug={slug})? [y/N]: ')
            if (confirm or 'n').lower() != 'y':
                self.stdout.write('Cancelado.')
                return

        if not self._ensure_database_in_settings(loja):
            return

        from clinica_beleza.models import Payment, Appointment, Patient, Professional, Procedure
        db_name = loja.database_name

        self.stdout.write('Limpando dados da Clínica da Beleza...')

        n_pay, _ = Payment.objects.using(db_name).all().delete()
        self.stdout.write(self.style.SUCCESS(f'   {n_pay} pagamento(s) removido(s)'))

        n_app, _ = Appointment.objects.using(db_name).all().delete()
        self.stdout.write(self.style.SUCCESS(f'   {n_app} agendamento(s) removido(s)'))

        n_pat, _ = Patient.objects.using(db_name).all().delete()
        self.stdout.write(self.style.SUCCESS(f'   {n_pat} paciente(s) removido(s)'))

        n_prof, _ = Professional.objects.using(db_name).all().delete()
        self.stdout.write(self.style.SUCCESS(f'   {n_prof} profissional(is) removido(s)'))

        n_proc, _ = Procedure.objects.using(db_name).all().delete()
        self.stdout.write(self.style.SUCCESS(f'   {n_proc} procedimento(s) removido(s)'))

        self.stdout.write(self.style.SUCCESS('\nBanco da loja limpo.'))
