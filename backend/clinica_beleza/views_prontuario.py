"""
Views do Prontuário — Visualização e geração de PDF
"""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .documento_service import listar_prontuario_paciente
from .models import DocumentoClinico, Patient
from .permissions import CLINICA_CLINICAL
from .prontuario_pdf import gerar_pdf_documento, gerar_pdf_prontuario_completo, gerar_pdf_secao
from .serializers import ProntuarioSectionSerializer
from .views_base import GetObjectMixin


class ProntuarioView(APIView):
    """
    GET /clinica-beleza/patients/<patient_id>/prontuario/
    Retorna prontuário do paciente agrupado por seção.

    Query params:
        ?secao=receituario — filtra por seção específica
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        if not Patient.objects.filter(pk=patient_id).exists():
            return Response(
                {'error': 'Paciente não encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        secao = request.query_params.get('secao')
        prontuario = listar_prontuario_paciente(patient_id, secao=secao)
        serializer = ProntuarioSectionSerializer(prontuario)
        return Response(serializer.data)


class ProntuarioPDFView(APIView):
    """
    GET /clinica-beleza/patients/<patient_id>/prontuario/pdf/
    Gera PDF do prontuário (seção ou completo).

    Query params:
        ?secao=receituario — PDF de uma seção específica
        (sem parâmetro) — PDF completo
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        if not Patient.objects.filter(pk=patient_id).exists():
            return Response(
                {'error': 'Paciente não encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        secao = request.query_params.get('secao')

        try:
            if secao:
                buffer = gerar_pdf_secao(patient_id, secao)
                filename = f'prontuario_{secao}_{patient_id}.pdf'
            else:
                buffer = gerar_pdf_prontuario_completo(patient_id)
                filename = f'prontuario_completo_{patient_id}.pdf'
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class DocumentoPDFView(GetObjectMixin, APIView):
    """
    GET /clinica-beleza/documentos/<doc_id>/pdf/
    Gera PDF de um documento individual.
    """
    permission_classes = CLINICA_CLINICAL
    model_class = DocumentoClinico
    not_found_message = 'Documento não encontrado'

    def get(self, request, doc_id):
        obj, error = self.object_or_404(doc_id)
        if error:
            return error

        try:
            buffer = gerar_pdf_documento(obj)
        except Exception as e:
            return Response(
                {'error': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        tipo = obj.tipo or 'documento'
        filename = f'{tipo}_{obj.id}.pdf'
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
