"""Views de Profissionais e Horários de Trabalho — Clínica da Beleza
"""
import json
import logging
from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Appointment,
    BloqueioHorario,
    Convenio,
    HorarioTrabalhoProfissional,
    LocalAtendimento,
    Procedure,
    Professional,
    ProfessionalCommission,
)
from .pagination import paginate_queryset
from .permissions import CLINICA_ADMIN, CLINICA_AGENDA
from .serializers import (
    HorarioTrabalhoProfissionalSerializer,
    ProfessionalCommissionSerializer,
    ProfessionalCreateWithUserSerializer,
    ProfessionalSerializer,
)
from .utils import LojaContextHelper
from .views_base import GetObjectMixin, map_field_names

logger = logging.getLogger(__name__)


def _sync_memed(professional):
    """Dispara o auto-cadastro do prescritor na Memed (best-effort; nunca quebra o save)."""
    try:
        from .memed_service import sincronizar_prescritor
        resultado = sincronizar_prescritor(professional)
        if resultado.get("ok") is False and resultado.get("status"):
            logger.info("Memed auto-cadastro prof %s: %s", getattr(professional, "id", None), resultado)
    except Exception as e:  # noqa: BLE001 — sincronização é opcional.
        logger.warning("Memed auto-cadastro ignorado (prof %s): %s", getattr(professional, "id", None), e)


_PROFESSIONAL_FIELD_MAP = {
    "name": "nome",
    "specialty": "especialidade",
    "phone": "telefone",
    "active": "is_active",
}

# Campos operacionais que o profissional-admin da loja pode alterar (PUT parcial).
_OWNER_PROFESSIONAL_EDITABLE_FIELDS = frozenset({
    "tempo_consulta_minutos",
    "registro_profissional", "conselho", "conselho_uf",
    "especialidade", "telefone", "email",
    "cpf", "data_nascimento", "sexo",
    "nome", "specialty", "name", "phone",
    "registro", "uf", "is_profissional",
    "is_active", "active",
})

def _map_professional_data(raw_data):
    """Normaliza campos legados (inglês) para os nomes do model."""
    data = raw_data.copy() if hasattr(raw_data, "copy") else dict(raw_data)
    data = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in data.items()}

    def _empty_to_none(v):
        if isinstance(v, list):
            v = v[0] if len(v) == 1 else None
        if isinstance(v, str) and (v.strip() == "" or v.strip().lower() == "null"):
            return None
        return v

    data = map_field_names(data, _PROFESSIONAL_FIELD_MAP)

    for key in ("email", "telefone", "data_nascimento", "sexo"):
        if key in data:
            data[key] = _empty_to_none(data[key])
    if "telefone" in data and data["telefone"] is None:
        data["telefone"] = ""

    for key in ("nome", "especialidade"):
        if key in data and isinstance(data[key], str):
            data[key] = data[key].strip() or None

    if "is_active" in data and isinstance(data["is_active"], str):
        data["is_active"] = data["is_active"].strip().lower() in ("1", "true", "yes", "on")

    if "is_profissional" in data and isinstance(data["is_profissional"], str):
        data["is_profissional"] = data["is_profissional"].strip().lower() in ("1", "true", "yes", "on")

    for key in ("criar_acesso", "perfil"):
        data.pop(key, None)

    return data


