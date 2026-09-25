"""Lista e abertura de consulta avulsa."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..consulta_service import criar_consulta_avulsa
from ..models import Consulta, Patient, Procedure, Professional
from ..pagination import paginate_queryset
from ..permissions import CLINICA_CLINICAL
from ..serializers import ConsultaSerializer
from ..views_base import resolve_loja_id_from_request
from .helpers import aplicar_ordem_fila_iniciar, q_consultas_aguardando_inicio


class ConsultaListView(APIView):
    """GET  /clinica-beleza/consultas/ — lista consultas.
    POST /clinica-beleza/consultas/ — abre uma consulta avulsa (sem agendamento na
         agenda) a partir do cadastro do cliente.
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        from django.db.models import Count

        from ..serializers import ConsultaListSerializer

        qs = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
            "appointment__nome_agenda",
        ).prefetch_related(
            "appointment__appointment_procedures__procedure",
            "appointment__payment_set",
            "appointment__payment_set__parcelas",
        ).annotate(
            total_evolucoes_count=Count("evolucoes"),
        ).exclude(
            status="CANCELLED",
        ).order_by("-data_inicio", "-created_at")
        if patient_id := request.query_params.get("patient"):
            qs = qs.filter(patient_id=patient_id)
        if professional_id := request.query_params.get("professional"):
            qs = qs.filter(professional_id=professional_id)
        if st := request.query_params.get("status"):
            qs = qs.filter(status=st)
        if appointment_id := request.query_params.get("appointment"):
            qs = qs.filter(appointment_id=appointment_id)
        if (request.query_params.get("fila") or "").strip().lower() == "iniciar":
            qs = aplicar_ordem_fila_iniciar(qs.filter(q_consultas_aguardando_inicio()))
        elif (request.query_params.get("ordem") or "").strip().lower() == "nome":
            qs = qs.order_by("patient__nome", "patient_id", "-data_inicio", "-id")
        return paginate_queryset(qs, request, ConsultaListSerializer)

    def post(self, request):
        patient_id = request.data.get("patient")
        professional_id = request.data.get("professional")
        procedure_id = request.data.get("procedure")
        procedures_ids = request.data.get("procedures_ids") or []
        if not patient_id:
            return Response(
                {"error": "Informe o paciente."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not professional_id:
            return Response(
                {"error": "Selecione o profissional."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not procedures_ids and not procedure_id:
            proc_list = []
        elif procedures_ids:
            proc_list = list(Procedure.objects.filter(id__in=procedures_ids, is_active=True))
            if not proc_list:
                return Response({"error": "Nenhum procedimento válido encontrado."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                proc_list = [Procedure.objects.get(pk=procedure_id)]
            except Procedure.DoesNotExist:
                return Response({"error": "Procedimento não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Cliente não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        loja_id = resolve_loja_id_from_request(request)
        if patient.loja_id != loja_id:
            return Response({"error": "Paciente não pertence a esta loja."}, status=status.HTTP_400_BAD_REQUEST)

        professional = None
        if professional_id:
            try:
                professional = Professional.objects.get(pk=professional_id)
            except Professional.DoesNotExist:
                return Response({"error": "Profissional não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        iniciar = request.data.get("iniciar", False)
        local_atendimento_id = request.data.get("local_atendimento")
        valor_consulta_override = request.data.get("valor_consulta")
        convenio_id = request.data.get("convenio")
        nome_agenda_id = request.data.get("nome_agenda")
        notes = request.data.get("notes")
        retorno_procedure_id = request.data.get("retorno_procedure")
        appointment_date = None
        if date_raw := request.data.get("date"):
            from django.utils.dateparse import parse_datetime
            appointment_date = parse_datetime(str(date_raw))
            if appointment_date is None:
                return Response({"error": "Data/hora inválida."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from django.utils import timezone

            from ..agenda_service import AgendaValidationError
            from ..convenio_service import resolver_convenio
            from ..models import LocalAtendimento, NomeAgenda
            from ..permissions import is_clinica_admin
            from ..protocolo_comercial import ProtocoloAgendaConflito, agendar_protocolo_da_selecao

            if proc_list:
                local = None
                if local_atendimento_id:
                    local = LocalAtendimento.objects.filter(pk=local_atendimento_id, is_active=True).first()
                nome_agenda = None
                if nome_agenda_id:
                    nome_agenda = NomeAgenda.objects.filter(pk=nome_agenda_id, is_active=True).first()
                resultado = agendar_protocolo_da_selecao(
                    procedures=proc_list,
                    patient=patient,
                    professional=professional,
                    local_atendimento=local,
                    data_inicio=appointment_date or timezone.now(),
                    forma_cobranca=str(request.data.get("forma_cobranca") or "").strip(),
                    request=request,
                    convenio=resolver_convenio(convenio_id, loja_id=patient.loja_id),
                    nome_agenda=nome_agenda,
                    abrir_primeira=True,
                    observacao=notes or "",
                )
                if resultado is not None:
                    consulta = Consulta.objects.select_related(
                        "patient", "professional", "procedure", "protocol", "appointment",
                    ).get(pk=resultado["consulta_id"])
                    data = ConsultaSerializer(consulta).data
                    data["sessoes_criadas"] = len(resultado["agendamentos"])
                    return Response(data, status=status.HTTP_201_CREATED)

            consulta = criar_consulta_avulsa(
                patient=patient,
                professional=professional,
                procedures=proc_list,
                loja_id=patient.loja_id,
                iniciar=bool(iniciar),
                local_atendimento_id=local_atendimento_id,
                valor_consulta=valor_consulta_override,
                convenio_id=convenio_id,
                nome_agenda_id=nome_agenda_id,
                appointment_date=appointment_date,
                notes=notes,
                retorno_procedure_id=retorno_procedure_id,
                bypass_inadimplencia=is_clinica_admin(request),
            )
        except ProtocoloAgendaConflito as exc:
            return Response(
                {"error": str(exc), "conflitos": exc.conflitos},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AgendaValidationError as exc:
            return Response({"error": exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=consulta.id)
        return Response(ConsultaSerializer(consulta).data, status=status.HTTP_201_CREATED)
