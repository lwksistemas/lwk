"""
Comando para vincular oportunidades sem vendedor ao vendedor da loja.
"""
from django.core.management.base import BaseCommand
from crm_vendas.models import Oportunidade, Vendedor
from tenants.middleware import set_current_loja_id


class Command(BaseCommand):
    help = 'Vincula oportunidades sem vendedor ao vendedor especificado ou ao primeiro vendedor ativo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            required=True,
            help='ID da loja',
        )
        parser.add_argument(
            '--vendedor-id',
            type=int,
            required=False,
            help='ID do vendedor (opcional, usa o primeiro ativo se não especificado)',
        )

    def handle(self, *args, **options):
        loja_id = options['loja_id']
        vendedor_id = options.get('vendedor_id')
        
        set_current_loja_id(loja_id)

        # Buscar vendedor
        if vendedor_id:
            try:
                vendedor = Vendedor.objects.get(id=vendedor_id, is_active=True)
            except Vendedor.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Vendedor ID {vendedor_id} não encontrado ou inativo'))
                return
        else:
            vendedor = Vendedor.objects.filter(is_active=True).first()
        
        if not vendedor:
            self.stdout.write(self.style.ERROR(f'❌ Nenhum vendedor ativo encontrado na loja {loja_id}'))
            return

        # Buscar oportunidades sem vendedor
        oportunidades_sem_vendedor = Oportunidade.objects.filter(vendedor__isnull=True)
        total = oportunidades_sem_vendedor.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS(f'✅ Todas as oportunidades já têm vendedor vinculado'))
            return

        # Vincular ao vendedor
        oportunidades_sem_vendedor.update(vendedor=vendedor)

        self.stdout.write(self.style.SUCCESS(
            f'✅ {total} oportunidade(s) vinculada(s) ao vendedor: {vendedor.nome} (ID: {vendedor.id})'
        ))
        
        # Mostrar detalhes das oportunidades vinculadas
        for opp in Oportunidade.objects.filter(vendedor=vendedor):
            self.stdout.write(f'  - {opp.titulo} (R$ {opp.valor}) - Etapa: {opp.get_etapa_display()}')
