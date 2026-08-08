"""Persistência de regras de comissão por profissional."""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import status

from .models import Convenio, LocalAtendimento, Procedure, ProfessionalCommission
from .serializers import ProfessionalCommissionSerializer

logger = logging.getLogger(__name__)


def salvar_comissoes_profissional(professional, itens):
    """Substitui todas as comissões do profissional.

    Returns:
        (data, None) em sucesso — lista serializada
        (None, (error_payload, http_status)) em validação/erro
    """
    if not isinstance(itens, list):
        return None, ({"error": "Envie uma lista de comissões."}, status.HTTP_400_BAD_REQUEST)

    locais_consulta_vistos = set()
    procedimentos_convenio_vistos = set()
    local_ids = set()
    procedure_ids = set()
    convenio_ids = set()
    rows = []

    for item in itens:
        if not isinstance(item, dict):
            return None, ({"error": "Cada comissão deve ser um objeto."}, status.HTTP_400_BAD_REQUEST)
        tipo = item.get("tipo")
        modo = item.get("modo") or "percentual"
        if tipo not in ("consulta", "procedimento"):
            return None, ({"tipo": "Tipo inválido."}, status.HTTP_400_BAD_REQUEST)
        if modo not in ("percentual", "fixo"):
            return None, ({"modo": "Modo inválido."}, status.HTTP_400_BAD_REQUEST)
        try:
            valor = Decimal(str(item.get("valor") if item.get("valor") is not None else 0))
        except (InvalidOperation, TypeError, ValueError):
            return None, ({"valor": "Valor inválido."}, status.HTTP_400_BAD_REQUEST)

        if tipo == "consulta":
            local_id = item.get("local_atendimento")
            if not local_id:
                return None, (
                    {"local_atendimento": "Informe o local para cada comissão de consulta."},
                    status.HTTP_400_BAD_REQUEST,
                )
            try:
                local_id = int(local_id)
            except (TypeError, ValueError):
                return None, ({"local_atendimento": "Local inválido."}, status.HTTP_400_BAD_REQUEST)
            if item.get("procedure") or item.get("convenio"):
                return None, (
                    {"tipo": "Comissão de consulta não vincula procedimento/convênio."},
                    status.HTTP_400_BAD_REQUEST,
                )
            if local_id in locais_consulta_vistos:
                return None, (
                    {"local_atendimento": "Não repita o mesmo local de atendimento."},
                    status.HTTP_400_BAD_REQUEST,
                )
            locais_consulta_vistos.add(local_id)
            local_ids.add(local_id)
            rows.append({
                "tipo": tipo,
                "modo": modo,
                "valor": valor,
                "procedure_id": None,
                "convenio_id": None,
                "local_atendimento_id": local_id,
            })
        else:
            proc_id = item.get("procedure")
            conv_id = item.get("convenio")
            if not proc_id:
                return None, ({"procedure": "Procedimento obrigatório."}, status.HTTP_400_BAD_REQUEST)
            if not conv_id:
                return None, (
                    {"convenio": "Informe o convênio para cada comissão de procedimento."},
                    status.HTTP_400_BAD_REQUEST,
                )
            if item.get("local_atendimento"):
                return None, (
                    {"local_atendimento": "Não use local em comissão de procedimento."},
                    status.HTTP_400_BAD_REQUEST,
                )
            try:
                proc_id = int(proc_id)
                conv_id = int(conv_id)
            except (TypeError, ValueError):
                return None, (
                    {"error": "Procedimento ou convênio inválido."},
                    status.HTTP_400_BAD_REQUEST,
                )
            chave = (proc_id, conv_id)
            if chave in procedimentos_convenio_vistos:
                return None, (
                    {"convenio": "Não repita o mesmo procedimento para o mesmo convênio."},
                    status.HTTP_400_BAD_REQUEST,
                )
            procedimentos_convenio_vistos.add(chave)
            procedure_ids.add(proc_id)
            convenio_ids.add(conv_id)
            rows.append({
                "tipo": tipo,
                "modo": modo,
                "valor": valor,
                "procedure_id": proc_id,
                "convenio_id": conv_id,
                "local_atendimento_id": None,
            })

    if local_ids:
        found = set(LocalAtendimento.objects.filter(id__in=local_ids).values_list("id", flat=True))
        if found != local_ids:
            return None, (
                {"local_atendimento": "Local de atendimento inválido."},
                status.HTTP_400_BAD_REQUEST,
            )
    if procedure_ids:
        found = set(Procedure.objects.filter(id__in=procedure_ids).values_list("id", flat=True))
        if found != procedure_ids:
            return None, ({"procedure": "Procedimento inválido."}, status.HTTP_400_BAD_REQUEST)
    if convenio_ids:
        found = set(Convenio.objects.filter(id__in=convenio_ids).values_list("id", flat=True))
        if found != convenio_ids:
            return None, ({"convenio": "Convênio inválido."}, status.HTTP_400_BAD_REQUEST)

    loja_id = getattr(professional, "loja_id", None)
    if not loja_id:
        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
    if not loja_id:
        return None, ({"error": "Contexto de loja ausente."}, status.HTTP_400_BAD_REQUEST)

    pk = professional.pk
    with transaction.atomic():
        ProfessionalCommission.objects.filter(professional_id=pk).delete()
        if rows:
            ProfessionalCommission.objects.bulk_create([
                ProfessionalCommission(
                    professional_id=pk,
                    loja_id=loja_id,
                    tipo=row["tipo"],
                    modo=row["modo"],
                    valor=row["valor"],
                    procedure_id=row["procedure_id"],
                    convenio_id=row["convenio_id"],
                    local_atendimento_id=row["local_atendimento_id"],
                    is_active=True,
                )
                for row in rows
            ])

    qs = ProfessionalCommission.objects.filter(
        professional_id=pk, is_active=True,
    ).select_related("procedure", "convenio", "local_atendimento").order_by(
        "tipo", "procedure__nome", "convenio__nome",
    )
    return ProfessionalCommissionSerializer(qs, many=True).data, None
