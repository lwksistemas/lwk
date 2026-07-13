"""Serviço unificado para criação de cobranças (Asaas + Mercado Pago)

Usa Strategy Pattern para abstrair a lógica de cada provedor de pagamento,
facilitando manutenção e adição de novos provedores.

Baseado no payment_deletion_service.py existente.
"""
import logging
from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def _parse_due_date(value) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        return date.fromisoformat(value.strip()[:10])
    return date.today()


def _registrar_pagamento_loja_pendente(loja, financeiro, result: dict[str, Any], provedor: str, due_date) -> None:
    """Registra PagamentoLoja pendente para histórico, boleto e NFS-e após confirmação."""
    from django.utils import timezone

    from .models import PagamentoLoja

    payment_id = (result.get("payment_id") or "").strip()
    if not payment_id:
        return

    due = _parse_due_date(due_date)
    valor = result.get("value", financeiro.valor_mensalidade)
    defaults = {
        "valor": valor,
        "status": "pendente",
        "data_vencimento": due,
        "referencia_mes": timezone.now().date().replace(day=1),
        "forma_pagamento": "BOLETO",
        "provedor_boleto": provedor,
        "boleto_url": (result.get("boleto_url") or "")[:200],
        "pix_qr_code": (result.get("pix_qr_code") or "")[:2000],
        "pix_copy_paste": (result.get("pix_copy_paste") or "")[:500],
    }

    if provedor == "mercadopago":
        defaults["mercadopago_payment_id"] = payment_id[:100]
        pix_id = (result.get("pix_payment_id") or "").strip()
        if pix_id:
            defaults["mercadopago_pix_payment_id"] = pix_id[:100]
        pl, _ = PagamentoLoja.objects.update_or_create(
            loja=loja,
            financeiro=financeiro,
            mercadopago_payment_id=payment_id[:100],
            defaults=defaults,
        )
    else:
        defaults["asaas_payment_id"] = payment_id[:100]
        pl, _ = PagamentoLoja.objects.update_or_create(
            loja=loja,
            financeiro=financeiro,
            asaas_payment_id=payment_id[:100],
            defaults=defaults,
        )
    logger.info("PagamentoLoja pendente registrado id=%s loja=%s venc=%s", pl.id, loja.slug, due)


