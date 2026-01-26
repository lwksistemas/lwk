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
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from superadmin.models import Loja


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
                
                # Criar funcionário baseado no tipo de loja
                if tipo_loja_nome == 'Clínica de Estética':
                    from clinica_estetica.models import Funcionario
                    from django.db import connection
                    
                    # Verificar diretamente no banco (bypass do manager)
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM clinica_funcionarios WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Funcionário já existe'))
                    else:
                        # Criar diretamente no banco
                        func = Funcionario(**funcionario_data)
                        func.save(using='default')
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'Serviços':
                    from servicos.models import Funcionario
                    from django.db import connection
                    
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM servicos_funcionarios WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Funcionário já existe'))
                    else:
                        func = Funcionario(**funcionario_data)
                        func.save(using='default')
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'Restaurante':
                    from restaurante.models import Funcionario
                    from django.db import connection
                    
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM restaurante_funcionarios WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Funcionário já existe'))
                    else:
                        funcionario_data['cargo'] = 'Gerente'
                        func = Funcionario(**funcionario_data)
                        func.save(using='default')
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'CRM Vendas':
                    from crm_vendas.models import Vendedor
                    from django.db import connection
                    
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT COUNT(*) FROM crm_vendedores WHERE email = %s AND loja_id = %s", [owner.email, loja.id])
                        count = cursor.fetchone()[0]
                    
                    if count > 0:
                        ja_existentes += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠️ Vendedor já existe'))
                    else:
                        funcionario_data['cargo'] = 'Gerente de Vendas'
                        funcionario_data['meta_mensal'] = 10000.00
                        func = Vendedor(**funcionario_data)
                        func.save(using='default')
                        funcionario_criado = True
                        
                elif tipo_loja_nome == 'E-commerce':
                    self.stdout.write(self.style.WARNING(f'   ⚠️ E-commerce não possui modelo de funcionário'))
                    continue
                    
                else:
                    self.stdout.write(self.style.WARNING(f'   ⚠️ Tipo de loja não reconhecido: {tipo_loja_nome}'))
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