class ProfessionalListView(APIView):
    """Listagem e criação de profissionais
    GET /clinica-beleza/professionals/
    POST /clinica-beleza/professionals/
    """

    permission_classes = CLINICA_ADMIN

    def get_permissions(self):
        if self.request.method == "GET":
            scheduling = self.request.query_params.get("scheduling", "").lower() == "true"
            if scheduling:
                return [perm() for perm in CLINICA_AGENDA]
        return [perm() for perm in CLINICA_ADMIN]

    def get(self, request):
        active_only = request.query_params.get("active", "true").lower() == "true"
        with_schedule = request.query_params.get("with_schedule", "false").lower() == "true"

        queryset = Professional.objects.all().order_by("nome")
        if active_only:
            queryset = queryset.filter(is_active=True)
        # Filtrar apenas profissionais que atendem (is_profissional=True)
        # para agenda e agendamentos
        scheduling = request.query_params.get("scheduling", "").lower() == "true"
        if with_schedule or scheduling:
            queryset = queryset.filter(is_profissional=True)

        # Na agenda: exibir apenas profissionais com horário de trabalho ativo
        if with_schedule or scheduling:
            queryset = queryset.filter(
                id__in=HorarioTrabalhoProfissional.objects.filter(ativo=True)
                .values_list("professional_id", flat=True).distinct(),
            )

        admin_professional_ids = LojaContextHelper.get_admin_professional_ids()
        owner_professional_id = LojaContextHelper.get_owner_professional_id()

        # Na agenda: administradores com is_profissional=False não aparecem
        if (with_schedule or scheduling) and admin_professional_ids:
            admin_not_professional = Professional.objects.filter(
                id__in=admin_professional_ids, is_profissional=False,
            ).values_list("id", flat=True)
            queryset = queryset.exclude(id__in=admin_not_professional)

        return paginate_queryset(
            queryset,
            request,
            ProfessionalSerializer,
            serializer_context={
                "admin_professional_ids": admin_professional_ids,
                "owner_professional_id": owner_professional_id,
            },
        )

    def post(self, request):
        raw = request.data if isinstance(request.data, dict) else dict(request.data)

        # Criar com acesso (usuário Django) — serializer usa campos em inglês
        data = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in raw.items()}
        if data.get("criar_acesso") and data.get("email"):
            serializer = ProfessionalCreateWithUserSerializer(data=data)
            if serializer.is_valid():
                professional = serializer.save()
                _sync_memed(professional)
                return Response(
                    ProfessionalSerializer(professional).data,
                    status=status.HTTP_201_CREATED,
                )
            err_payload = dict(serializer.errors)
            for v in serializer.errors.values():
                msg = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else None)
                if msg:
                    err_payload["detail"] = msg
                    break
            return Response(err_payload, status=status.HTTP_400_BAD_REQUEST)

        payload = _map_professional_data(raw)
        name_val = (payload.get("nome") or "").strip()
        specialty_val = (payload.get("especialidade") or "").strip()
        if not name_val or not specialty_val:
            missing = [f for f, v in [("nome", name_val), ("especialidade", specialty_val)] if not v]
            return Response({"detail": f'Preencha {", ".join(missing)}.'}, status=status.HTTP_400_BAD_REQUEST)

        payload["nome"] = name_val
        payload["especialidade"] = specialty_val
        payload.setdefault("is_active", True)

        serializer = ProfessionalSerializer(data=payload)
        if serializer.is_valid():
            professional = serializer.save()
            _sync_memed(professional)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error("POST professionals 400 payload=%s errors=%s", payload, json.dumps(serializer.errors, ensure_ascii=False))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/professionals/<id>/  PUT  DELETE"""

    permission_classes = CLINICA_ADMIN
    model_class = Professional
    not_found_message = "Profissional não encontrado"

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        admin_professional_ids = LojaContextHelper.get_admin_professional_ids()
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        return Response(ProfessionalSerializer(obj, context={
            "admin_professional_ids": admin_professional_ids,
            "owner_professional_id": owner_professional_id,
        }).data)

    def put(self, request, pk):
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        data = _map_professional_data(request.data)
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            # Bloquear desativação do owner
            if "is_active" in data and data["is_active"] is False:
                return Response(
                    {"error": "O administrador vinculado à loja não pode ser desativado."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            keys = set(data.keys())
            if not keys or not keys.issubset(_OWNER_PROFESSIONAL_EDITABLE_FIELDS):
                return Response(
                    {"error": "O administrador vinculado à loja não pode ser editado."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        obj, err = self.object_or_404(pk)
        if err:
            return err
        serializer = ProfessionalSerializer(obj, data=data, partial=True)
        if serializer.is_valid():
            professional = serializer.save()
            _sync_memed(professional)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            return Response({"error": "O administrador vinculado à loja não pode ser excluído."}, status=status.HTTP_403_FORBIDDEN)
        obj, err = self.object_or_404(pk)
        if err:
            return err
        from django.utils import timezone
        agora = timezone.now()

        # Exclui apenas agendamentos futuros SEM consulta finalizada ou em andamento
        future_appointments = Appointment.objects.filter(professional=obj, date__gte=agora)
        safe_to_delete = future_appointments.exclude(
            consulta__status__in=("COMPLETED", "IN_PROGRESS"),
        )
        count = safe_to_delete.count()
        safe_to_delete.delete()

        HorarioTrabalhoProfissional.objects.filter(professional=obj).delete()
        BloqueioHorario.objects.filter(professional=obj).delete()
        obj.is_active = False
        obj.save()
        return Response({
            "message": f"Profissional desativado. {count} agendamento(s) futuro(s) excluído(s).",
        }, status=status.HTTP_200_OK)


class HorarioTrabalhoProfissionalView(GetObjectMixin, APIView):
    """Dias e horários de trabalho do profissional.
    GET /clinica-beleza/professionals/<id>/horarios-trabalho/
    PUT /clinica-beleza/professionals/<id>/horarios-trabalho/
    """

    permission_classes = CLINICA_ADMIN
    model_class = Professional
    not_found_message = "Profissional não encontrado"

    def get(self, request, pk):
        professional, err = self.object_or_404(pk)
        if err:
            return err
        queryset = HorarioTrabalhoProfissional.objects.filter(professional_id=pk).order_by("dia_semana")
        return Response(HorarioTrabalhoProfissionalSerializer(queryset, many=True).data)

    def put(self, request, pk):
        professional, err = self.object_or_404(pk)
        if err:
            return err
        if not isinstance(request.data, list):
            return Response(
                {"error": 'Envie uma lista de horários. Ex.: [{"dia_semana": 0, "hora_entrada": "08:00", "hora_saida": "18:00", "ativo": true}]'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        HorarioTrabalhoProfissional.objects.filter(professional_id=pk).delete()
        created = []
        for item in request.data:
            serializer = HorarioTrabalhoProfissionalSerializer(data=dict(item))
            if serializer.is_valid():
                created.append(HorarioTrabalhoProfissionalSerializer(serializer.save(professional=professional)).data)
            else:
                HorarioTrabalhoProfissional.objects.filter(professional_id=pk).delete()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(created, status=status.HTTP_200_OK)


class ProfessionalCommissionView(GetObjectMixin, APIView):
    """GET  /clinica-beleza/professionals/<id>/comissoes/ — lista comissões do profissional.
    POST /clinica-beleza/professionals/<id>/comissoes/ — cria/atualiza comissões (recebe lista).
    """

    permission_classes = CLINICA_ADMIN
    model_class = Professional
    not_found_message = "Profissional não encontrado"

    def get(self, request, pk):
        professional, err = self.object_or_404(pk)
        if err:
            return err
        try:
            qs = ProfessionalCommission.objects.filter(
                professional_id=pk, is_active=True,
            ).select_related("procedure", "convenio", "local_atendimento").order_by(
                "tipo", "procedure__nome", "convenio__nome",
            )
            return Response(ProfessionalCommissionSerializer(qs, many=True).data)
        except Exception:
            logger.exception("Erro ao listar comissões do profissional %s", pk)
            return Response(
                {"error": "Erro ao carregar comissões do profissional."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, pk):
        """Recebe uma lista de comissões. Substitui todas as existentes."""
        professional, err = self.object_or_404(pk)
        if err:
            return err

        if not isinstance(request.data, list):
            return Response(
                {"error": "Envie uma lista de comissões."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            return self._salvar_comissoes(pk, professional, request.data)
        except Exception:
            logger.exception("Erro ao salvar comissões do profissional %s", pk)
            return Response(
                {"error": "Erro ao salvar comissões. Verifique os dados e tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _salvar_comissoes(self, pk, professional, itens):
        """Substitui comissões com delete + bulk_create (evita N inserts/serializer/Loja.exists)."""
        locais_consulta_vistos = set()
        procedimentos_convenio_vistos = set()
        local_ids = set()
        procedure_ids = set()
        convenio_ids = set()
        rows = []

        for item in itens:
            if not isinstance(item, dict):
                return Response(
                    {"error": "Cada comissão deve ser um objeto."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            tipo = item.get("tipo")
            modo = item.get("modo") or "percentual"
            if tipo not in ("consulta", "procedimento"):
                return Response({"tipo": "Tipo inválido."}, status=status.HTTP_400_BAD_REQUEST)
            if modo not in ("percentual", "fixo"):
                return Response({"modo": "Modo inválido."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                valor = Decimal(str(item.get("valor") if item.get("valor") is not None else 0))
            except (InvalidOperation, TypeError, ValueError):
                return Response({"valor": "Valor inválido."}, status=status.HTTP_400_BAD_REQUEST)

            if tipo == "consulta":
                local_id = item.get("local_atendimento")
                if not local_id:
                    return Response(
                        {"local_atendimento": "Informe o local para cada comissão de consulta."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                try:
                    local_id = int(local_id)
                except (TypeError, ValueError):
                    return Response(
                        {"local_atendimento": "Local inválido."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if item.get("procedure") or item.get("convenio"):
                    return Response(
                        {"tipo": "Comissão de consulta não vincula procedimento/convênio."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if local_id in locais_consulta_vistos:
                    return Response(
                        {"local_atendimento": "Não repita o mesmo local de atendimento."},
                        status=status.HTTP_400_BAD_REQUEST,
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
                    return Response(
                        {"procedure": "Procedimento obrigatório."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not conv_id:
                    return Response(
                        {"convenio": "Informe o convênio para cada comissão de procedimento."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if item.get("local_atendimento"):
                    return Response(
                        {"local_atendimento": "Não use local em comissão de procedimento."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                try:
                    proc_id = int(proc_id)
                    conv_id = int(conv_id)
                except (TypeError, ValueError):
                    return Response(
                        {"error": "Procedimento ou convênio inválido."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                chave = (proc_id, conv_id)
                if chave in procedimentos_convenio_vistos:
                    return Response(
                        {"convenio": "Não repita o mesmo procedimento para o mesmo convênio."},
                        status=status.HTTP_400_BAD_REQUEST,
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
            found = set(
                LocalAtendimento.objects.filter(id__in=local_ids).values_list("id", flat=True),
            )
            if found != local_ids:
                return Response(
                    {"local_atendimento": "Local de atendimento inválido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if procedure_ids:
            found = set(
                Procedure.objects.filter(id__in=procedure_ids).values_list("id", flat=True),
            )
            if found != procedure_ids:
                return Response(
                    {"procedure": "Procedimento inválido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if convenio_ids:
            found = set(
                Convenio.objects.filter(id__in=convenio_ids).values_list("id", flat=True),
            )
            if found != convenio_ids:
                return Response(
                    {"convenio": "Convênio inválido."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        loja_id = getattr(professional, "loja_id", None)
        if not loja_id:
            from tenants.middleware import get_current_loja_id

            loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {"error": "Contexto de loja ausente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        return Response(
            ProfessionalCommissionSerializer(qs, many=True).data,
            status=status.HTTP_200_OK,
        )
