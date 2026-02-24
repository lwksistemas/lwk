"""
Serviço para integração com Mercado Pago na geração de boletos para lojas.
API: https://www.mercadopago.com.br/developers/pt/reference/payments/_payments/post
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Boleto no Brasil: payment_method_id = bolbradesco
MP_PAYMENT_METHOD_BOLETO = "bolbradesco"
MP_API_BASE = "https://api.mercadopago.com"


class MercadoPagoClient:
    """Cliente para API de pagamentos do Mercado Pago (v1)."""

    def __init__(self, access_token: str):
        self.access_token = access_token.strip()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4()),
        })

    def _post_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{MP_API_BASE}/v1/payments"
        # Nova chave de idempotência por requisição
        self.session.headers["X-Idempotency-Key"] = str(uuid.uuid4())
        resp = self.session.post(url, json=payload, timeout=30)
        if resp.status_code >= 400:
            logger.warning("Mercado Pago API error: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()
        return resp.json()

    def create_boleto(
        self,
        transaction_amount: float,
        payer_email: str,
        payer_first_name: str,
        payer_last_name: str,
        payer_doc_type: str,
        payer_doc_number: str,
        due_date: str,
        description: str,
        external_reference: str = "",
        zip_code: str = "",
        street_name: str = "",
        street_number: str = "",
        neighborhood: str = "",
        city: str = "",
        federal_unit: str = "",
    ) -> Dict[str, Any]:
        """
        Cria um pagamento por boleto (Brasil - bolbradesco).

        due_date: YYYY-MM-DD.
        payer_doc_type: 'CPF' ou 'CNPJ'.
        payer_doc_number: apenas números.
        """
        # Data de expiração no formato ISO 8601 (fim do dia no Brasil -03:00)
        try:
            dt = datetime.strptime(due_date, "%Y-%m-%d")
            date_of_expiration = dt.replace(hour=23, minute=59, second=59, microsecond=0)
            date_of_expiration = date_of_expiration.strftime("%Y-%m-%dT%H:%M:%S.000-03:00")
        except Exception:
            date_of_expiration = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT23:59:59.000-03:00")

        doc_number = "".join(c for c in str(payer_doc_number) if c.isdigit()) or "00000000000"
        if len(doc_number) > 11:
            payer_doc_type = "CNPJ"
        else:
            payer_doc_type = "CPF"

        payload = {
            "transaction_amount": round(float(transaction_amount), 2),
            "payment_method_id": MP_PAYMENT_METHOD_BOLETO,
            "payer": {
                "email": payer_email,
                "first_name": (payer_first_name or " ").strip() or "Cliente",
                "last_name": (payer_last_name or " ").strip() or "Loja",
                "identification": {
                    "type": payer_doc_type,
                    "number": doc_number,
                },
                "address": {
                    "zip_code": (zip_code or "").replace("-", "").replace(" ", "")[:8] or "00000000",
                    "street_name": (street_name or "Não informado")[:100],
                    "street_number": (street_number or "0")[:10],
                    "neighborhood": (neighborhood or "Não informado")[:50],
                    "city": (city or "Não informado")[:50],
                    "federal_unit": (federal_unit or "SP")[:2],
                },
            },
            "date_of_expiration": date_of_expiration,
            "description": (description or "Assinatura")[:230],
        }
        if external_reference:
            payload["external_reference"] = external_reference[:256]

        return self._post_payment(payload)

    def test_connection(self) -> Dict[str, Any]:
        """
        Testa a conexão com a API do Mercado Pago (valida o Access Token).
        Usa GET /v1/payment_methods como health check.
        """
        try:
            url = f"{MP_API_BASE}/v1/payment_methods"
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 401:
                return {"success": False, "error": "Access Token inválido ou expirado."}
            if resp.status_code >= 400:
                return {"success": False, "error": resp.text or f"HTTP {resp.status_code}"}
            data = resp.json()
            # Lista de métodos (bolbradesco = boleto está presente em produção)
            methods = data if isinstance(data, list) else []
            boleto_ok = any(
                m.get("id") == MP_PAYMENT_METHOD_BOLETO
                for m in (methods if isinstance(methods, list) else [])
            )
            return {
                "success": True,
                "message": "Conexão com a API do Mercado Pago OK. Boleto (bolbradesco) disponível."
                if boleto_ok
                else "Conexão com a API do Mercado Pago OK.",
                "payment_methods_count": len(methods) if isinstance(methods, list) else 0,
            }
        except requests.exceptions.RequestException as e:
            msg = getattr(e, "response", None)
            if msg is not None and hasattr(msg, "text"):
                try:
                    err = msg.json()
                    msg = err.get("message", msg.text)
                except Exception:
                    msg = msg.text
            else:
                msg = str(e)
            logger.warning("Mercado Pago test_connection error: %s", msg)
            return {"success": False, "error": msg}
        except Exception as e:
            logger.exception("Mercado Pago test_connection exception")
            return {"success": False, "error": str(e)}

    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados de um pagamento pela API do Mercado Pago."""
        try:
            url = f"{MP_API_BASE}/v1/payments/{payment_id}"
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception as e:
            logger.warning("Erro ao obter pagamento MP %s: %s", payment_id, e)
            return None

    def cancel_payment(self, payment_id: str) -> bool:
        """
        Cancela um pagamento pendente no Mercado Pago (PUT status=cancelled).
        Só é possível cancelar quando status é 'pending' ou 'in_process'.
        Retorna True se cancelou, False se não cancelou (já pago, já cancelado ou erro).
        """
        try:
            payment = self.get_payment(payment_id)
            if not payment:
                return False
            status = (payment.get("status") or "").lower()
            if status not in ("pending", "in_process", "in_mediation"):
                logger.info(
                    "Pagamento MP %s não cancelado (status: %s)",
                    payment_id,
                    status,
                )
                return False
            url = f"{MP_API_BASE}/v1/payments/{payment_id}"
            self.session.headers["X-Idempotency-Key"] = str(uuid.uuid4())
            resp = self.session.put(
                url,
                json={"status": "cancelled"},
                timeout=15,
            )
            if resp.status_code >= 400:
                logger.warning(
                    "Mercado Pago cancel_payment %s: %s %s",
                    payment_id,
                    resp.status_code,
                    resp.text,
                )
                return False
            logger.info("Pagamento MP %s cancelado", payment_id)
            return True
        except Exception as e:
            logger.warning("Erro ao cancelar pagamento MP %s: %s", payment_id, e)
            return False


