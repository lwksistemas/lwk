"""
Views de Consultas — Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import (
    Consulta, PatientAnamnese, ConsultaEvolucao, ProcedureProtocol,
    Patient, Professional, Procedure, PrescricaoMemed,
)
from .serializers import (
    ConsultaSerializer, PatientAnamneseSerializer, ConsultaEvolucaoSerializer,
    PrescricaoMemedSerializer,
)
from .consulta_service import finalizar_consulta, iniciar_consulta, criar_consulta_avulsa
from .pagination import paginate_queryset


class ConsultaListView(APIView):
    """
    GET  /clinica-beleza/consultas/ — lista consultas.
    POST /clinica-beleza/consultas/ — abre uma consulta avulsa (sem agendamento na
         agenda) a partir do cadastro do cliente.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).order_by('-data_inicio', '-created_at')
        if patient_id := request.query_params.get('patient'):
            qs = qs.filter(patient_id=patient_id)
        if professional_id := request.query_params.get('professional'):
            qs = qs.filter(professional_id=professional_id)
        if st := request.query_params.get('status'):
            qs = qs.filter(status=st)
        if appointment_id := request.query_params.get('appointment'):
            qs = qs.filter(appointment_id=appointment_id)
        return paginate_queryset(qs, request, ConsultaSerializer)

    def post(self, request):
        patient_id = request.data.get('patient')
        professional_id = request.data.get('professional')
        procedure_id = request.data.get('procedure')
        if not patient_id or not professional_id or not procedure_id:
            return Response(
                {'error': 'Informe cliente, profissional e procedimento.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Cliente não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            professional = Professional.objects.get(pk=professional_id)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            procedure = Procedure.objects.get(pk=procedure_id)
        except Procedure.DoesNotExist:
            return Response({'error': 'Procedimento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Por padrão NÃO inicia o atendimento — quem inicia é o profissional.
        iniciar = request.data.get('iniciar', False)
        consulta = criar_consulta_avulsa(
            patient=patient,
            professional=professional,
            procedure=procedure,
            loja_id=patient.loja_id,
            iniciar=bool(iniciar),
        )
        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=consulta.id)
        return Response(ConsultaSerializer(consulta).data, status=status.HTTP_201_CREATED)


class ConsultaDetailView(APIView):
    """GET / PUT / PATCH /clinica-beleza/consultas/<id>/"""
    permission_classes = [IsAuthenticated]

    def _get(self, pk):
        return Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=pk)

    def get(self, request, pk):
        try:
            return Response(ConsultaSerializer(self._get(pk)).data)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            obj = self._get(pk)
            serializer = ConsultaSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        try:
            consulta = self._get(pk)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        # Só permite excluir consultas que ainda não foram concluídas
        if consulta.status == 'COMPLETED':
            return Response(
                {'error': 'Consultas concluídas não podem ser excluídas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            consulta = Consulta.objects.select_related(
                'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
            ).get(pk=pk)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

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
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            consulta = Consulta.objects.select_related(
                'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
            ).get(pk=pk)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        mark_as_paid = bool(request.data.get('mark_as_paid'))
        payment_method = (request.data.get('payment_method') or request.data.get('forma_pagamento') or '').strip() or None
        amount = request.data.get('amount') or request.data.get('valor')

        try:
            finalizar_consulta(
                consulta,
                payment_method=payment_method,
                mark_as_paid=mark_as_paid,
                amount=amount,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaAplicarProtocoloView(APIView):
    """POST /clinica-beleza/consultas/<id>/aplicar-protocolo/ — vincula protocolo e preenche notas."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            consulta = Consulta.objects.select_related('procedure').get(pk=pk)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        protocol_id = request.data.get('protocol_id')
        if not protocol_id:
            return Response({'error': 'Informe protocol_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            protocol = ProcedureProtocol.objects.get(pk=protocol_id, is_active=True)
        except ProcedureProtocol.DoesNotExist:
            return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

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


class PatientAnamneseView(APIView):
    """GET / PUT /clinica-beleza/patients/<patient_id>/anamnese/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        obj, _ = PatientAnamnese.objects.get_or_create(
            patient_id=patient_id,
            defaults={'loja_id': patient.loja_id},
        )
        return Response(PatientAnamneseSerializer(obj).data)

    def put(self, request, patient_id):
        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        obj, _ = PatientAnamnese.objects.get_or_create(
            patient_id=patient_id,
            defaults={'loja_id': patient.loja_id},
        )
        serializer = PatientAnamneseSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultaEvolucaoListView(APIView):
    """GET / POST /clinica-beleza/consultas/<consulta_id>/evolucoes/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, consulta_id):
        qs = ConsultaEvolucao.objects.filter(consulta_id=consulta_id).select_related(
            'patient', 'professional',
        ).order_by('-created_at')
        return Response(ConsultaEvolucaoSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        try:
            consulta = Consulta.objects.get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        data = {
            **request.data,
            'consulta': consulta.id,
            'patient': consulta.patient_id,
            'professional': request.data.get('professional') or consulta.professional_id,
        }
        serializer = ConsultaEvolucaoSerializer(data=data)
        if serializer.is_valid():
            serializer.save(loja_id=consulta.loja_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientHistoricoConsultasView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/consultas/ — histórico do cliente."""
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        qs = Consulta.objects.filter(patient_id=patient_id).select_related(
            'professional', 'procedure', 'protocol', 'appointment',
        ).order_by('-data_inicio', '-created_at')
        return Response(ConsultaSerializer(qs, many=True).data)


class ConsultaPrescricaoView(APIView):
    """
    GET  /clinica-beleza/consultas/<consulta_id>/prescricoes/ — lista prescrições da consulta.
    POST /clinica-beleza/consultas/<consulta_id>/prescricoes/ — registra uma prescrição emitida
         na Memed (a partir do evento prescricaoImpressa).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, consulta_id):
        qs = PrescricaoMemed.objects.filter(consulta_id=consulta_id).select_related(
            'patient', 'professional',
        ).order_by('-created_at')
        return Response(PrescricaoMemedSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        try:
            consulta = Consulta.objects.get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        itens = request.data.get('itens') or []
        if not isinstance(itens, list):
            itens = []
        data = {
            'consulta': consulta.id,
            'patient': consulta.patient_id,
            'professional': request.data.get('professional') or consulta.professional_id,
            'prescricao_id': str(request.data.get('prescricao_id') or '')[:64],
            'resumo': request.data.get('resumo') or '',
            'itens': itens,
        }
        serializer = PrescricaoMemedSerializer(data=data)
        if serializer.is_valid():
            serializer.save(loja_id=consulta.loja_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientPrescricaoView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/prescricoes/ — prescrições do cliente (histórico)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        qs = PrescricaoMemed.objects.filter(patient_id=patient_id).select_related(
            'professional', 'consulta',
        ).order_by('-created_at')
        return Response(PrescricaoMemedSerializer(qs, many=True).data)
