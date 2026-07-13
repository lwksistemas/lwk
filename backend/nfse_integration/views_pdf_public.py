"""Download público de PDF da NFS-e (token assinado — uso no envio WhatsApp)."""
import logging
import time

from django.conf import settings
from django.core.signing import BadSignature, dumps, loads
from django.http import HttpResponse
from django.views import View

from core.db_config import ensure_loja_database_config
from tenants.middleware import set_current_loja_id, set_current_tenant_db

from .models import NFSe
from .pdf_download import resolver_download_pdf_loja

logger = logging.getLogger(__name__)

TOKEN_MAX_AGE = 3600


def criar_token_pdf_nfse(nfse_id: int, loja_id: int) -> str:
    payload = {
        "id": nfse_id,
        "loja_id": loja_id,
        "exp": int(time.time()) + TOKEN_MAX_AGE,
    }
    return dumps(payload)


def _verificar_token(token: str) -> dict | None:
    try:
        payload = loads(token)
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except (BadSignature, TypeError, ValueError):
        return None


class NFSePdfPublicView(View):
    """GET /api/nfse/documento-pdf/?token=xxx
    Endpoint público para Evolution/Meta baixarem o PDF ao enviar por WhatsApp.
    """

    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return HttpResponse("Token ausente", status=400)

        payload = _verificar_token(token)
        if not payload:
            return HttpResponse("Token inválido ou expirado", status=403)

        nfse_id = payload.get("id")
        loja_id = payload.get("loja_id")
        if not nfse_id or not loja_id:
            return HttpResponse("Token inválido", status=403)

        try:
            from superadmin.models import Loja

            loja = Loja.objects.using("default").filter(id=loja_id).first()
            if not loja:
                return HttpResponse("Loja não encontrada", status=404)

            db_name = getattr(loja, "database_name", None) or f'loja_{getattr(loja, "slug", "")}'
            set_current_loja_id(loja_id)
            ensure_loja_database_config(db_name, conn_max_age=0)
            set_current_tenant_db(db_name if db_name in settings.DATABASES else "default")

            nfse = NFSe.objects.filter(id=nfse_id, loja_id=loja_id).first()
            if not nfse:
                return HttpResponse("NFS-e não encontrada", status=404)

            resultado = resolver_download_pdf_loja(nfse, loja, loja_id)
            if resultado.tipo == "url" and resultado.url:
                from django.shortcuts import redirect
                return redirect(resultado.url)

            response = HttpResponse(resultado.conteudo_pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'inline; filename="{resultado.nome_arquivo or f"nfse_{nfse.numero_nf or nfse.id}.pdf"}"'
            )
            return response
        except Exception as exc:
            logger.exception("Erro ao servir PDF público NFS-e: %s", exc)
            return HttpResponse("Erro interno", status=500)
