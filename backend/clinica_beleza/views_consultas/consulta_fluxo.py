"""Iniciar, receber, estornar, NFS-e, finalizar e protocolo."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..consulta_service import (
    MSG_PROFISSIONAL_OBRIGATORIO,
    estornar_recebimento_consulta,
    finalizar_consulta,
    iniciar_consulta,
    reabrir_consulta,
    registrar_recebimento_consulta,
    trocar_profissional_consulta,
)
from ..models import Consulta, ProcedureProtocol, Professional
from ..permissions import CLINICA_CLINICAL, CLINICA_CONSULTA_OPERACIONAL, CLINICA_FINANCEIRO, IsClinicaAdmin
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

        from ..permissions import is_clinica_admin, usuario_e_profissional_da_consulta

        if not usuario_e_profissional_da_consulta(request, consulta):
            return Response(
                {
                    "error": (
                        "Só o profissional vinculado na agenda pode iniciar esta consulta. "
                        "Se ele não puder atender, troque o profissional."
                    ),
                    "code": "PROFESSIONAL_MISMATCH",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            iniciar_consulta(consulta, bypass_inadimplencia=is_clinica_admin(request))
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaTrocarProfissionalView(APIView):
    """POST /consultas/<id>/trocar-profissional/ — troca quem vai atender, sem iniciar."""

    permission_classes = CLINICA_CONSULTA_OPERACIONAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=(
            "patient", "professional", "appointment",
        ))
        if error:
            return error
        professional_id = request.data.get("professional")
        if not professional_id:
            return Response(
                {"error": MSG_PROFISSIONAL_OBRIGATORIO},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            prof = Professional.objects.get(pk=professional_id)
        except (Professional.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Profissional não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        try:
            trocar_profissional_consulta(consulta, prof)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta, context={"request": request}).data)


class ConsultaReceberView(APIView):
    """POST /clinica-beleza/consultas/<id>/receber/ — registra pagamento (total ou parcial)."""

    permission_classes = CLINICA_CONSULTA_OPERACIONAL

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

        forma = str(request.data.get("forma_cobranca") or "").strip()
        try:
            from django.db import transaction

            from ..agenda_service import AgendaValidationError
            from ..protocolo_personalizado import definir_pagamento_protocolo

            with transaction.atomic():
                if forma and getattr(consulta, "appointment_id", None):
                    contrato = getattr(consulta.appointment, "protocolo_contrato", None)
                    if contrato is not None and not getattr(contrato, "protocol_id", None):
                        definir_pagamento_protocolo(
                            contrato,
                            forma,
                            appointment_id=consulta.appointment_id,
                        )
                payment = registrar_recebimento_consulta(
                    consulta,
                    payment_method=payment_method,
                    amount=amount,
                    mark_as_paid=mark_as_paid,
                    desconto=desconto,
                    entradas=entradas,
                    valor_procedimentos=valor_procedimentos,
                    usuario=request.user,
                )
        except AgendaValidationError as exc:
            return Response({"error": exc.message}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        from ..serializers.financeiro import PaymentSerializer

        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response({
            "consulta": ConsultaSerializer(consulta, context={"request": request}).data,
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
            payment = estornar_recebimento_consulta(consulta, usuario=request.user)
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
        from ..permissions import recusar_andamento_alheio

        if bloqueio := recusar_andamento_alheio(request, consulta):
            return bloqueio
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
                usuario=request.user,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            "patient", "professional", "procedure", "protocol", "appointment",
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaReabrirView(APIView):
    """POST /clinica-beleza/consultas/<id>/reabrir/ — só o profissional que fez a consulta.

    Volta o status para "em atendimento" para incluir procedimentos ou corrigir.
    Não estorna pagamento, não reverte estoque e não cancela NFS-e.
    """

    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        from ..permissions import MSG_REABRIR_SO_QUEM_FEZ, usuario_e_profissional_da_consulta

        consulta, error = get_consulta_or_404(pk, select_related=(
            "patient", "professional", "procedure", "protocol", "appointment", "appointment__procedure",
        ))
        if error:
            return error
        if not usuario_e_profissional_da_consulta(request, consulta):
            return Response({"error": MSG_REABRIR_SO_QUEM_FEZ}, status=status.HTTP_403_FORBIDDEN)

        try:
            reabrir_consulta(consulta)
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
        from ..permissions import recusar_andamento_alheio

        if bloqueio := recusar_andamento_alheio(request, consulta):
            return bloqueio

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
