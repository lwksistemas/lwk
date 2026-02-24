"""
Serviço para integração com Mercado Pago na geração de boletos para lojas.
API: https://www.mercadopago.com.br/developers/pt/reference/payments/_payments/post
"""
import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Boleto no Brasil: payment_method_id = bolbradesco
MP_PAYMENT_METHOD_BOLETO = "bolbradesco"
# PIX Brasil
MP_PAYMENT_METHOD_PIX = "pix"
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

    def create_pix(
        self,
        transaction_amount: float,
        payer_email: str,
        payer_first_name: str,
        payer_last_name: str,
        payer_doc_type: str,
        payer_doc_number: str,
        description: str,
        external_reference: str = "",
    ) -> Dict[str, Any]:
        """
        Cria um pagamento por PIX (Brasil).
        Retorna o mesmo formato da API; qr_code (copia e cola) e qr_code_base64 vêm em point_of_interaction.transaction_data.
        """
        doc_number = "".join(c for c in str(payer_doc_number) if c.isdigit()) or "00000000000"
        if len(doc_number) > 11:
            payer_doc_type = "CNPJ"
        else:
            payer_doc_type = "CPF"
        payload = {
            "transaction_amount": round(float(transaction_amount), 2),
            "payment_method_id": MP_PAYMENT_METHOD_PIX,
            "payer": {
                "email": (payer_email or "").strip() or "pagador@email.com",
                "first_name": (payer_first_name or " ").strip() or "Cliente",
                "last_name": (payer_last_name or " ").strip() or "Loja",
                "identification": {
                    "type": payer_doc_type,
                    "number": doc_number,
                },
            },
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

    def criar_cobranca_loja(self, loja, financeiro, criar_pix: bool = True) -> Dict[str, Any]:
        """
        Cria cobrança no Mercado Pago (boleto + PIX) para a loja.

        Por padrão cria boleto e PIX (QR + copia e cola) para a loja pagar rápido
        e a assinatura ser atualizada/liberada via webhook.

        Args:
            loja: instância de Loja
            financeiro: instância de FinanceiroLoja
            criar_pix: se True (padrão), cria também pagamento PIX com QR na mesma cobrança.

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
        # Mercado Pago: data de vencimento do boleto não pode ser maior que 29 dias (usar 28 para evitar rejeição)
        try:
            dt_due = datetime.strptime(due_date, "%Y-%m-%d").date()
            today = date.today()
            if (dt_due - today).days > 28:
                due_date = (today + timedelta(days=28)).strftime("%Y-%m-%d")
                logger.info("Mercado Pago: vencimento limitado a 28 dias: %s", due_date)
        except Exception:
            pass

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

        # PIX opcional: na criação da loja criamos só o boleto (1 transação no MP).
        # PIX pode ser gerado depois pelo botão "Gerar PIX" no financeiro.
        pix_payment_id = ""
        pix_qr_code = ""
        pix_copy_paste = ""

        if criar_pix:
            def _extract_pix_from_response(pix_result: dict) -> tuple:
                """Extrai qr_code e qr_code_base64 da resposta do MP (transaction_data)."""
                poi = pix_result.get("point_of_interaction") or {}
                tdata = poi.get("transaction_data") or {}
                cp = (tdata.get("qr_code") or tdata.get("qr_code_copia_cola") or "")[:500]
                qr = (tdata.get("qr_code_base64") or "")[:2000]
                return cp, qr

            try:
                pix_result = client.create_pix(
                    transaction_amount=float(financeiro.valor_mensalidade),
                    payer_email=email,
                    payer_first_name=first_name,
                    payer_last_name=last_name,
                    payer_doc_type="CPF",
                    payer_doc_number=cpf_cnpj,
                    description=description,
                    external_reference=external_ref + "_pix",
                )
                pix_payment_id = str(pix_result.get("id", ""))
                pix_copy_paste, pix_qr_code = _extract_pix_from_response(pix_result)
                # Se criou o pagamento PIX mas QR não veio na resposta, refetch (API às vezes retorna após um instante)
                import time
                for tentativa, espera in enumerate([1, 2], 1):
                    if pix_payment_id and not pix_copy_paste:
                        try:
                            time.sleep(espera)
                            refetched = client.get_payment(pix_payment_id)
                            if refetched:
                                pix_copy_paste, pix_qr_code = _extract_pix_from_response(refetched)
                                if pix_copy_paste:
                                    logger.info("PIX Mercado Pago: QR obtido na consulta %s para loja %s", tentativa + 1, loja.nome)
                                    break
                                if tentativa == 2:
                                    tdata = (refetched.get("point_of_interaction") or {}).get("transaction_data") or {}
                                    logger.info("PIX MP sem QR após refetch; transaction_data keys: %s", list(tdata.keys()))
                        except Exception as e2:
                            logger.debug("PIX refetch tentativa %s para %s: %s", tentativa, loja.nome, e2)
                    else:
                        break
                if pix_payment_id and not pix_copy_paste:
                    tdata = (pix_result.get("point_of_interaction") or {}).get("transaction_data") or {}
                    logger.info("PIX MP criado mas QR vazio na resposta inicial; transaction_data keys: %s", list(tdata.keys()))
                if pix_payment_id:
                    logger.info("PIX Mercado Pago criado para loja %s: %s (QR: %s)", loja.nome, pix_payment_id, "sim" if pix_copy_paste else "não")
            except requests.exceptions.HTTPError as e:
                err_body = getattr(e, "response", None) and getattr(e.response, "text", None)
                logger.warning("PIX Mercado Pago não gerado para %s: %s | Response: %s", loja.nome, e, (err_body or "")[:500])
            except Exception as e:
                logger.warning("PIX Mercado Pago não gerado para %s: %s", loja.nome, e)
        else:
            logger.info("Cobrança MP para loja %s: apenas boleto (criar_pix=False)", loja.nome)

        return {
            "success": True,
            "payment_id": payment_id,
            "boleto_url": boleto_url,
            "due_date": due_date,
            "value": float(result.get("transaction_amount", financeiro.valor_mensalidade)),
            "status": status,
            "raw": result,
            "pix_payment_id": pix_payment_id or None,
            "pix_qr_code": pix_qr_code or None,
            "pix_copy_paste": pix_copy_paste or None,
        }

    def get_boleto_url(self, payment_id: str) -> Optional[str]:
        """
        Obtém a URL completa do boleto consultando o pagamento na API do MP.
        Sempre use este método ao exibir/baixar boleto: a URL salva em boleto_url
        é truncada a 200 chars e perde o hash, gerando 'Pagamento não encontrado'.
        """
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
            boleto_url = td.get("external_resource_url") or ""
            if not boleto_url and data.get("point_of_interaction"):
                poi = data.get("point_of_interaction", {})
                boleto_url = poi.get("transaction_data", {}).get("ticket_url") or ""
            return boleto_url or None
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
            ).values_list("mercadopago_payment_id", "mercadopago_pix_payment_id"):
                for pid in fin:
                    if pid:
                        payment_ids.add(str(pid).strip())
            for pag in PagamentoLoja.objects.filter(loja=loja).values_list(
                "mercadopago_payment_id", "mercadopago_pix_payment_id"
            ):
                for pid in pag:
                    if pid:
                        payment_ids.add(str(pid).strip())

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

    def gerar_pix_para_pagamento(self, pagamento) -> Dict[str, Any]:
        """
        Gera PIX para um PagamentoLoja que já tem boleto MP mas ainda não tem PIX
        (ex.: cobrança criada antes da opção PIX ou falha na criação).
        Persiste em FinanceiroLoja e PagamentoLoja e retorna pix_copy_paste e pix_qr_code.
        """
        from .models import PagamentoLoja

        if not self.available:
            return {"success": False, "error": "Mercado Pago não configurado ou desabilitado"}
        if not isinstance(pagamento, PagamentoLoja):
            return {"success": False, "error": "Pagamento inválido"}
        if getattr(pagamento, "provedor_boleto", "") != "mercadopago":
            return {"success": False, "error": "Apenas pagamentos Mercado Pago podem gerar PIX por aqui"}
        if (getattr(pagamento, "pix_copy_paste", None) or "").strip():
            return {
                "success": True,
                "pix_copy_paste": pagamento.pix_copy_paste,
                "pix_qr_code": getattr(pagamento, "pix_qr_code", None) or "",
                "message": "PIX já existente",
            }
        loja = pagamento.loja
        financeiro = pagamento.financeiro
        try:
            from django.contrib.auth.models import User

            owner = getattr(loja, "owner", None)
            if not isinstance(owner, User):
                owner = getattr(loja, "owner_id", None) and User.objects.get(pk=loja.owner_id)
            email = getattr(owner, "email", "") or ""
            first_name = (getattr(owner, "first_name", "") or "").strip() or (loja.nome or "")[:50]
            last_name = (getattr(owner, "last_name", "") or "").strip() or "."
        except Exception as e:
            logger.warning("Dados do owner da loja: %s", e)
            email = ""
            first_name = (loja.nome or "Cliente")[:50]
            last_name = "."

        cpf_cnpj = (getattr(loja, "cpf_cnpj", None) or "").replace(".", "").replace("-", "").replace("/", "").strip()
        if not cpf_cnpj or not email:
            return {
                "success": False,
                "error": "Loja precisa de e-mail do responsável e CPF/CNPJ para gerar PIX.",
            }

        description = f"Assinatura {getattr(loja.plano, 'nome', 'Plano')} - Loja {loja.nome}"
        external_ref = f"loja_{loja.slug}_pix_{pagamento.id}"

        try:
            client = MercadoPagoClient(self._config.access_token)
            valor = float(pagamento.valor)
            pix_result = client.create_pix(
                transaction_amount=valor,
                payer_email=email,
                payer_first_name=first_name,
                payer_last_name=last_name,
                payer_doc_type="CPF",
                payer_doc_number=cpf_cnpj,
                description=description,
                external_reference=external_ref,
            )
            pix_payment_id = str(pix_result.get("id", ""))
            poi = pix_result.get("point_of_interaction") or {}
            tdata = poi.get("transaction_data") or {}
            pix_copy_paste = (tdata.get("qr_code") or "")[:500]
            pix_qr_code = (tdata.get("qr_code_base64") or "")[:2000]
            if not pix_copy_paste:
                return {"success": False, "error": "Resposta do Mercado Pago sem código PIX"}
            financeiro.pix_copy_paste = pix_copy_paste
            financeiro.pix_qr_code = pix_qr_code or ""
            financeiro.mercadopago_pix_payment_id = pix_payment_id
            financeiro.save(update_fields=["pix_copy_paste", "pix_qr_code", "mercadopago_pix_payment_id"])
            pagamento.pix_copy_paste = pix_copy_paste
            pagamento.pix_qr_code = pix_qr_code or ""
            pagamento.mercadopago_pix_payment_id = pix_payment_id
            pagamento.save(update_fields=["pix_copy_paste", "pix_qr_code", "mercadopago_pix_payment_id"])
            logger.info("PIX gerado para PagamentoLoja %s (loja %s): %s", pagamento.id, loja.slug, pix_payment_id)
            return {
                "success": True,
                "pix_copy_paste": pix_copy_paste,
                "pix_qr_code": pix_qr_code or None,
                "mercadopago_pix_payment_id": pix_payment_id,
            }
        except Exception as e:
            logger.exception("Erro ao gerar PIX para pagamento %s: %s", pagamento.id, e)
            return {"success": False, "error": str(e)}
