"""
Comando para verificar e criar dados de teste no CRM da loja
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from superadmin.models import Loja
import dj_database_url
import os


class Command(BaseCommand):
    help = 'Verifica e cria dados de teste no CRM da loja'

    def add_arguments(self, parser):
        parser.add_argument('loja_id', type=int, help='ID da loja')

    def handle(self, *args, **options):
        loja_id = options['loja_id']
        
        try:
            loja = Loja.objects.get(id=loja_id)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Loja {loja_id} não encontrada'))
            return
        
        self.stdout.write(f"🏪 Loja: {loja.nome}")
        self.stdout.write(f"📊 Database: {loja.database_name}")
        
        # Configurar banco
        DATABASE_URL = os.environ.get('DATABASE_URL')
        schema_name = loja.database_name.replace('-', '_')
        default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=0)
        settings.DATABASES[loja.database_name] = {
            **default_db,
            'OPTIONS': {'options': f'-c search_path={schema_name},public'},
            'TIME_ZONE': None,
            'AUTOCOMMIT': True,
            'ATOMIC_REQUESTS': False,
            'CONN_MAX_AGE': 0,
        }
        
        conn = connections[loja.database_name]
        
        # Verificar dados existentes
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM crm_vendas_vendedor")
            vendedores = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM crm_vendas_conta")
            contas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM crm_vendas_lead")
            leads = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM crm_vendas_oportunidade")
            oportunidades = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM crm_vendas_atividade")
            atividades = cursor.fetchone()[0]
        
        self.stdout.write(f"\n📈 Dados atuais:")
        self.stdout.write(f"  Vendedores: {vendedores}")
        self.stdout.write(f"  Contas: {contas}")
        self.stdout.write(f"  Leads: {leads}")
        self.stdout.write(f"  Oportunidades: {oportunidades}")
        self.stdout.write(f"  Atividades: {atividades}")
        
        # Criar dados de teste se necessário
        if leads == 0:
            self.stdout.write(f"\n⚠️ Nenhum lead encontrado. Criando dados de teste...")
            with conn.cursor() as cursor:
                # Lead 1
                cursor.execute("""
                    INSERT INTO crm_vendas_lead 
                    (nome, empresa, email, telefone, origem, status, valor_estimado, loja_id, created_at, updated_at, observacoes)
                    VALUES 
                    ('João Silva', 'Tech Solutions LTDA', 'joao@techsolutions.com', '11987654321', 'site', 'novo', 50000.00, %s, NOW(), NOW(), 'Interessado em sistema de gestão')
                    RETURNING id
                """, [loja.id])
                lead1_id = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"  ✅ Lead 1 criado (ID: {lead1_id})"))
                
                # Lead 2
                cursor.execute("""
                    INSERT INTO crm_vendas_lead 
                    (nome, empresa, email, telefone, origem, status, valor_estimado, loja_id, created_at, updated_at, observacoes)
                    VALUES 
                    ('Maria Santos', 'Comercial ABC', 'maria@comercialabc.com', '11976543210', 'indicacao', 'contato', 35000.00, %s, NOW(), NOW(), 'Indicação de cliente atual')
                    RETURNING id
                """, [loja.id])
                lead2_id = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"  ✅ Lead 2 criado (ID: {lead2_id})"))
                
                # Lead 3
                cursor.execute("""
                    INSERT INTO crm_vendas_lead 
                    (nome, empresa, email, telefone, origem, status, valor_estimado, loja_id, created_at, updated_at, observacoes)
                    VALUES 
                    ('Pedro Costa', 'Distribuidora XYZ', 'pedro@distxyz.com', '11965432109', 'whatsapp', 'qualificado', 75000.00, %s, NOW(), NOW(), 'Contato via WhatsApp')
                    RETURNING id
                """, [loja.id])
                lead3_id = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"  ✅ Lead 3 criado (ID: {lead3_id})"))
        
        if atividades == 0:
            self.stdout.write(f"\n⚠️ Nenhuma atividade encontrada. Criando atividades de teste...")
            with conn.cursor() as cursor:
                # Pegar leads
                cursor.execute("SELECT id FROM crm_vendas_lead ORDER BY id LIMIT 3")
                lead_ids = [row[0] for row in cursor.fetchall()]
                
                if lead_ids:
                    # Atividade 1 - Hoje
                    cursor.execute("""
                        INSERT INTO crm_vendas_atividade 
                        (titulo, tipo, data, duracao_minutos, concluido, loja_id, lead_id, created_at, updated_at, observacoes)
                        VALUES 
                        ('Ligar para João Silva', 'call', NOW() + INTERVAL '2 hours', 30, false, %s, %s, NOW(), NOW(), 'Primeira ligação de contato')
                        RETURNING id
                    """, [loja.id, lead_ids[0]])
                    ativ1_id = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Atividade 1 criada (ID: {ativ1_id})"))
                    
                    # Atividade 2 - Amanhã
                    cursor.execute("""
                        INSERT INTO crm_vendas_atividade 
                        (titulo, tipo, data, duracao_minutos, concluido, loja_id, lead_id, created_at, updated_at, observacoes)
                        VALUES 
                        ('Reunião com Maria Santos', 'meeting', NOW() + INTERVAL '1 day', 60, false, %s, %s, NOW(), NOW(), 'Apresentação da proposta')
                        RETURNING id
                    """, [loja.id, lead_ids[1] if len(lead_ids) > 1 else lead_ids[0]])
                    ativ2_id = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Atividade 2 criada (ID: {ativ2_id})"))
                    
                    # Atividade 3 - Próxima semana
                    cursor.execute("""
                        INSERT INTO crm_vendas_atividade 
                        (titulo, tipo, data, duracao_minutos, concluido, loja_id, lead_id, created_at, updated_at, observacoes)
                        VALUES 
                        ('Enviar proposta para Pedro Costa', 'email', NOW() + INTERVAL '3 days', 15, false, %s, %s, NOW(), NOW(), 'Enviar proposta detalhada por email')
                        RETURNING id
                    """, [loja.id, lead_ids[2] if len(lead_ids) > 2 else lead_ids[0]])
                    ativ3_id = cursor.fetchone()[0]
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Atividade 3 criada (ID: {ativ3_id})"))
        
        # Verificar totais finais
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM crm_vendas_lead")
            leads_final = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM crm_vendas_atividade")
            atividades_final = cursor.fetchone()[0]
        
        self.stdout.write(f"\n✅ Totais finais:")
        self.stdout.write(f"  Leads: {leads_final}")
        self.stdout.write(f"  Atividades: {atividades_final}")
        
        # Limpar conexões
        if loja.database_name in connections:
            connections[loja.database_name].close()
        if loja.database_name in settings.DATABASES:
            del settings.DATABASES[loja.database_name]
        
        self.stdout.write(self.style.SUCCESS(f"\n🎉 Processo concluído!"))
        self.stdout.write(f"\n🌐 Acesse: https://lwksistemas.com.br/loja/{loja.slug}/crm-vendas/leads")
        self.stdout.write(f"🌐 Calendário: https://lwksistemas.com.br/loja/{loja.slug}/crm-vendas/calendario")