class LojaMercadoPagoService:
    """Serviço para criar cobrança (boleto) de loja via Mercado Pago."""

    def __init__(self):
        self._config = None
        try:
            from .models import MercadoPagoConfig
            self._config = MercadoPagoConfig.get_config()
        except Exception as e:
            logger.warning("MercadoPagoConfig não disponível: %s", e)

    @property
    def available(self) -> bool:
        return (
            self._config is not None
            and bool(self._config.access_token)
            and self._config.enabled
        )

    def criar_cobranca_loja(self, loja, financeiro) -> Dict[str, Any]:
        """
        Cria cobrança no Mercado Pago (boleto) para a loja.

        Args:
            loja: instância de Loja
            financeiro: instância de FinanceiroLoja

        Returns:
            dict com success, payment_id, boleto_url, due_date, value ou error.
        """
        if not self.available:
            return {"success": False, "error": "Mercado Pago não configurado ou desabilitado"}

        try:
            from django.contrib.auth.models import User
            owner = loja.owner
            if not isinstance(owner, User):
                owner = getattr(loja, "owner_id", None) and User.objects.get(pk=loja.owner_id)
            email = getattr(owner, "email", "") or ""
            first_name = (getattr(owner, "first_name", "") or "").strip() or loja.nome[:50]
            last_name = (getattr(owner, "last_name", "") or "").strip() or "."
        except Exception as e:
            logger.warning("Dados do owner da loja: %s", e)
            email = ""
            first_name = loja.nome[:50] if loja.nome else "Cliente"
            last_name = "."

        cpf_cnpj = (loja.cpf_cnpj or "").replace(".", "").replace("-", "").replace("/", "").strip()
        if not cpf_cnpj or not email:
            return {
                "success": False,
                "error": "Loja precisa de e-mail do responsável e CPF/CNPJ para gerar boleto no Mercado Pago.",
            }

        # Mercado Pago exige endereço completo do pagador para boleto (CEP, logradouro, número, bairro, cidade, UF)
        cep_ok = (getattr(loja, "cep", None) or "").replace("-", "").replace(" ", "").strip()
        cep_ok = len(cep_ok) >= 8
        endereco_ok = bool((getattr(loja, "logradouro", None) or "").strip() and (getattr(loja, "cidade", None) or "").strip() and (getattr(loja, "uf", None) or "").strip())
        if not cep_ok or not endereco_ok:
            return {
                "success": False,
                "error": "Para gerar boleto pelo Mercado Pago, preencha o endereço da loja: CEP (buscar), logradouro, número, bairro, cidade e UF.",
            }

        due_date = financeiro.data_proxima_cobranca
        if hasattr(due_date, "strftime"):
            due_date = due_date.strftime("%Y-%m-%d")
        else:
            due_date = str(due_date)[:10]

        client = MercadoPagoClient(self._config.access_token)
        description = f"Assinatura {loja.plano.nome} - Loja {loja.nome}"
        external_ref = f"loja_{loja.slug}_assinatura"

        # Endereço da loja (obrigatório para boleto MP: zip_code, street_name, street_number, neighborhood, city, federal_unit)
        zip_code = (getattr(loja, "cep", None) or "").strip()
        street_name = (getattr(loja, "logradouro", None) or "").strip()
        street_number = (getattr(loja, "numero", None) or "").strip()
        neighborhood = (getattr(loja, "bairro", None) or "").strip()
        city = (getattr(loja, "cidade", None) or "").strip()
        federal_unit = (getattr(loja, "uf", None) or "").strip()[:2].upper()

        try:
            result = client.create_boleto(
                transaction_amount=float(financeiro.valor_mensalidade),
                payer_email=email,
                payer_first_name=first_name,
                payer_last_name=last_name,
                payer_doc_type="CPF",
                payer_doc_number=cpf_cnpj,
                due_date=due_date,
                description=description,
                external_reference=external_ref,
                zip_code=zip_code,
                street_name=street_name,
                street_number=street_number,
                neighborhood=neighborhood,
                city=city,
                federal_unit=federal_unit,
            )
        except requests.exceptions.HTTPError as e:
            msg = getattr(e, "response", None)
            if msg is not None and hasattr(msg, "text"):
                try:
                    err = msg.json()
                    msg = err.get("message", msg.text)
                except Exception:
                    msg = msg.text
            else:
                msg = str(e)
            logger.error("Mercado Pago create_boleto error: %s", msg)
            return {"success": False, "error": msg}
        except Exception as e:
            logger.exception("Mercado Pago create_boleto exception")
            return {"success": False, "error": str(e)}

        payment_id = str(result.get("id", ""))
        status = result.get("status", "")
        # Link do boleto para o pagador
        transaction_details = result.get("transaction_details") or {}
        boleto_url = (
            transaction_details.get("external_resource_url")
            or result.get("transaction_details", {}).get("external_resource_url")
            or ""
        )
        if not boleto_url and result.get("point_of_interaction"):
            poi = result.get("point_of_interaction", {})
            boleto_url = poi.get("transaction_data", {}).get("ticket_url") or ""

        date_approved = result.get("date_approved")
        date_created = result.get("date_created")

        return {
            "success": True,
            "payment_id": payment_id,
            "boleto_url": boleto_url,
            "due_date": due_date,
            "value": float(result.get("transaction_amount", financeiro.valor_mensalidade)),
            "status": status,
            "raw": result,
        }

    def get_boleto_url(self, payment_id: str) -> Optional[str]:
        """Obtém a URL do boleto consultando o pagamento no MP (se necessário)."""
        if not self.available or not payment_id:
            return None
        try:
            url = f"{MP_API_BASE}/v1/payments/{payment_id}"
            resp = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {self._config.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            td = data.get("transaction_details") or {}
            return td.get("external_resource_url") or ""
        except Exception as e:
            logger.warning("Erro ao obter boleto URL do MP: %s", e)
            return None

    def cancel_pending_payments_loja(self, loja_slug: str) -> Dict[str, Any]:
        """
        Cancela todos os boletos pendentes do Mercado Pago associados à loja
        (igual ao fluxo Asaas na exclusão da loja).
        Retorna dict com success, cancelled_count, error (opcional).
        """
        if not self.available:
            return {
                "success": False,
                "cancelled_count": 0,
                "error": "Mercado Pago não configurado ou desabilitado",
            }
        try:
            from .models import FinanceiroLoja, Loja, PagamentoLoja

            try:
                loja = Loja.objects.get(slug=loja_slug)
            except Loja.DoesNotExist:
                logger.info("Loja não encontrada: %s", loja_slug)
                return {
                    "success": True,
                    "cancelled_count": 0,
                    "message": "Loja não encontrada",
                }

            payment_ids = set()
            for fin in FinanceiroLoja.objects.filter(loja=loja).exclude(
                mercadopago_payment_id=""
            ).values_list("mercadopago_payment_id", flat=True):
                if fin:
                    payment_ids.add(str(fin).strip())
            for pag in PagamentoLoja.objects.filter(loja=loja).exclude(
                mercadopago_payment_id=""
            ).values_list("mercadopago_payment_id", flat=True):
                if pag:
                    payment_ids.add(str(pag).strip())

            if not payment_ids:
                logger.info(
                    "Nenhum boleto Mercado Pago pendente para loja: %s",
                    loja_slug,
                )
                return {
                    "success": True,
                    "cancelled_count": 0,
                    "message": "Nenhum pagamento MP encontrado para a loja",
                }

            client = MercadoPagoClient(self._config.access_token)
            cancelled = 0
            for pid in payment_ids:
                if client.cancel_payment(pid):
                    cancelled += 1
            logger.info(
                "Mercado Pago: %s pagamento(s) cancelado(s) para loja %s",
                cancelled,
                loja_slug,
            )
            return {
                "success": True,
                "cancelled_count": cancelled,
                "message": f"{cancelled} boleto(s) cancelado(s) no Mercado Pago",
            }
        except Exception as e:
            logger.exception("Erro ao cancelar boletos MP da loja %s: %s", loja_slug, e)
            return {
                "success": False,
                "cancelled_count": 0,
                "error": str(e),
            }
