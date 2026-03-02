"""
Comando para criar funcionários para administradores de lojas existentes

⚠️ ATENÇÃO: Este comando é apenas para CORREÇÃO de dados antigos!

Lojas novas já têm funcionários criados automaticamente pelo signal em:
backend/superadmin/signals.py -> create_funcionario_for_loja_owner()

Use este comando apenas se:
1. Você tem lojas antigas criadas antes do signal ser implementado
2. Houve algum erro na criação automática e precisa recriar

Uso:
    python manage.py criar_funcionarios_admins
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from superadmin.models import Loja


def _db_alias_for_loja(loja):
    """Retorna o alias do banco da loja (schema isolado) ou 'default' se não houver."""
    db_name = getattr(loja, 'database_name', None)
    if not db_name:
        return 'default'
    if db_name in settings.DATABASES:
        return db_name
    try:
        import dj_database_url
        database_url = os.environ.get('DATABASE_URL', '')
        if 'postgres' not in database_url.lower():
            return 'default'
        default_db = dj_database_url.config(default=database_url, conn_max_age=0)
        schema_name = db_name.replace('-', '_')
        settings.DATABASES[db_name] = {
            **default_db,
            'OPTIONS': {'options': f'-c search_path={schema_name},public'},
            'CONN_MAX_AGE': 0,
        }
        return db_name
    except Exception:
        return 'default'


class Command(BaseCommand):
    help = 'Cria funcionários para administradores de lojas existentes que ainda não têm'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando criação de funcionários para administradores...'))
        
        lojas = Loja.objects.all()
        total_lojas = lojas.count()
        criados = 0
        ja_existentes = 0
        erros = 0
        
        for loja in lojas:
            try:
                tipo_loja_nome = loja.tipo_loja.nome
                owner = loja.owner
                db_alias = _db_alias_for_loja(loja)
                
                self.stdout.write(f'\n📋 Processando loja: {loja.nome} ({tipo_loja_nome})')
                self.stdout.write(f'   Owner: {owner.username} ({owner.email})')
                
                # Dados básicos do funcionário
                funcionario_data = {
                    'nome': owner.get_full_name() or owner.username,
                    'email': owner.email,
                    'telefone': '',
                    'cargo': 'Administrador',
                    'is_admin': True,
                    'loja_id': loja.id
                }
                
                funcionario_criado = False
                
                # Criar funcionário baseado no tipo de app (no schema da loja quando db_alias != default)
                if tipo_loja_nome == 'Clínica de Estética':
                    from clinica_estetica.models import Funcionario
                    from django.db import connections
                    
                    conn = connections[db_alias]
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM clinica_funcionarios WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Funcionário já existe'))
                    else:
                        func = Funcionario(**funcionario_data)
                        func.save(using=db_alias)
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'Serviços':
                    from servicos.models import Funcionario
                    from django.db import connections
                    
                    conn = connections[db_alias]
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM servicos_funcionarios WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Funcionário já existe'))
                    else:
                        func = Funcionario(**funcionario_data)
                        func.save(using=db_alias)
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'Restaurante':
                    from restaurante.models import Funcionario
                    from django.db import connections
                    
                    conn = connections[db_alias]
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM restaurante_funcionarios WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Funcionário já existe'))
                    else:
                        funcionario_data['cargo'] = 'Gerente'
                        func = Funcionario(**funcionario_data)
                        func.save(using=db_alias)
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'CRM Vendas':
                    from crm_vendas.models import Vendedor
                    from django.db import connections
                    
                    conn = connections[db_alias]
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM crm_vendedores WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Vendedor já existe'))
                    else:
                        funcionario_data['cargo'] = 'Gerente de Vendas'
                        funcionario_data['meta_mensal'] = 10000.00
                        func = Vendedor(**funcionario_data)
                        func.save(using=db_alias)
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'E-commerce':
                    self.stdout.write(self.style.WARNING(f'   ⚠️ E-commerce não possui modelo de funcionário'))
                    continue
                    
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ Tipo de app não reconhecido: {tipo_loja_nome}'))
                    continue
                
                if funcionario_criado:
                    criados += 1
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Funcionário criado com sucesso!'))
                    
            except Exception as e:
                erros += 1
                self.stdout.write(self.style.ERROR(f'   ❌ Erro ao processar loja {loja.nome}: {e}'))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))
        
        # Resumo final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Processamento concluído!'))
        self.stdout.write(f'📊 Total de lojas processadas: {total_lojas}')
        self.stdout.write(self.style.SUCCESS(f'✅ Funcionários criados: {criados}'))
        self.stdout.write(self.style.WARNING(f'⚠️ Já existentes: {ja_existentes}'))
        if erros > 0:
            self.stdout.write(self.style.ERROR(f'❌ Erros: {erros}'))
        self.stdout.write('='*60)
