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

    def _salvar_financeiro_mp(self, loja, financeiro, resultado):
        """Persiste dados do Mercado Pago no financeiro e cria PagamentoLoja."""
        boleto_url = (resultado.get("boleto_url") or "")[:200]
        pix_qr = (resultado.get("pix_qr_code") or "")[:2000]
        pix_paste = (resultado.get("pix_copy_paste") or "")[:500]
        pix_pid = (resultado.get("pix_payment_id") or "")[:100]
        financeiro.provedor_boleto = "mercadopago"
        financeiro.mercadopago_payment_id = (resultado.get("payment_id") or "")[:100]
        financeiro.mercadopago_pix_payment_id = pix_pid
        financeiro.asaas_customer_id = ""
        financeiro.asaas_payment_id = ""
        financeiro.boleto_url = boleto_url
        financeiro.pix_qr_code = pix_qr
        financeiro.pix_copy_paste = pix_paste
        financeiro.status_pagamento = "pendente"
        financeiro.save()
        from .models import PagamentoLoja
        pagamento = PagamentoLoja.objects.create(
            loja=loja,
            financeiro=financeiro,
            valor=financeiro.valor_mensalidade,
            referencia_mes=financeiro.data_proxima_cobranca.replace(day=1),
            status="pendente",
            forma_pagamento="boleto",
            data_vencimento=financeiro.data_proxima_cobranca,
            provedor_boleto="mercadopago",
            mercadopago_payment_id=(resultado.get("payment_id") or "")[:100],
            mercadopago_pix_payment_id=pix_pid,
            asaas_payment_id="",
            boleto_url=boleto_url,
            pix_qr_code=pix_qr,
            pix_copy_paste=pix_paste,
        )
        logger.info(
            "Cobrança Mercado Pago criada para loja %s: %s%s",
            loja.nome, resultado.get("payment_id"), f", PIX: {pix_pid}" if pix_pid else "",
        )
        return {
            "success": True,
            "provedor": "mercadopago",
            "payment_id": resultado.get("payment_id"),
            "customer_id": "",
            "boleto_url": resultado.get("boleto_url"),
            "pix_qr_code": pix_qr or resultado.get("pix_qr_code"),
            "pix_copy_paste": pix_paste or resultado.get("pix_copy_paste"),
            "due_date": resultado.get("due_date"),
            "value": resultado.get("value"),
            "pagamento_id": pagamento.id,
        }

    def _salvar_financeiro_asaas(self, loja, financeiro, resultado):
        """Persiste dados do Asaas no financeiro e cria PagamentoLoja."""
        boleto_url_asaas = (resultado.get("boleto_url") or "")[:200]
        financeiro.provedor_boleto = "asaas"
        financeiro.mercadopago_payment_id = ""
        financeiro.asaas_customer_id = resultado.get("customer_id", "")
        financeiro.asaas_payment_id = resultado.get("payment_id", "")
        financeiro.boleto_url = boleto_url_asaas
        financeiro.pix_qr_code = (resultado.get("pix_qr_code") or "")[:500]
        financeiro.pix_copy_paste = (resultado.get("pix_copy_paste") or "")[:500]
        financeiro.status_pagamento = "pendente"
        financeiro.save()
        from .models import PagamentoLoja
        pagamento = PagamentoLoja.objects.create(
            loja=loja,
            financeiro=financeiro,
            valor=financeiro.valor_mensalidade,
            referencia_mes=financeiro.data_proxima_cobranca.replace(day=1),
            status="pendente",
            forma_pagamento="boleto",
            data_vencimento=financeiro.data_proxima_cobranca,
            provedor_boleto="asaas",
            mercadopago_payment_id="",
            asaas_payment_id=(resultado.get("payment_id") or "")[:100],
            boleto_url=boleto_url_asaas,
            pix_qr_code=(resultado.get("pix_qr_code") or "")[:500],
            pix_copy_paste=(resultado.get("pix_copy_paste") or "")[:500],
        )
        logger.info("Cobrança Asaas criada para loja %s: %s", loja.nome, resultado.get("payment_id"))
        return {
            "success": True,
            "provedor": "asaas",
            "payment_id": resultado.get("payment_id"),
            "customer_id": resultado.get("customer_id"),
            "boleto_url": resultado.get("boleto_url"),
            "pix_qr_code": resultado.get("pix_qr_code"),
            "due_date": resultado.get("due_date"),
            "value": resultado.get("value"),
            "pagamento_id": pagamento.id,
        }

    def _criar_cobranca_asaas(self, loja, financeiro) -> dict:
        """Cria cobrança via Asaas. Retorna dict de resultado."""
        try:
            config = self.AsaasConfig.get_config()
            if not self.AsaasConfig.resolve_api_key() or not config.enabled:
                logger.warning("Asaas não configurado ou desabilitado")
                return {"success": False, "error": "Asaas não configurado"}
            loja_data = {
                "nome": loja.nome,
                "email": loja.owner.email,
                "cpf_cnpj": loja.cpf_cnpj or "00000000000",
                "telefone": loja.owner_telefone or "",
                "endereco": loja.logradouro or "",
                "numero": loja.numero or "",
                "complemento": loja.complemento or "",
                "bairro": loja.bairro or "",
                "cidade": loja.cidade or "",
                "estado": loja.uf or "",
                "cep": loja.cep or "",
                "slug": loja.slug,
            }
            plano_data = {"nome": loja.plano.nome, "preco": float(financeiro.valor_mensalidade)}
            service = self.AsaasPaymentService()
            from asaas_integration.models import LojaAssinatura
            customer_id = (financeiro.asaas_customer_id or "").strip() or None
            if not customer_id:
                loja_assinatura = LojaAssinatura.objects.filter(loja_slug=loja.slug).select_related("asaas_customer").first()
                if loja_assinatura and loja_assinatura.asaas_customer_id:
                    customer_id = loja_assinatura.asaas_customer.asaas_id
            resultado = service.create_loja_subscription_payment(loja_data, plano_data, customer_id=customer_id)
            if resultado.get("success"):
                return self._salvar_financeiro_asaas(loja, financeiro, resultado)
            logger.error("Erro ao criar cobrança Asaas: %s", resultado.get("error"))
            return {"success": False, "error": resultado.get("error", "Erro desconhecido")}
        except Exception as e:
            logger.error("Erro no serviço Asaas: %s", e)
            return {"success": False, "error": str(e)}

    def _tentar_cobranca_mercadopago(self, loja, financeiro) -> dict | None:
        """Tenta criar cobrança via Mercado Pago se configurado. Retorna resultado ou None para usar fallback Asaas."""
        try:
            from .mercadopago_service import LojaMercadoPagoService
            from .models import MercadoPagoConfig
            mp_config = MercadoPagoConfig.get_config()
            usar_mp = (
                mp_config.enabled
                and mp_config.access_token
                and getattr(loja, "provedor_boleto_preferido", "asaas") == "mercadopago"
            )
            if not usar_mp:
                return None
            mp_service = LojaMercadoPagoService()
            if not mp_service.available:
                return None
            resultado = mp_service.criar_cobranca_loja(loja, financeiro)
            if resultado.get("success"):
                return self._salvar_financeiro_mp(loja, financeiro, resultado)
            return resultado
        except Exception as e:
            logger.warning("Mercado Pago não usado para cobrança: %s", e)
            return None

    def criar_cobranca_loja(self, loja, financeiro):
        """Cria cobrança (boleto) para a loja. Usa Mercado Pago se configurado e
        use_for_boletos ativo; caso contrário usa Asaas.

        Args:
            loja: Instância da Loja
            financeiro: Instância do FinanceiroLoja

        Returns:
            dict: Resultado da criação da cobrança

        """
        mp_resultado = self._tentar_cobranca_mercadopago(loja, financeiro)
        if mp_resultado is not None:
            return mp_resultado

        # Fallback: Asaas
        if not self.available:
            return {"success": False, "error": "Integração Asaas não disponível"}
        return self._criar_cobranca_asaas(loja, financeiro)

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