class PaymentProviderStrategy(ABC):
    """Interface abstrata para estratégias de provedor de pagamento"""

    @abstractmethod
    def criar_cobranca(self, loja, financeiro, due_date_override=None) -> dict[str, Any]:
        """Cria cobrança no provedor de pagamento

        Args:
            loja: Instância do modelo Loja
            financeiro: Instância do modelo FinanceiroLoja

        Returns:
            dict com success, payment_id, boleto_url, pix_qr_code, pix_copy_paste, error

        """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna nome do provedor"""


class AsaasPaymentStrategy(PaymentProviderStrategy):
    """Estratégia para criação de cobranças no Asaas"""

    def get_provider_name(self) -> str:
        return "asaas"

    @staticmethod
    def _resolver_customer_id_asaas(financeiro, loja_slug: str) -> str | None:
        """Resolve o customer_id Asaas a partir do financeiro ou da assinatura existente."""
        from asaas_integration.models import LojaAssinatura
        customer_id = (financeiro.asaas_customer_id or "").strip() or None
        if not customer_id:
            loja_assinatura = LojaAssinatura.objects.filter(
                loja_slug=loja_slug,
            ).select_related("asaas_customer").first()
            if loja_assinatura and loja_assinatura.asaas_customer_id:
                customer_id = loja_assinatura.asaas_customer.asaas_id
        return customer_id

    @staticmethod
    def _salvar_assinatura_cobranca(loja_data, plano_data, result, customer, payment, financeiro):
        """Salva/atualiza LojaAssinatura e FinanceiroLoja após criação de cobrança Asaas."""
        from asaas_integration.models import LojaAssinatura
        loja_assinatura_existente = LojaAssinatura.objects.filter(loja_slug=loja_data["slug"]).first()
        if loja_assinatura_existente:
            loja_assinatura_existente.loja_nome = loja_data["nome"]
            loja_assinatura_existente.asaas_customer = customer
            loja_assinatura_existente.current_payment = payment
            loja_assinatura_existente.plano_nome = plano_data["nome"]
            loja_assinatura_existente.plano_valor = plano_data["preco"]
            loja_assinatura_existente.save()
        else:
            LojaAssinatura.objects.create(
                loja_slug=loja_data["slug"],
                loja_nome=loja_data["nome"],
                asaas_customer=customer,
                current_payment=payment,
                plano_nome=plano_data["nome"],
                plano_valor=plano_data["preco"],
                data_vencimento=payment.due_date,
            )
        financeiro.provedor_boleto = "asaas"
        financeiro.asaas_customer_id = result["customer_id"]
        financeiro.asaas_payment_id = result["payment_id"]
        financeiro.boleto_url = result.get("boleto_url", "")
        financeiro.pix_qr_code = result.get("pix_qr_code", "")
        financeiro.pix_copy_paste = result.get("pix_copy_paste", "")
        financeiro.save(update_fields=[
            "provedor_boleto", "asaas_customer_id", "asaas_payment_id",
            "boleto_url", "pix_qr_code", "pix_copy_paste",
        ])

    def criar_cobranca(self, loja, financeiro, due_date_override=None) -> dict[str, Any]:
        """Cria cobrança no Asaas"""
        try:
            from datetime import datetime

            from django.db import transaction

            from asaas_integration.client import AsaasPaymentService
            from asaas_integration.models import AsaasCustomer, AsaasPayment

            logger.info(f"Criando cobrança Asaas para loja: {loja.nome}")

            due = due_date_override or financeiro.data_proxima_cobranca
            due_date_str = due.strftime("%Y-%m-%d") if hasattr(due, "strftime") else str(due)[:10]

            loja_data = {
                "nome": loja.nome,
                "slug": loja.slug,
                "email": loja.owner.email,
                "cpf_cnpj": loja.cpf_cnpj or "000.000.000-00",
                "telefone": loja.owner_telefone or "",  # ✅ CORREÇÃO: Telefone do administrador para NF
                # ✅ CORREÇÃO v1320: Incluir endereço completo para emissão de NF
                "endereco": loja.logradouro or "",
                "numero": loja.numero or "",
                "complemento": loja.complemento or "",
                "bairro": loja.bairro or "",
                "cidade": loja.cidade or "",
                "estado": loja.uf or "",
                "cep": loja.cep or "",
            }

            valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == "anual" else loja.plano.preco_mensal
            plano_data = {
                "nome": f"{loja.plano.nome} ({loja.get_tipo_assinatura_display()})",
                "preco": valor_plano,
            }

            # Criar cobrança no Asaas
            service = AsaasPaymentService()

            # Verificar se já existe customer_id no financeiro ou na assinatura
            customer_id = self._resolver_customer_id_asaas(financeiro, loja.slug)

            result = service.create_loja_subscription_payment(
                loja_data,
                plano_data,
                due_date=due_date_str,
                customer_id=customer_id,
            )

            if not result["success"]:
                logger.error(f"Erro ao criar cobrança Asaas: {result['error']}")
                return result

            # Salvar no banco local
            with transaction.atomic():
                # Criar/atualizar cliente
                customer, _ = AsaasCustomer.objects.update_or_create(
                    asaas_id=result["customer_id"],
                    defaults={
                        "name": loja_data["nome"],
                        "email": loja_data["email"],
                        "cpf_cnpj": loja_data["cpf_cnpj"],
                        "phone": loja_data.get("telefone", ""),
                        "external_reference": f"loja_{loja_data['slug']}",
                        "raw_data": result.get("raw_customer", {}),
                    },
                )

                # Criar pagamento
                payment = AsaasPayment.objects.create(
                    asaas_id=result["payment_id"],
                    customer=customer,
                    external_reference=f"loja_{loja_data['slug']}_assinatura",
                    billing_type="BOLETO",
                    status=result["status"],
                    value=result["value"],
                    due_date=datetime.strptime(result["due_date"], "%Y-%m-%d").date(),
                    invoice_url=result["payment_url"],
                    bank_slip_url=result["boleto_url"],
                    pix_qr_code=result.get("pix_qr_code", ""),
                    pix_copy_paste=result.get("pix_copy_paste", ""),
                    description=f"Assinatura {plano_data['nome']} - Loja {loja_data['nome']}",
                    raw_data=result.get("raw_payment", {}),
                )

                # Criar/atualizar assinatura e FinanceiroLoja
                self._salvar_assinatura_cobranca(loja_data, plano_data, result, customer, payment, financeiro)

            logger.info(f"✅ Cobrança Asaas criada: payment_id={result['payment_id']}")

            payload = {
                "success": True,
                "provedor": "asaas",
                "payment_id": result["payment_id"],
                "boleto_url": result.get("boleto_url", ""),
                "pix_qr_code": result.get("pix_qr_code", ""),
                "pix_copy_paste": result.get("pix_copy_paste", ""),
                "due_date": result["due_date"],
                "value": result["value"],
            }
            _registrar_pagamento_loja_pendente(loja, financeiro, payload, "asaas", result["due_date"])
            return payload

        except Exception as e:
            logger.exception(f"Erro ao criar cobrança Asaas para loja {loja.slug}: {e}")
            return {"success": False, "error": str(e)}


class MercadoPagoPaymentStrategy(PaymentProviderStrategy):
    """Estratégia para criação de cobranças no Mercado Pago"""

    def get_provider_name(self) -> str:
        return "mercadopago"

    def criar_cobranca(self, loja, financeiro, due_date_override=None) -> dict[str, Any]:
        """Cria cobrança no Mercado Pago"""
        try:
            from superadmin.mercadopago_service import LojaMercadoPagoService

            logger.info(f"Criando cobrança Mercado Pago para loja: {loja.nome}")

            original_due = None
            if due_date_override is not None:
                original_due = financeiro.data_proxima_cobranca
                financeiro.data_proxima_cobranca = _parse_due_date(due_date_override)

            service = LojaMercadoPagoService()
            result = service.criar_cobranca_loja(loja, financeiro, criar_pix=True)

            if original_due is not None:
                financeiro.data_proxima_cobranca = original_due

            if not result.get("success"):
                logger.error(f"Erro ao criar cobrança Mercado Pago: {result.get('error')}")
                return result

            # Atualizar FinanceiroLoja
            financeiro.provedor_boleto = "mercadopago"
            financeiro.mercadopago_payment_id = result.get("payment_id", "")[:100]
            financeiro.mercadopago_pix_payment_id = result.get("pix_payment_id", "")[:100]
            financeiro.boleto_url = result.get("boleto_url", "")[:200]
            financeiro.pix_qr_code = result.get("pix_qr_code", "")[:2000]
            financeiro.pix_copy_paste = result.get("pix_copy_paste", "")[:500]
            financeiro.save(update_fields=[
                "provedor_boleto", "mercadopago_payment_id", "mercadopago_pix_payment_id",
                "boleto_url", "pix_qr_code", "pix_copy_paste",
            ])

            logger.info(f"✅ Cobrança Mercado Pago criada: payment_id={result.get('payment_id')}")

            payload = {
                "success": True,
                "provedor": "mercadopago",
                "payment_id": result.get("payment_id"),
                "boleto_url": result.get("boleto_url", ""),
                "pix_qr_code": result.get("pix_qr_code", ""),
                "pix_copy_paste": result.get("pix_copy_paste", ""),
                "due_date": result.get("due_date"),
                "value": result.get("value"),
                "pix_payment_id": result.get("pix_payment_id"),
            }
            _registrar_pagamento_loja_pendente(loja, financeiro, payload, "mercadopago", result.get("due_date"))
            return payload

        except Exception as e:
            logger.exception(f"Erro ao criar cobrança Mercado Pago para loja {loja.slug}: {e}")
            return {"success": False, "error": str(e)}


class CobrancaService:
    """Serviço unificado para criação de cobranças

    Usa Strategy Pattern para abstrair a lógica de cada provedor.
    """

    def __init__(self):
        self.strategies = {
            "asaas": AsaasPaymentStrategy(),
            "mercadopago": MercadoPagoPaymentStrategy(),
        }

    def criar_cobranca(self, loja, financeiro, due_date_override=None) -> dict[str, Any]:
        """Cria cobrança no provedor escolhido pela loja

        Args:
            loja: Instância do modelo Loja
            financeiro: Instância do modelo FinanceiroLoja
            due_date_override: Vencimento do boleto (ex.: pagamento antecipado)

        Returns:
            dict com success, provedor, payment_id, boleto_url, pix_qr_code, error

        """
        validation_error = self._validar_dados_loja(loja)
        if validation_error:
            return {"success": False, "error": validation_error}

        provedor = loja.provedor_boleto_preferido or "asaas"
        strategy = self.strategies.get(provedor)

        if not strategy:
            return {"success": False, "error": f"Provedor {provedor} não suportado"}

        logger.info(f"Criando cobrança para loja {loja.slug} usando provedor {provedor}")

        return strategy.criar_cobranca(loja, financeiro, due_date_override=due_date_override)

    def renovar_cobranca(self, loja, financeiro, dia_vencimento=None, antecipado=False) -> dict[str, Any]:
        """Cria nova cobrança para o proprietário pagar (antecipado ou renovação).

        antecipado=True: boleto com vencimento na data_proxima_cobranca (sem alterar o ciclo futuro).
        """
        due_date_override = None
        if antecipado:
            due_date_override = financeiro.data_proxima_cobranca or (date.today() + timedelta(days=3))
            logger.info("Cobrança manual loja %s, vencimento %s", loja.slug, due_date_override)
        elif dia_vencimento is not None:
            financeiro.dia_vencimento = dia_vencimento
            financeiro.data_proxima_cobranca = self._calcular_proxima_cobranca(dia_vencimento, loja.tipo_assinatura)
            financeiro.save(update_fields=["dia_vencimento", "data_proxima_cobranca"])
            logger.info(f"Data de vencimento atualizada para dia {dia_vencimento}")

        return self.criar_cobranca(loja, financeiro, due_date_override=due_date_override)

    def _validar_dados_loja(self, loja) -> str:
        """Valida dados necessários para criar cobrança

        Returns:
            str com mensagem de erro ou None se válido

        """
        if not loja.cpf_cnpj:
            return "CPF/CNPJ da loja é obrigatório"

        if not loja.owner or not loja.owner.email:
            return "Email do administrador da loja é obrigatório"

        # Validações específicas do Mercado Pago
        if loja.provedor_boleto_preferido == "mercadopago":
            campos_obrigatorios = {
                "cep": "CEP",
                "logradouro": "Logradouro",
                "cidade": "Cidade",
                "uf": "UF",
            }

            for campo, nome in campos_obrigatorios.items():
                if not getattr(loja, campo, None):
                    return f"{nome} é obrigatório para boletos do Mercado Pago"

        return None

    def _calcular_proxima_cobranca(self, dia_vencimento: int, tipo_assinatura: str = "mensal") -> date:
        """Calcula próxima data de cobrança baseada no dia de vencimento e tipo de assinatura

        Args:
            dia_vencimento: Dia do mês (1-28)
            tipo_assinatura: 'mensal' ou 'anual'

        Returns:
            date da próxima cobrança (próximo mês para mensal, próximo ano para anual)

        """
        hoje = date.today()

        if tipo_assinatura == "anual":
            # Para assinatura anual, adicionar 1 ano
            proximo_ano = hoje.year + 1
            proximo_mes = hoje.month

            # Ajustar dia se o mês não tiver esse dia (ex: 29 de fevereiro em ano não bissexto)
            ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
            dia_cobranca = min(dia_vencimento, ultimo_dia_mes)

            return date(proximo_ano, proximo_mes, dia_cobranca)
        # Para assinatura mensal, calcular próximo mês
        if hoje.month == 12:
            proximo_mes = 1
            proximo_ano = hoje.year + 1
        else:
            proximo_mes = hoje.month + 1
            proximo_ano = hoje.year

        # Ajustar dia se o mês não tiver esse dia (ex: dia 31 em fevereiro)
        ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
        dia_cobranca = min(dia_vencimento, ultimo_dia_mes)

        return date(proximo_ano, proximo_mes, dia_cobranca)
