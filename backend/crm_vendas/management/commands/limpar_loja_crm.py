"""Comando para limpar TODOS os dados de uma loja CRM
Remove: Leads, Oportunidades, Atividades, Propostas, Contratos, etc.
"""
from django.core.management.base import BaseCommand
from django.db import transaction


def _contar_seguro(model):
    """Conta registros do model sem falhar se a tabela não existir."""
    try:
        return model.objects.count()
    except Exception:
        return 0


def _deletar_seguro(stdout, model, label):
    """Exclui todos os registros do model, retornando a contagem deletada."""
    try:
        count = model.objects.all().delete()[0]
        stdout.write(f"  ✅ {count} {label} excluído(s)")
        return count
    except Exception:
        stdout.write(f"  ⚠️  Tabela de {label} não existe (loja antiga)")
        return 0


class Command(BaseCommand):
    help = "Limpa todos os dados de uma loja CRM (CUIDADO: irreversível!)"

    def add_arguments(self, parser):
        parser.add_argument("loja_id", type=int, help="ID da loja")
        parser.add_argument(
            "--confirmar",
            action="store_true",
            help="Confirma a exclusão (obrigatório para executar)",
        )

    def handle(self, *args, **options):
        from crm_vendas.models import (
            AssinaturaDigital,
            Atividade,
            Conta,
            Contato,
            Contrato,
            ContratoTemplate,
            Lead,
            Oportunidade,
            OportunidadeItem,
            ProdutoServico,
            Proposta,
            PropostaTemplate,
        )
        from tenants.middleware import set_current_loja_id

        loja_id = options["loja_id"]
        confirmar = options.get("confirmar", False)

        # Configurar contexto da loja
        set_current_loja_id(loja_id)

        self.stdout.write(f"\n🏪 Loja ID: {loja_id}")
        self.stdout.write("=" * 60)

        modelos_contagem = [
            ("Assinaturas Digitais", AssinaturaDigital),
            ("Contratos", Contrato),
            ("Propostas", Proposta),
            ("Itens de Oportunidade", OportunidadeItem),
            ("Atividades", Atividade),
            ("Oportunidades", Oportunidade),
            ("Contatos", Contato),
            ("Leads", Lead),
            ("Contas", Conta),
            ("Produtos/Serviços", ProdutoServico),
            ("Templates de Proposta", PropostaTemplate),
            ("Templates de Contrato", ContratoTemplate),
        ]
        counts = {label: _contar_seguro(model) for label, model in modelos_contagem}

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

        if resposta != "SIM":
            self.stdout.write(self.style.WARNING("\n❌ Operação cancelada"))
            return

        # Executar limpeza
        self.stdout.write(self.style.WARNING("\n🗑️  Iniciando limpeza..."))

        try:
            with transaction.atomic():
                deleted_counts = {
                    label: _deletar_seguro(self.stdout, model, label)
                    for label, model in modelos_contagem
                }

                total_deleted = sum(deleted_counts.values())

                self.stdout.write(self.style.SUCCESS("\n✅ Limpeza concluída com sucesso!"))
                self.stdout.write(f"📊 Total de registros excluídos: {total_deleted}")

                # Verificar se está limpo
                self.stdout.write("\n🔍 Verificando limpeza...")
                verificacao = {
                    "Leads": Lead.objects.count(),
                    "Oportunidades": Oportunidade.objects.count(),
                    "Atividades": Atividade.objects.count(),
                    "Propostas": Proposta.objects.count(),
                    "Contratos": Contrato.objects.count(),
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
