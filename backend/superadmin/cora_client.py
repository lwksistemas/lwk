"""Cliente da API Cora (Integração Direta, mTLS) para boleto de assinatura."""

from __future__ import annotations

import logging
import re
import tempfile
import uuid
from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import requests

logger = logging.getLogger(__name__)

CORA_BASE_URL = "https://matls-clients.api.cora.com.br"
VALOR_MINIMO_CENTAVOS = 500


def centavos(valor) -> int:
    quantizado = (Decimal(str(valor)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(quantizado)


def documento_cliente(cpf_cnpj: str) -> dict[str, str]:
    digitos = re.sub(r"\D", "", cpf_cnpj or "")
    tipo = "CPF" if len(digitos) <= 11 else "CNPJ"
    return {"identity": digitos, "type": tipo}


def montar_fatura(loja, valor, due_date: str, code: str) -> dict[str, Any]:
    """Corpo do POST /v2/invoices. Valores em centavos. Pix no boleto quando a conta tem chave."""
    nome = (loja.nome or "Loja")[:60]
    email = (getattr(getattr(loja, "owner", None), "email", "") or "")[:60]
    descricao = f"Assinatura LWK — {loja.nome}"[:100]
    corpo: dict[str, Any] = {
        "code": code[:64],
        "customer": {
            "name": nome,
            "document": documento_cliente(getattr(loja, "cpf_cnpj", "") or ""),
        },
        "services": [{
            "name": "Assinatura LWK"[:60],
            "description": descricao,
            "amount": centavos(valor),
        }],
        "payment_terms": {"due_date": due_date},
        "payment_forms": ["BANK_SLIP", "PIX"],
    }
    if email:
        corpo["customer"]["email"] = email
    endereco = _endereco(loja)
    if endereco:
        corpo["customer"]["address"] = endereco
    return corpo


def _endereco(loja) -> dict[str, str] | None:
    cep = re.sub(r"\D", "", getattr(loja, "cep", "") or "")[:8]
    rua = (getattr(loja, "logradouro", "") or "").strip()
    numero = (getattr(loja, "numero", "") or "").strip() or "S/N"
    bairro = (getattr(loja, "bairro", "") or "").strip()
    cidade = (getattr(loja, "cidade", "") or "").strip()
    uf = (getattr(loja, "uf", "") or "").strip().upper()[:2]
    if not (cep and rua and bairro and cidade and uf):
        return None
    return {
        "street": rua[:100],
        "number": numero[:20],
        "district": bairro[:60],
        "city": cidade[:60],
        "state": uf,
        "complement": (getattr(loja, "complemento", "") or "S/N")[:100],
        "zip_code": cep,
    }


def interpretar_fatura(data: dict[str, Any]) -> dict[str, Any]:
    boleto = ((data.get("payment_options") or {}).get("bank_slip") or {})
    pix = data.get("pix") or {}
    total = data.get("total_amount") or 0
    return {
        "success": True,
        "payment_id": data.get("id") or "",
        "status": data.get("status") or "",
        "boleto_url": boleto.get("url") or "",
        "linha_digitavel": boleto.get("digitable") or "",
        "pix_copy_paste": pix.get("emv") or "",
        "value": Decimal(total) / Decimal(100) if total else Decimal(0),
    }


class CoraClient:
    def __init__(self, client_id: str, certificate_pem: str, private_key_pem: str, base_url: str = CORA_BASE_URL):
        self.client_id = (client_id or "").strip()
        self.certificate_pem = certificate_pem or ""
        self.private_key_pem = private_key_pem or ""
        self.base_url = base_url.rstrip("/")
        self._token = ""

    @contextmanager
    def _arquivos_mtls(self):
        cert = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False)
        key = tempfile.NamedTemporaryFile("w", suffix=".key", delete=False)
        try:
            cert.write(self.certificate_pem)
            key.write(self.private_key_pem)
            cert.close()
            key.close()
            yield cert.name, key.name
        finally:
            import os
            for path in (cert.name, key.name):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _token_acesso(self, session: requests.Session) -> str:
        if self._token:
            return self._token
        with self._arquivos_mtls() as (cert_path, key_path):
            resposta = session.post(
                f"{self.base_url}/token",
                data={"grant_type": "client_credentials", "client_id": self.client_id},
                cert=(cert_path, key_path),
                timeout=30,
            )
        if resposta.status_code >= 400:
            logger.error("Cora recusou o token: HTTP %s", resposta.status_code)
            raise RuntimeError("Não foi possível autenticar na Cora.")
        self._token = (resposta.json() or {}).get("access_token") or ""
        if not self._token:
            raise RuntimeError("A Cora não devolveu o token de acesso.")
        return self._token

    def _pedir(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        with self._arquivos_mtls() as (cert_path, key_path):
            session = requests.Session()
            token = self._token_acesso(session)
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            headers.update(kwargs.pop("headers", {}))
            resposta = session.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                cert=(cert_path, key_path),
                timeout=40,
                **kwargs,
            )
        if resposta.status_code >= 400:
            logger.error("Cora %s %s HTTP %s", method, path, resposta.status_code)
            raise RuntimeError("A Cora recusou a cobrança.")
        if not resposta.content:
            return {}
        return resposta.json()

    def testar(self) -> dict[str, Any]:
        self._token = ""
        with self._arquivos_mtls() as (cert_path, key_path):
            resposta = requests.post(
                f"{self.base_url}/token",
                data={"grant_type": "client_credentials", "client_id": self.client_id},
                cert=(cert_path, key_path),
                timeout=30,
            )
        if resposta.status_code >= 400:
            return {"success": False, "error": "A Cora não aceitou o certificado."}
        return {"success": True, "message": "Conexão com a Cora ok."}

    def criar_boleto(self, loja, valor, due_date: str, code: str) -> dict[str, Any]:
        corpo = montar_fatura(loja, valor, due_date, code)
        data = self._pedir(
            "POST",
            "/v2/invoices",
            json=corpo,
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        return interpretar_fatura(data)

    def consultar_fatura(self, invoice_id: str) -> dict[str, Any]:
        data = self._pedir("GET", f"/v2/invoices/{invoice_id}")
        return interpretar_fatura(data)

    def cancelar_fatura(self, invoice_id: str) -> None:
        self._pedir("DELETE", f"/v2/invoices/{invoice_id}")

    def registrar_webhook(self, url: str) -> None:
        self._pedir(
            "POST",
            "/endpoints/",
            json={"url": url, "resource": "invoice", "trigger": "paid"},
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
