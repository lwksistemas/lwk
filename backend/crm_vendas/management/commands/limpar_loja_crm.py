"""
Comando para limpar TODOS os dados de uma loja CRM
Remove: Leads, Oportunidades, Atividades, Propostas, Contratos, etc.
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Limpa todos os dados de uma loja CRM (CUIDADO: irreversível!)'

    def add_arguments(self, parser):
        parser.add_argument('loja_id', type=int, help='ID da loja')
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a exclusão (obrigatório para executar)'
        )

    def handle(self, *args, **options):
        from crm_vendas.models import (
            Lead, Conta, Contato, Oportunidade, Atividade,
            ProdutoServico, OportunidadeItem, Proposta, Contrato,
            AssinaturaDigital, PropostaTemplate, ContratoTemplate
        )
        from tenants.middleware import set_current_loja_id
        
        loja_id = options['loja_id']
        confirmar = options.get('confirmar', False)
        
        # Configurar contexto da loja
        set_current_loja_id(loja_id)
        
        self.stdout.write(f"\n🏪 Loja ID: {loja_id}")
        self.stdout.write("=" * 60)
        
        # Contar dados existentes
        counts = {
            'Assinaturas Digitais': AssinaturaDigital.objects.count(),
            'Contratos': Contrato.objects.count(),
            'Propostas': Proposta.objects.count(),
            'Itens de Oportunidade': OportunidadeItem.objects.count(),
            'Atividades': Atividade.objects.count(),
            'Oportunidades': Oportunidade.objects.count(),
            'Contatos': Contato.objects.count(),
            'Leads': Lead.objects.count(),
            'Contas': Conta.objects.count(),
            'Produtos/Serviços': ProdutoServico.objects.count(),
            'Templates de Proposta': PropostaTemplate.objects.count(),
            'Templates de Contrato': ContratoTemplate.objects.count(),
        }
        
        self.stdout.write("\n📊 Dados atuais:")
        total = 0
        for nome, count in counts.items():
            if count > 0:
                self.stdout.write(f"  • {nome}: {count}")
                total += count
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("\n✅ Loja já está limpa (sem dados)"))
            return
        
        self.stdout.write(f"\n📈 Total de registros: {total}")
        
        if not confirmar:
            self.stdout.write(self.style.WARNING("\n⚠️  ATENÇÃO: Esta operação é IRREVERSÍVEL!"))
            self.stdout.write(self.style.WARNING("⚠️  Todos os dados acima serão PERMANENTEMENTE excluídos."))
            self.stdout.write("\n❌ Operação cancelada (use --confirmar para executar)")
            self.stdout.write("\nExemplo:")
            self.stdout.write(f"  python manage.py limpar_loja_crm {loja_id} --confirmar")
            return
        
        # Confirmar novamente
        self.stdout.write(self.style.ERROR("\n🚨 ÚLTIMA CONFIRMAÇÃO 🚨"))
        self.stdout.write(self.style.ERROR(f"Você está prestes a EXCLUIR {total} registros da loja {loja_id}"))
        resposta = input("\nDigite 'SIM' (em maiúsculas) para confirmar: ")
        
        if resposta != 'SIM':
            self.stdout.write(self.style.WARNING("\n❌ Operação cancelada"))
            return
        
        # Executar limpeza
        self.stdout.write(self.style.WARNING("\n🗑️  Iniciando limpeza..."))
        
        try:
            with transaction.atomic():
                # Ordem de exclusão (respeitar FKs)
                deleted_counts = {}
                
                # 1. Assinaturas digitais (FK para Proposta/Contrato)
                count = AssinaturaDigital.objects.all().delete()[0]
                deleted_counts['Assinaturas Digitais'] = count
                self.stdout.write(f"  ✅ {count} assinaturas digitais excluídas")
                
                # 2. Contratos
                count = Contrato.objects.all().delete()[0]
                deleted_counts['Contratos'] = count
                self.stdout.write(f"  ✅ {count} contratos excluídos")
                
                # 3. Propostas
                count = Proposta.objects.all().delete()[0]
                deleted_counts['Propostas'] = count
                self.stdout.write(f"  ✅ {count} propostas excluídas")
                
                # 4. Itens de Oportunidade
                count = OportunidadeItem.objects.all().delete()[0]
                deleted_counts['Itens de Oportunidade'] = count
                self.stdout.write(f"  ✅ {count} itens de oportunidade excluídos")
                
                # 5. Atividades
                count = Atividade.objects.all().delete()[0]
                deleted_counts['Atividades'] = count
                self.stdout.write(f"  ✅ {count} atividades excluídas")
                
                # 6. Oportunidades
                count = Oportunidade.objects.all().delete()[0]
                deleted_counts['Oportunidades'] = count
                self.stdout.write(f"  ✅ {count} oportunidades excluídas")
                
                # 7. Contatos
                count = Contato.objects.all().delete()[0]
                deleted_counts['Contatos'] = count
                self.stdout.write(f"  ✅ {count} contatos excluídos")
                
                # 8. Leads
                count = Lead.objects.all().delete()[0]
                deleted_counts['Leads'] = count
                self.stdout.write(f"  ✅ {count} leads excluídos")
                
                # 9. Contas
                count = Conta.objects.all().delete()[0]
                deleted_counts['Contas'] = count
                self.stdout.write(f"  ✅ {count} contas excluídas")
                
                # 10. Produtos/Serviços
                count = ProdutoServico.objects.all().delete()[0]
                deleted_counts['Produtos/Serviços'] = count
                self.stdout.write(f"  ✅ {count} produtos/serviços excluídos")
                
                # 11. Templates de Proposta
                count = PropostaTemplate.objects.all().delete()[0]
                deleted_counts['Templates de Proposta'] = count
                self.stdout.write(f"  ✅ {count} templates de proposta excluídos")
                
                # 12. Templates de Contrato
                count = ContratoTemplate.objects.all().delete()[0]
                deleted_counts['Templates de Contrato'] = count
                self.stdout.write(f"  ✅ {count} templates de contrato excluídos")
                
                total_deleted = sum(deleted_counts.values())
                
                self.stdout.write(self.style.SUCCESS(f"\n✅ Limpeza concluída com sucesso!"))
                self.stdout.write(f"📊 Total de registros excluídos: {total_deleted}")
                
                # Verificar se está limpo
                self.stdout.write("\n🔍 Verificando limpeza...")
                verificacao = {
                    'Leads': Lead.objects.count(),
                    'Oportunidades': Oportunidade.objects.count(),
                    'Atividades': Atividade.objects.count(),
                    'Propostas': Proposta.objects.count(),
                    'Contratos': Contrato.objects.count(),
                }
                
                tudo_limpo = all(count == 0 for count in verificacao.values())
                
                if tudo_limpo:
                    self.stdout.write(self.style.SUCCESS("✅ Loja completamente limpa!"))
                else:
                    self.stdout.write(self.style.WARNING("⚠️  Alguns dados ainda existem:"))
                    for nome, count in verificacao.items():
                        if count > 0:
                            self.stdout.write(f"  • {nome}: {count}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Erro durante a limpeza: {e}"))
            raise
