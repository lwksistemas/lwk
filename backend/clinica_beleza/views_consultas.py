"""
Views de Consultas — Clínica da Beleza
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Consulta, PatientAnamnese, ConsultaEvolucao, ProcedureProtocol, Patient
from .serializers import ConsultaSerializer, PatientAnamneseSerializer, ConsultaEvolucaoSerializer


class ConsultaListView(APIView):
    """GET /clinica-beleza/consultas/ — lista consultas (criadas via agenda)."""
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
        return Response(ConsultaSerializer(qs, many=True).data)


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
