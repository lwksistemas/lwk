"""
Comando para listar lojas de clínica com cadastros
"""
from django.core.management.base import BaseCommand
from superadmin.models import Loja
from clinica_estetica.models import Cliente, Procedimento, Agendamento


class Command(BaseCommand):
    help = 'Lista lojas de clínica de estética que têm cadastros'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*100)
        self.stdout.write('🔍 CLÍNICAS DE ESTÉTICA - LOJAS COM CADASTROS')
        self.stdout.write('='*100 + '\n')

        lojas_clinica = Loja.objects.filter(
            tipo_loja__nome='Clínica de Estética', 
            is_active=True
        ).order_by('created_at')
        
        self.stdout.write(f'Total de clínicas ativas: {lojas_clinica.count()}\n')

        lojas_com_dados = []
        for loja in lojas_clinica:
            db_name = loja.database_name
            try:
                clientes = Cliente.objects.using(db_name).count()
                procedimentos = Procedimento.objects.using(db_name).count()
                agendamentos = Agendamento.objects.using(db_name).count()
                
                total = clientes + procedimentos + agendamentos
                if total > 0:
                    lojas_com_dados.append((loja, clientes, procedimentos, agendamentos))
            except Exception as e:
                self.stdout.write(f'Erro ao acessar {loja.nome}: {e}')

        if lojas_com_dados:
            self.stdout.write('LOJAS COM CADASTROS:')
            self.stdout.write('-' * 100)
            for i, (loja, clientes, proc, agend) in enumerate(lojas_com_dados, 1):
                self.stdout.write(f'\n{i}. {loja.nome} (ID: {loja.id})')
                self.stdout.write(f'   Slug: {loja.slug}')
                self.stdout.write(f'   Database: {loja.database_name}')
                self.stdout.write(f'   Criada em: {loja.created_at}')
                self.stdout.write(f'   Dados: {clientes} clientes, {proc} procedimentos, {agend} agendamentos')
                if i == 1:
                    self.stdout.write(self.style.WARNING('   ⚠️  PROVÁVEL LOJA MODELO (mais antiga com dados)'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Nenhuma loja com cadastros encontrada'))

        self.stdout.write('\n' + '='*100)
