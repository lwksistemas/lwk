"""GET /clinica-beleza/memed/token/"""
import logging
import re

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.memed_config import memed_config as _memed_config
from clinica_beleza.memed_config import memed_credentials as _memed_credentials
from clinica_beleza.models import Professional
from clinica_beleza.permissions import CLINICA_CLINICAL

from .helpers import (
    _consultar_usuario_memed,
    _dados_clinica,
    _normalizar_status_memed,
    mensagem_falha_token_memed,
    prescritor_demo_homologacao,
)

logger = logging.getLogger(__name__)


class MemedTokenView(APIView):
    """GET /clinica-beleza/memed/token/?professional=<id>&uf=<UF>

    Retorna o token do prescritor (para o data-token do script da Memed), a URL do
    script e o ambiente. Mantém api-key/secret-key no servidor.

    O token do prescritor NÃO é cacheado: a Memed exige recuperar o último token
    válido a cada chamada (o token rotaciona). A chamada ocorre só ao abrir a
    prescrição, então o custo é baixo.
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        from tenants.middleware import get_current_loja_id
        from superadmin.plano_features import loja_plano_permite_memed

        ok, err = loja_plano_permite_memed(get_current_loja_id())
        if not ok:
            return Response({"error": err}, status=status.HTTP_403_FORBIDDEN)

        env, endpoints = _memed_config()
        api_key, secret_key = _memed_credentials(env)
        if not api_key or not secret_key:
            return Response(
                {"error": "Integração Memed não configurada. Defina MEMED_API_KEY e MEMED_SECRET_KEY no servidor."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        prescritor_id = self._resolver_prescritor_id(request, env)
        if not prescritor_id:
            return Response(
                {"error": "Prescritor não identificado. Cadastre o CPF ou o CRM do profissional desta loja."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # O token do prescritor NÃO é estático (rotaciona). A doc da Memed exige
        # recuperar o último token válido a cada chamada — por isso NÃO cacheamos o
        # token. A chamada é feita só ao abrir a prescrição (baixo volume), então o
        # custo é aceitável e evita servir um token vencido (que impede prescrever).
        resp = _consultar_usuario_memed(endpoints, api_key, secret_key, prescritor_id)
        if resp is None:
            return Response(
                {"error": "Não foi possível conectar à Memed. Tente novamente."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        demo = prescritor_demo_homologacao(
            env,
            resp.status_code,
            prescritor_id,
            getattr(settings, "MEMED_PRESCRITOR_ID", "") or "",
        )
        if demo:
            logger.info(
                "Memed homologação: prescritor da loja %s não existe; usando prescritor de demonstração",
                prescritor_id,
            )
            prescritor_id = demo
            resp = _consultar_usuario_memed(endpoints, api_key, secret_key, prescritor_id)
            if resp is None:
                return Response(
                    {"error": "Não foi possível conectar à Memed. Tente novamente."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        if resp.status_code == 404:
            return Response(
                {"error": f"Prescritor não encontrado na Memed (id: {prescritor_id}). "
                          "Cadastre o profissional na Memed antes de prescrever."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not resp.ok:
            logger.warning("Memed: resposta %s — %s", resp.status_code, resp.text[:400])
            return Response(
                {"error": mensagem_falha_token_memed(env, resp.status_code, resp.text or "")},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        attrs = ((resp.json() or {}).get("data") or {}).get("attributes") or {}
        token = attrs.get("token")
        if not token:
            return Response(
                {"error": "Token do prescritor não retornado pela Memed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Prescritor "Inativo" na Memed não consegue prescrever (a busca de
        # medicamentos volta vazia e o editor abre sem funcionar). Bloqueamos aqui
        # com uma mensagem clara em vez de abrir um widget inutilizável.
        # "Em análise" e "Ativo" liberam a prescrição (confirmação do suporte Memed).
        status_prescritor = _normalizar_status_memed(attrs.get("status"))
        if status_prescritor == "inativo":
            return Response(
                {
                    "error": (
                        "O cadastro deste profissional na Memed está inativo e ainda não "
                        "libera a emissão de receitas. O cadastro já foi enviado para ativação; "
                        "assim que a Memed liberar (status 'Em análise' ou 'Ativo'), a prescrição "
                        "funcionará normalmente. Se persistir, contate o suporte."
                    ),
                    "memed_status": attrs.get("status") or "Inativo",
                },
                status=status.HTTP_409_CONFLICT,
            )

        payload = {
            "token": token,
            "script_url": endpoints["script"],
            "environment": env,
            "prescritor": {
                "nome": attrs.get("nome", ""),
                "sobrenome": attrs.get("sobrenome", ""),
                "crm": attrs.get("crm", ""),
                "uf": attrs.get("uf", ""),
                "status": attrs.get("status") or "",
                "terms_accepted": bool(attrs.get("terms_accepted")),
            },
            "clinica": _dados_clinica(request),
        }
        # Sem cache do token: sempre retornamos o token recém-obtido da Memed.
        return Response(payload)

    def _resolver_prescritor_por_professional(self, professional_id, request) -> str:
        """Resolve prescritor via registro profissional do Professional."""
        prof = Professional.objects.filter(pk=professional_id).first()
        if not prof:
            return ""
        cpf_digitos = "".join(ch for ch in (prof.cpf or "") if ch.isdigit())
        if len(cpf_digitos) == 11:
            return cpf_digitos
        if not prof.registro_profissional:
            return ""
        raw = prof.registro_profissional.strip().upper()
        so_digitos = "".join(ch for ch in raw if ch.isdigit())
        if len(so_digitos) == 11 and not prof.conselho_uf:
            return so_digitos
        match_uf = re.search(r"[-\s/]*([A-Z]{2})\s*$", raw)
        uf_campo = match_uf.group(1) if match_uf else ""
        registro = "".join(ch for ch in raw if ch.isalnum())
        if uf_campo and registro.endswith(uf_campo):
            registro = registro[: -len(uf_campo)]
        uf = (
            request.query_params.get("uf")
            or (prof.conselho_uf or "")
            or uf_campo
            or getattr(settings, "MEMED_DEFAULT_UF", "")
            or ""
        ).strip().upper()
        if registro:
            return f"{registro}{uf}" if uf else registro
        return ""

    def _resolver_prescritor_id(self, request, env="integration"):
        """Resolve o identificador do prescritor na Memed (CPF, external_id ou registro+UF)."""
        from tenants.middleware import get_current_loja_id

        em_loja = bool(get_current_loja_id())

        # 1) Identificador explícito na query (?prescritor=...) tem prioridade,
        #    MAS apenas fora de contexto de loja (teste/superadmin). Dentro de um
        #    tenant, aceitar um prescritor arbitrário permitiria obter o token de
        #    prescritor de outra clínica — o vínculo deve vir sempre do Professional
        #    da loja atual (etapa 2, via ?professional=).
        explicit = (request.query_params.get("prescritor") or "").strip()
        if explicit and not em_loja:
            return explicit

        # 2) Registro profissional (CRM) do profissional da consulta + UF.
        #    O campo registro_profissional pode vir como "016964-SP" (CRM-UF);
        #    extraímos a UF do próprio campo, com fallback para ?uf ou MEMED_DEFAULT_UF.
        professional_id = request.query_params.get("professional")
        if professional_id:
            prescritor = self._resolver_prescritor_por_professional(professional_id, request)
            if prescritor:
                return prescritor

        # 3) Prescritor padrão só fora de loja (teste/superadmin).
        # Em tenant nunca usar MEMED_PRESCRITOR_ID — seria o prescritor de outra clínica.
        if em_loja:
            return ""

        default_id = ""
        if env == "production":
            default_id = getattr(settings, "MEMED_PRESCRITOR_ID_PROD", "") or ""
        default_id = default_id or getattr(settings, "MEMED_PRESCRITOR_ID", "")
        return (default_id or "").strip()
