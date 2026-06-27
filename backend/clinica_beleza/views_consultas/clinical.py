"""Anamnese, evolução, histórico e PDF de consulta."""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Consulta, ConsultaEvolucao, PatientAnamnese
from ..pagination import paginate_queryset
from ..permissions import CLINICA_CLINICAL
from ..serializers import ConsultaEvolucaoSerializer, PatientAnamneseSerializer
from .helpers import get_patient_or_404

class PatientAnamneseView(APIView):
    """GET / PUT /clinica-beleza/patients/<patient_id>/anamnese/"""
    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        from clinica_beleza.schema_ensure import ensure_patient_anamnese_for_tenant

        patient, error = get_patient_or_404(patient_id)
        if error:
            return error
        if not ensure_patient_anamnese_for_tenant():
            return Response(
                {'error': 'Estrutura de anamnese indisponível. Contate o suporte.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        obj, _ = PatientAnamnese.objects.get_or_create(
            patient_id=patient_id,
            defaults={'loja_id': patient.loja_id},
        )
        return Response(PatientAnamneseSerializer(obj).data)

    def put(self, request, patient_id):
        from clinica_beleza.schema_ensure import ensure_patient_anamnese_for_tenant

        patient, error = get_patient_or_404(patient_id)
        if error:
            return error
        if not ensure_patient_anamnese_for_tenant():
            return Response(
                {'error': 'Estrutura de anamnese indisponível. Contate o suporte.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        obj, _ = PatientAnamnese.objects.get_or_create(
            patient_id=patient_id,
            defaults={'loja_id': patient.loja_id},
        )
        serializer = PatientAnamneseSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        import logging
        logger = logging.getLogger(__name__)
        logger.warning('Anamnese PUT 400 patient_id=%s errors=%s data_keys=%s', patient_id, serializer.errors, list(request.data.keys()))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultaEvolucaoListView(APIView):
    """GET / POST /clinica-beleza/consultas/<consulta_id>/evolucoes/"""
    permission_classes = CLINICA_CLINICAL

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

        if consulta.status == 'COMPLETED':
            return Response(
                {'error': 'Consulta finalizada não permite novas evoluções.'},
                status=status.HTTP_403_FORBIDDEN,
            )

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


class ConsultaSecaoPDFView(APIView):
    """
    GET /clinica-beleza/consultas/<consulta_id>/pdf/?secao=atendimento|produtos|anamnese|evolucao
    Gera PDF da seção com logo ou papel timbrado da clínica.
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request, consulta_id):
        from .consulta_queries import get_consulta_for_tenant

        consulta = get_consulta_for_tenant(
            consulta_id,
            select_related=('patient', 'professional', 'procedure', 'protocol'),
        )
        if not consulta:
            return Response({'error': 'Consulta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        secao = request.query_params.get('secao', 'atendimento')
        try:
            from .prontuario_pdf import gerar_pdf_consulta_secao
            buffer = gerar_pdf_consulta_secao(consulta, secao)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Erro PDF consulta %s secao %s', consulta_id, secao)
            return Response(
                {'error': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = f'consulta_{consulta_id}_{secao}.pdf'
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class PatientHistoricoConsultasView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/consultas/ — histórico do cliente."""
    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        from django.db.models import Count

        from ..serializers import ConsultaListSerializer

        qs = Consulta.objects.filter(patient_id=patient_id).select_related(
            'professional', 'procedure', 'protocol', 'appointment', 'patient',
        ).prefetch_related(
            'appointment__appointment_procedures__procedure',
        ).annotate(
            total_evolucoes_count=Count('evolucoes'),
        ).order_by('-data_inicio', '-created_at')
        return paginate_queryset(qs, request, ConsultaListSerializer)
