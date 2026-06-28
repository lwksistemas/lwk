"""CRUD e fluxo principal de consultas."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..consulta_service import (
    consulta_esta_concluida,
    criar_consulta_avulsa,
    finalizar_consulta,
    iniciar_consulta,
    motivo_bloqueio_exclusao_consulta,
)
from ..models import Consulta, Patient, Procedure, ProcedureProtocol, Professional
from ..pagination import paginate_queryset
from ..permissions import CLINICA_CLINICAL
from ..serializers import ConsultaSerializer
from ..views_base import GetObjectMixin, resolve_loja_id_from_request
from .helpers import get_consulta_or_404, get_patient_or_404
class ConsultaListView(APIView):
    """
    GET  /clinica-beleza/consultas/ — lista consultas.
    POST /clinica-beleza/consultas/ — abre uma consulta avulsa (sem agendamento na
         agenda) a partir do cadastro do cliente.
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        from django.db.models import Count

        from ..serializers import ConsultaListSerializer

        qs = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
            'appointment__nome_agenda',
        ).prefetch_related(
            'appointment__appointment_procedures__procedure',
        ).annotate(
            total_evolucoes_count=Count('evolucoes'),
        ).exclude(
            status='CANCELLED',
        ).order_by('-data_inicio', '-created_at')
        if patient_id := request.query_params.get('patient'):
            qs = qs.filter(patient_id=patient_id)
        if professional_id := request.query_params.get('professional'):
            qs = qs.filter(professional_id=professional_id)
        if st := request.query_params.get('status'):
            qs = qs.filter(status=st)
        if appointment_id := request.query_params.get('appointment'):
            qs = qs.filter(appointment_id=appointment_id)
        return paginate_queryset(qs, request, ConsultaListSerializer)

    def post(self, request):
        patient_id = request.data.get('patient')
        professional_id = request.data.get('professional')
        procedure_id = request.data.get('procedure')
        procedures_ids = request.data.get('procedures_ids') or []
        if not patient_id:
            return Response(
                {'error': 'Informe o paciente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not procedures_ids and not procedure_id:
            proc_list = []
        elif procedures_ids:
            proc_list = list(Procedure.objects.filter(id__in=procedures_ids, is_active=True))
            if not proc_list:
                return Response({'error': 'Nenhum procedimento válido encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                proc_list = [Procedure.objects.get(pk=procedure_id)]
            except Procedure.DoesNotExist:
                return Response({'error': 'Procedimento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Cliente não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        loja_id = resolve_loja_id_from_request(request)
        if patient.loja_id != loja_id:
            return Response({'error': 'Paciente não pertence a esta loja.'}, status=status.HTTP_400_BAD_REQUEST)

        professional = None
        if professional_id:
            try:
                professional = Professional.objects.get(pk=professional_id)
            except Professional.DoesNotExist:
                return Response({'error': 'Profissional não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        iniciar = request.data.get('iniciar', False)
        local_atendimento_id = request.data.get('local_atendimento')
        valor_consulta_override = request.data.get('valor_consulta')
        convenio_id = request.data.get('convenio')
        nome_agenda_id = request.data.get('nome_agenda')
        notes = request.data.get('notes')
        retorno_procedure_id = request.data.get('retorno_procedure')
        appointment_date = None
        if date_raw := request.data.get('date'):
            from django.utils.dateparse import parse_datetime
            appointment_date = parse_datetime(str(date_raw))
            if appointment_date is None:
                return Response({'error': 'Data/hora inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
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
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=consulta.id)
        return Response(ConsultaSerializer(consulta).data, status=status.HTTP_201_CREATED)


class ConsultaDetailView(GetObjectMixin, APIView):
    """GET / PUT / PATCH /clinica-beleza/consultas/<id>/"""
    permission_classes = CLINICA_CLINICAL
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = (
        'patient', 'professional', 'procedure', 'protocol', 'appointment',
        'local_atendimento', 'convenio',
    )
    prefetch_related_fields = ('appointment__appointment_procedures__procedure',)

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(ConsultaSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        if consulta_esta_concluida(obj):
            return Response(
                {'error': 'Consulta finalizada não pode ser editada.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ConsultaSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err

        if motivo := motivo_bloqueio_exclusao_consulta(consulta):
            return Response({'error': motivo}, status=status.HTTP_403_FORBIDDEN)

        # Cancela o agendamento vinculado (se existir e estiver aberto)
        appointment = consulta.appointment
        if appointment and appointment.status not in ('COMPLETED', 'CANCELLED'):
            appointment.status = 'CANCELLED'
            appointment.version = (appointment.version or 1) + 1
            appointment.save(update_fields=['status', 'version', 'updated_at'])

        consulta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConsultaIniciarView(APIView):
    """POST /clinica-beleza/consultas/<id>/iniciar/ — inicia atendimento (consulta + agenda)."""
    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=(
            'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
        ))
        if error:
            return error

        # Se agendamento sem profissional, exigir no body
        appointment = consulta.appointment
        if not appointment.professional_id:
            professional_id = request.data.get('professional')
            if not professional_id:
                return Response(
                    {'error': 'Selecione o profissional para iniciar a consulta.', 'code': 'PROFESSIONAL_REQUIRED'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                prof = Professional.objects.get(pk=professional_id)
            except Professional.DoesNotExist:
                return Response({'error': 'Profissional não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
            appointment.professional = prof
            appointment.save(update_fields=['professional', 'updated_at'])
            consulta.professional = prof
            consulta.save(update_fields=['professional', 'updated_at'])

        try:
            iniciar_consulta(consulta)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaFinalizarView(APIView):
    """POST /clinica-beleza/consultas/<id>/finalizar/ — conclui consulta, agenda e financeiro."""
    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=(
            'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
        ))
        if error:
            return error

        mark_as_paid = bool(request.data.get('mark_as_paid'))
        payment_method = (request.data.get('payment_method') or request.data.get('forma_pagamento') or '').strip() or None
        amount = request.data.get('amount') or request.data.get('valor')
        local_atendimento_id = request.data.get('local_atendimento')

        try:
            finalizar_consulta(
                consulta,
                payment_method=payment_method,
                mark_as_paid=mark_as_paid,
                amount=amount,
                local_atendimento_id=local_atendimento_id,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaAplicarProtocoloView(APIView):
    """POST /clinica-beleza/consultas/<id>/aplicar-protocolo/ — vincula protocolo e preenche notas."""
    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        consulta, error = get_consulta_or_404(pk, select_related=('procedure',))
        if error:
            return error

        protocol_id = request.data.get('protocol_id')
        if not protocol_id:
            return Response({'error': 'Informe protocol_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            protocol = ProcedureProtocol.objects.get(pk=protocol_id, is_active=True)
        except ProcedureProtocol.DoesNotExist:
            return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if not consulta.procedure_id:
            return Response(
                {'error': 'Adicione um procedimento à consulta antes de aplicar protocolo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if protocol.procedure_id != consulta.procedure_id:
            return Response({'error': 'Protocolo não pertence ao procedimento da consulta'}, status=status.HTTP_400_BAD_REQUEST)

        notas = (
            f"=== {protocol.nome} ===\n\n"
            f"Preparação:\n{protocol.preparacao}\n\n"
            f"Execução:\n{protocol.execucao}\n\n"
            f"Pós-procedimento:\n{protocol.pos_procedimento}\n\n"
            f"Materiais:\n{protocol.materiais_necessarios}"
        )
        consulta.protocol = protocol
        consulta.protocolo_notas = notas
        consulta.save(update_fields=['protocol', 'protocolo_notas', 'updated_at'])
        return Response(ConsultaSerializer(consulta).data)
