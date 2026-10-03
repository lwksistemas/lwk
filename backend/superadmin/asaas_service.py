"""Serviço para integração com Asaas na criação de lojas
"""
import logging

logger = logging.getLogger(__name__)

class LojaAsaasService:
    """Serviço para criar cobrança Asaas quando uma loja é criada"""

    def __init__(self):
        # Importação condicional para evitar erro se asaas_integration não estiver disponível
        try:
            from asaas_integration.client import AsaasPaymentService
            from asaas_integration.models import AsaasConfig
            self.AsaasConfig = AsaasConfig
            self.AsaasPaymentService = AsaasPaymentService
            self.available = True
        except ImportError:
            logger.warning("Asaas integration não disponível")
            self.available = False

    def baixar_pdf_boleto(self, payment_id):
        """Baixa o PDF do boleto do Asaas

        Args:
            payment_id: ID do pagamento no Asaas

        Returns:
            bytes: Conteúdo do PDF ou None se erro

        """
        if not self.available:
            return None

        try:
            config = self.AsaasConfig.get_config()
            if not self.AsaasConfig.resolve_api_key() or not config.enabled:
                return None

            service = self.AsaasPaymentService()
            return service.download_boleto_pdf(payment_id)

        except Exception as e:
            logger.error(f"Erro ao baixar PDF do boleto: {e}")
            return None

    def consultar_status_pagamento(self, payment_id):
        """Consulta status de um pagamento no Asaas

        Args:
            payment_id: ID do pagamento no Asaas

        Returns:
            dict: Status do pagamento

        """
        if not self.available:
            return {"success": False, "error": "Asaas não disponível"}

        try:
            config = self.AsaasConfig.get_config()
            if not self.AsaasConfig.resolve_api_key() or not config.enabled:
                return {"success": False, "error": "Asaas não configurado"}

            service = self.AsaasPaymentService()
            return service.get_payment_status(payment_id)

        except Exception as e:
            logger.error(f"Erro ao consultar status: {e}")
            return {"success": False, "error": str(e)}
