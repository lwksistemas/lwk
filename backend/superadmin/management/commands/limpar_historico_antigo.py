"""Remove o histórico de acessos vencido.

Uso:
    python manage.py limpar_historico_antigo

O padrão apaga o restante com mais de 90 dias e a leitura (visualizar) com mais de 180 dias.
"""
from django.core.management.base import BaseCommand

from superadmin.historico_limpeza import limpar_historico_acesso


class Command(BaseCommand):
    help = "Remove o histórico de acessos vencido, com prazo maior para a leitura"

    def handle(self, *args, **options):
        resultado = limpar_historico_acesso()
        self.stdout.write(self.style.SUCCESS(
            "Histórico apagado: "
            f"{resultado['operacao']} operação, {resultado['leitura']} leitura."
        ))
