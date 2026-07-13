"""Custom Managers para CRM Vendas.
"""
import logging

from core.mixins import LojaIsolationManager

logger = logging.getLogger(__name__)


class ProdutoServicoManager(LojaIsolationManager):
    """Manager de ProdutoServico — geração de código sequencial."""

    def gerar_proximo_codigo(self, tipo: str, loja_id: int) -> str:
        """Gera o próximo código sequencial para produto/serviço.

        Formato: produtos P001, P002…; serviços S001, S002…
        """
        prefixo = "P" if tipo == "produto" else "S"

        ultimo = self.filter(
            loja_id=loja_id,
            codigo__startswith=prefixo,
        ).order_by("-codigo").first()

        if ultimo and ultimo.codigo:
            try:
                proximo_num = int(ultimo.codigo[1:]) + 1
            except (ValueError, IndexError):
                logger.warning(
                    "Erro ao extrair número do código: %s. Iniciando do 1.",
                    ultimo.codigo,
                )
                proximo_num = 1
        else:
            proximo_num = 1

        codigo = f"{prefixo}{proximo_num:03d}"
        logger.debug("Código gerado: %s (tipo=%s, loja_id=%s)", codigo, tipo, loja_id)
        return codigo
