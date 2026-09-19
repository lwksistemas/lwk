"""Iniciar, receber, estornar, NFS-e, finalizar e protocolo."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..consulta_service import (
    estornar_recebimento_consulta,
    finalizar_consulta,
    iniciar_consulta,
    registrar_recebimento_consulta,
)
from ..models import Consulta, ProcedureProtocol, Professional
from ..permissions import CLINICA_CLINICAL, CLINICA_FINANCEIRO, IsClinicaAdmin
from ..serializers import ConsultaSerializer
from .helpers import get_consulta_or_404


class ConsultaIniciarView(APIView):
    """POST /clinica-beleza/consultas/<id>/iniciar/ — inicia atendimento (consulta + agenda)."""

    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=(
            "patient", "professional", "procedure", "protocol", "appointment", "appointment__procedure",
        ))
        if error:
            return error

        appointment = consulta.appointment
        if not appointment.professional_id:
            professional_id = request.data.get("professional")
            if not professional_id:
                return Response(
                    {"error": "Selecione o profissional para iniciar a consulta.", "code": "PROFESSIONAL_REQUIRED"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                prof = Professional.objects.get(pk=professional_id)
            except Professional.DoesNotExist:
                return Response({"error": "Profissional não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            if prof.is_profissional is False:
                return Response(
                    {
                        "error": "Este cadastro não está habilitado como profissional para atendimento.",
                        "code": "PROFESSIONAL_NOT_SCHEDULABLE",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            appointment.professional = prof
            appointment.save(update_fields=["professional", "updated_at"])
            consulta.professional = prof
            consulta.save(update_fields=["professional", "updated_at"])

        from ..permissions import is_clinica_admin

        try:
            iniciar_consulta(consulta, bypass_inadimplencia=is_clinica_admin(request))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaReceberView(APIView):
    """POST /clinica-beleza/consultas/<id>/receber/ — registra pagamento (total ou parcial)."""

    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=(
            "patient", "professional", "procedure", "protocol", "appointment",
            "appointment__procedure",
        ))
        if error:
            return error

        mark_as_paid = bool(request.data.get("mark_as_paid"))
        payment_method = (request.data.get("payment_method") or "CASH").strip()
        amount = request.data.get("amount")
        desconto = request.data.get("desconto")
        entradas = request.data.get("entradas")
        valor_procedimentos = request.data.get("valor_procedimentos")
        if valor_procedimentos not in (None, "") and not IsClinicaAdmin().has_permission(request, self):
            return Response(
                {"error": "Apenas o administrador pode alterar o valor do procedimento."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            payment = registrar_recebimento_consulta(
                consulta,
                payment_method=payment_method,
                amount=amount,
                mark_as_paid=mark_as_paid,
                desconto=desconto,
                entradas=entradas,
                valor_procedimentos=valor_procedimentos,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        from ..serializers.financeiro import PaymentSerializer

        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response({
            "consulta": ConsultaSerializer(consulta).data,
            "payment": PaymentSerializer(payment).data,
        }, status=status.HTTP_201_CREATED)


class ConsultaEstornarPagamentoView(APIView):
    """POST /clinica-beleza/consultas/<id>/estornar-pagamento/ — desfaz recebimento (não finalizada)."""

    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=(
            "patient", "professional", "procedure", "protocol", "appointment",
            "appointment__procedure",
        ))
        if error:
            return error

        try:
            payment = estornar_recebimento_consulta(consulta)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        from ..serializers.financeiro import PaymentSerializer

        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response({
            "consulta": ConsultaSerializer(consulta).data,
            "payment": PaymentSerializer(payment).data,
            "message": "Pagamento estornado. Você pode lançar novamente.",
        })


class ConsultaEmitirNfseView(APIView):
    """POST /clinica-beleza/consultas/<id>/emitir-nfse/ — emissão manual de NFS-e (consulta paga)."""

    permission_classes = CLINICA_FINANCEIRO

    def post(self, request, pk):
        from ..models import Payment
        from ..nfse_consulta_service import emitir_nfse_consulta_manual

        consulta, error = get_consulta_or_404(pk, select_related=(
            "patient", "professional", "procedure", "protocol", "appointment",
            "appointment__procedure",
        ))
        if error:
            return error

        appointment = getattr(consulta, "appointment", None)
        payment = None
        if appointment is not None:
            payment = (
                Payment.objects.filter(appointment=appointment, status="PAID")
                .order_by("-id")
                .first()
            )
        if payment is None:
            return Response(
                {"error": "Só é possível emitir nota de consulta com pagamento quitado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = emitir_nfse_consulta_manual(consulta, payment)
        if not result.get("success"):
            return Response(
                {"error": result.get("error") or "Falha ao emitir NFS-e."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        http_status = status.HTTP_202_ACCEPTED if result.get("queued") else status.HTTP_201_CREATED
        return Response(result, status=http_status)


class ConsultaFinalizarView(APIView):
    """POST /clinica-beleza/consultas/<id>/finalizar/ — conclui consulta, agenda e financeiro."""

    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=(
            "patient", "professional", "procedure", "protocol", "appointment", "appointment__procedure",
        ))
        if error:
            return error
        mark_as_paid = bool(request.data.get("mark_as_paid"))
        payment_method = (request.data.get("payment_method") or request.data.get("forma_pagamento") or "").strip() or None
        amount = request.data.get("amount") or request.data.get("valor")
        local_atendimento_id = request.data.get("local_atendimento")

        try:
            finalizar_consulta(
                consulta,
                payment_method=payment_method,
                mark_as_paid=mark_as_paid,
                amount=amount,
                local_atendimento_id=local_atendimento_id,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaAplicarProtocoloView(APIView):
    """POST /clinica-beleza/consultas/<id>/aplicar-protocolo/ — vincula protocolo e preenche notas."""

    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=("procedure",))
        if error:
            return error

        protocol_id = request.data.get("protocol_id")
        if not protocol_id:
            return Response({"error": "Informe protocol_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            protocol = ProcedureProtocol.objects.get(pk=protocol_id, is_active=True)
        except ProcedureProtocol.DoesNotExist:
            return Response({"error": "Protocolo não encontrado"}, status=status.HTTP_404_NOT_FOUND)

        if not consulta.procedure_id:
            return Response(
                {"error": "Adicione um procedimento à consulta antes de aplicar protocolo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if protocol.procedure_id != consulta.procedure_id:
            return Response({"error": "Protocolo não pertence ao procedimento da consulta"}, status=status.HTTP_400_BAD_REQUEST)

        notas = (
            f"=== {protocol.nome} ===\n\n"
            f"Preparação:\n{protocol.preparacao}\n\n"
            f"Execução:\n{protocol.execucao}\n\n"
            f"Pós-procedimento:\n{protocol.pos_procedimento}\n\n"
            f"Materiais:\n{protocol.materiais_necessarios}"
        )
        consulta.protocol = protocol
        consulta.protocolo_notas = notas
        consulta.save(update_fields=["protocol", "protocolo_notas", "updated_at"])
        return Response(ConsultaSerializer(consulta).data)
