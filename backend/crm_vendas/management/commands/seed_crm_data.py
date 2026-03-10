"""
Comando simplificado para criar dados de teste no CRM
Usa o ORM do Django diretamente (sem raw SQL)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Cria dados de teste no CRM usando ORM'

    def add_arguments(self, parser):
        parser.add_argument('loja_id', type=int, help='ID da loja')

    def handle(self, *args, **options):
        from crm_vendas.models import Lead, Atividade
        from tenants.middleware import set_current_loja_id
        
        loja_id = options['loja_id']
        
        # Configurar contexto da loja
        set_current_loja_id(loja_id)
        
        self.stdout.write(f"🏪 Criando dados para loja ID: {loja_id}")
        
        # Verificar dados existentes
        leads_count = Lead.objects.count()
        atividades_count = Atividade.objects.count()
        
        self.stdout.write(f"📊 Dados atuais: {leads_count} leads, {atividades_count} atividades")
        
        # Criar leads se não existirem
        if leads_count == 0:
            self.stdout.write("⚠️ Criando leads de teste...")
            
            lead1 = Lead.objects.create(
                nome='João Silva',
                empresa='Tech Solutions LTDA',
                email='joao@techsolutions.com',
                telefone='11987654321',
                origem='site',
                status='novo',
                valor_estimado=50000.00,
                observacoes='Interessado em sistema de gestão'
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ Lead criado: {lead1.nome}"))
            
            lead2 = Lead.objects.create(
                nome='Maria Santos',
                empresa='Comercial ABC',
                email='maria@comercialabc.com',
                telefone='11976543210',
                origem='indicacao',
                status='contato',
                valor_estimado=35000.00,
                observacoes='Indicação de cliente atual'
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ Lead criado: {lead2.nome}"))
            
            lead3 = Lead.objects.create(
                nome='Pedro Costa',
                empresa='Distribuidora XYZ',
                email='pedro@distxyz.com',
                telefone='11965432109',
                origem='whatsapp',
                status='qualificado',
                valor_estimado=75000.00,
                observacoes='Contato via WhatsApp'
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ Lead criado: {lead3.nome}"))
        
        # Criar atividades se não existirem
        if atividades_count == 0:
            self.stdout.write("⚠️ Criando atividades de teste...")
            
            leads = Lead.objects.all()[:3]
            
            if leads:
                # Atividade 1 - Hoje
                ativ1 = Atividade.objects.create(
                    titulo='Ligar para João Silva',
                    tipo='call',
                    data=timezone.now() + timedelta(hours=2),
                    duracao_minutos=30,
                    concluido=False,
                    lead=leads[0],
                    observacoes='Primeira ligação de contato'
                )
                self.stdout.write(self.style.SUCCESS(f"  ✅ Atividade criada: {ativ1.titulo}"))
                
                # Atividade 2 - Amanhã
                if len(leads) > 1:
                    ativ2 = Atividade.objects.create(
                        titulo='Reunião com Maria Santos',
                        tipo='meeting',
                        data=timezone.now() + timedelta(days=1),
                        duracao_minutos=60,
                        concluido=False,
                        lead=leads[1],
                        observacoes='Apresentação da proposta'
                    )
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Atividade criada: {ativ2.titulo}"))
                
                # Atividade 3 - Próxima semana
                if len(leads) > 2:
                    ativ3 = Atividade.objects.create(
                        titulo='Enviar proposta para Pedro Costa',
                        tipo='email',
                        data=timezone.now() + timedelta(days=3),
                        duracao_minutos=15,
                        concluido=False,
                        lead=leads[2],
                        observacoes='Enviar proposta detalhada por email'
                    )
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Atividade criada: {ativ3.titulo}"))
        
        # Totais finais
        leads_final = Lead.objects.count()
        atividades_final = Atividade.objects.count()
        
        self.stdout.write(f"\n✅ Totais finais:")
        self.stdout.write(f"  Leads: {leads_final}")
        self.stdout.write(f"  Atividades: {atividades_final}")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Processo concluído!"))
        self.stdout.write("🌐 Acesse: https://lwksistemas.com.br/loja/felix-representacoes-000172/crm-vendas/leads")
        self.stdout.write("🌐 Calendário: https://lwksistemas.com.br/loja/felix-representacoes-000172/crm-vendas/calendario")
