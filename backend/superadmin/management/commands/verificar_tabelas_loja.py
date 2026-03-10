from django.core.management.base import BaseCommand
from django.db import connections
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Verifica se as tabelas isoladas da loja foram criadas'

    def add_arguments(self, parser):
        parser.add_argument('loja_id', type=int, help='ID da loja para verificar')

    def handle(self, *args, **options):
        loja_id = options['loja_id']
        
        try:
            loja = Loja.objects.get(id=loja_id)
            self.stdout.write(f'\n🔍 Verificando loja: {loja.nome} (ID: {loja.id})')
            self.stdout.write(f'   Slug: {loja.slug}')
            self.stdout.write(f'   Tipo: {loja.tipo_loja.nome}')
            self.stdout.write(f'   Database: {loja.database_name}\n')
            
            # Verificar se o banco está configurado
            db_name = loja.database_name
            
            if db_name not in connections.databases:
                self.stdout.write(self.style.ERROR(f'❌ Banco "{db_name}" NÃO está configurado no Django'))
                self.stdout.write('\n⚠️ Sistema está usando banco único (Heroku Postgres)')
                self.stdout.write('   Todas as lojas compartilham o mesmo banco de dados')
                self.stdout.write('   Isolamento é feito por loja_id nas tabelas\n')
                
                # Verificar tabelas no banco principal
                self.verificar_tabelas_banco_unico(loja)
                return
            
            # Verificar tabelas no banco isolado
            self.verificar_tabelas_banco_isolado(loja, db_name)
            
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Loja com ID {loja_id} não encontrada'))
    
    def verificar_tabelas_banco_unico(self, loja):
        """Verifica tabelas no banco único (Heroku Postgres)"""
        from django.db import connection
        
        self.stdout.write('📊 Verificando tabelas no banco principal...\n')
        
        # Tabelas do CRM Vendas
        tabelas_crm = [
            'crm_vendas_lead',
            'crm_vendas_oportunidade',
            'crm_vendas_conta',
            'crm_vendas_atividade',
            'crm_vendas_produto',
            'crm_vendas_proposta',
        ]
        
        # Tabelas da Clínica de Estética
        tabelas_clinica = [
            'clinica_estetica_cliente',
            'clinica_estetica_profissional',
            'clinica_estetica_agendamento',
            'clinica_estetica_procedimento',
        ]
        
        # Tabelas da Clínica da Beleza
        tabelas_beleza = [
            'clinica_beleza_patient',
            'clinica_beleza_professional',
            'clinica_beleza_appointment',
            'clinica_beleza_service',
        ]
        
        todas_tabelas = tabelas_crm + tabelas_clinica + tabelas_beleza
        
        with connection.cursor() as cursor:
            for tabela in todas_tabelas:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    );
                """, [tabela])
                
                existe = cursor.fetchone()[0]
                
                if existe:
                    # Contar registros da loja
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {tabela} WHERE loja_id = %s", [loja.id])
                        count = cursor.fetchone()[0]
                        self.stdout.write(self.style.SUCCESS(f'  ✅ {tabela}: {count} registro(s)'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  ⚠️ {tabela}: existe mas erro ao contar ({str(e)[:50]})'))
                else:
                    self.stdout.write(self.style.ERROR(f'  ❌ {tabela}: NÃO EXISTE'))
        
        self.stdout.write('\n✅ Verificação concluída!')
    
    def verificar_tabelas_banco_isolado(self, loja, db_name):
        """Verifica tabelas no banco isolado (SQLite)"""
        from django.db import connections
        
        self.stdout.write(f'📊 Verificando tabelas no banco isolado "{db_name}"...\n')
        
        connection = connections[db_name]
        
        with connection.cursor() as cursor:
            # Listar todas as tabelas
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
            """)
            
            tabelas = cursor.fetchall()
            
            if not tabelas:
                self.stdout.write(self.style.ERROR('❌ Nenhuma tabela encontrada no banco isolado'))
                return
            
            self.stdout.write(f'✅ {len(tabelas)} tabela(s) encontrada(s):\n')
            
            for (tabela,) in tabelas:
                # Contar registros
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cursor.fetchone()[0]
                self.stdout.write(f'  • {tabela}: {count} registro(s)')
        
        self.stdout.write('\n✅ Verificação concluída!')
