"""GET /clinica-beleza/memed/status/ e verificar-cpf-paciente."""
import re

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.memed_config import memed_config as _memed_config
from clinica_beleza.memed_config import memed_credentials as _memed_credentials
from clinica_beleza.memed_service import status_prescritor_para_diagnostico
from clinica_beleza.permissions import CLINICA_CLINICAL
from django.conf import settings


class MemedVerificarCpfPacienteView(APIView):
    """GET /clinica-beleza/memed/verificar-cpf-paciente/?cpf=<cpf>

    Retorna {"conflito_prescritor": bool}. Quando o CPF de um paciente também é
    de um prescritor na Memed, o editor quebra ao gerar a receita
    (verifyIdentifyDataToNavigate). O frontend usa isso para omitir o CPF do
    paciente nesse caso, evitando o conflito de identificação.
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        from tenants.middleware import get_current_loja_id
        from superadmin.plano_features import loja_plano_permite_memed
        from clinica_beleza.memed_service import cpf_e_prescritor_na_memed

        ok, err = loja_plano_permite_memed(get_current_loja_id())
        if not ok:
            return Response({"error": err}, status=status.HTTP_403_FORBIDDEN)

        cpf = re.sub(r"\D", "", request.query_params.get("cpf") or "")
        if len(cpf) != 11:
            # Sem CPF válido não há conflito a checar.
            return Response({"conflito_prescritor": False})
        return Response({"conflito_prescritor": cpf_e_prescritor_na_memed(cpf)})


class MemedStatusView(APIView):
    """GET /clinica-beleza/memed/status/
    Diagnóstico: ambiente, credenciais e timbrado (sem expor secrets).
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        from tenants.middleware import get_current_loja_id
        from superadmin.plano_features import loja_plano_permite_memed

        ok, err = loja_plano_permite_memed(get_current_loja_id())
        if not ok:
            return Response({"error": err}, status=status.HTTP_403_FORBIDDEN)

        from clinica_beleza.models import MemedTimbrado, Professional

        env, endpoints = _memed_config()
        api_key, secret_key = _memed_credentials(env)
        timbrado = MemedTimbrado.objects.first()
        profs_cpf = list(
            Professional.objects.filter(is_active=True).exclude(cpf__isnull=True).exclude(cpf="").order_by("nome")
        )
        prescritores = []
        for p in profs_cpf:
            if len("".join(ch for ch in (p.cpf or "") if ch.isdigit())) != 11:
                continue
            prescritores.append(status_prescritor_para_diagnostico(p))
        profs_com_cpf = len(prescritores)
        prescritores_liberados = sum(1 for item in prescritores if item.get("pode_prescrever"))

        prod_keys = bool(
            getattr(settings, "MEMED_API_KEY_PROD", "") and getattr(settings, "MEMED_SECRET_KEY_PROD", ""),
        )
        clinica_conectada = env == "production" and bool(api_key and secret_key) and profs_com_cpf > 0

        return Response({
            "environment": env,
            "api_base": endpoints["api"],
            "credentials_configured": bool(api_key and secret_key),
            "production_keys_configured": prod_keys,
            "timbrado": {
                "tem_timbrado": bool(timbrado and timbrado.pdf),
                "pdf_nome": timbrado.pdf_nome if timbrado else None,
                "updated_at": timbrado.updated_at.isoformat() if timbrado and timbrado.updated_at else None,
            },
            "profissionais_com_cpf": profs_com_cpf,
            "prescritores": prescritores,
            "prescritores_liberados": prescritores_liberados,
            "ready_for_production": clinica_conectada and prescritores_liberados > 0,
        })
