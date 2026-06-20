"""Views de configuração de retorno gratuito — Clínica da Beleza."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RetornoProcedimentoRegra
from .permissions import CLINICA_MEMBER
from .retorno_service import get_agenda_retorno_config, verificar_retorno
from .serializers.retorno import AgendaRetornoConfigSerializer, RetornoProcedimentoRegraSerializer
from .views_base import GetObjectMixin


def _ensure_retorno_schema_or_response():
    from .retorno_service import require_retorno_gratuito_schema

    try:
        require_retorno_gratuito_schema()
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return None


class RetornoConfigView(APIView):
    """
    GET/PATCH /clinica-beleza/retorno/config/
    Configuração geral: ativar retorno por procedimento/consulta e prazo da consulta.
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
        config = get_agenda_retorno_config(loja_id)
        return Response(AgendaRetornoConfigSerializer(config).data)

    def patch(self, request):
        err = _ensure_retorno_schema_or_response()
        if err:
            return err
        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
        config = get_agenda_retorno_config(loja_id)
        serializer = AgendaRetornoConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetornoProcedimentoRegraListView(APIView):
    """GET/POST /clinica-beleza/retorno/procedimentos/"""
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        err = _ensure_retorno_schema_or_response()
        if err:
            return err
        qs = RetornoProcedimentoRegra.objects.filter(is_active=True).select_related('procedure').order_by('procedure__nome')
        return Response(RetornoProcedimentoRegraSerializer(qs, many=True).data)

    def post(self, request):
        err = _ensure_retorno_schema_or_response()
        if err:
            return err
        serializer = RetornoProcedimentoRegraSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RetornoProcedimentoRegraDetailView(GetObjectMixin, APIView):
    """GET/PATCH/DELETE /clinica-beleza/retorno/procedimentos/<pk>/"""
    permission_classes = CLINICA_MEMBER
    model_class = RetornoProcedimentoRegra
    not_found_message = 'Regra de retorno não encontrada'

    def get(self, request, pk):
        err = _ensure_retorno_schema_or_response()
        if err:
            return err
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(RetornoProcedimentoRegraSerializer(obj).data)

    def _update(self, request, pk):
        err = _ensure_retorno_schema_or_response()
        if err:
            return err
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = RetornoProcedimentoRegraSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self._update(request, pk)

    def put(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        err = _ensure_retorno_schema_or_response()
        if err:
            return err
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RetornoVerificarView(APIView):
    """
    GET /clinica-beleza/retorno/verificar/?patient_id=&procedure_ids=1,2&retorno_procedure_id=
    Verifica se paciente tem direito a retorno gratuito (taxa de consulta isenta).
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        err = _ensure_retorno_schema_or_response()
        if err:
            return err
        from tenants.middleware import get_current_loja_id

        loja_id = get_current_loja_id()
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        procedure_ids = []
        raw = (request.query_params.get('procedure_ids') or '').strip()
        if raw:
            procedure_ids = [int(x) for x in raw.split(',') if x.strip().isdigit()]
        retorno_proc = request.query_params.get('retorno_procedure_id')
        if retorno_proc and str(retorno_proc).isdigit():
            procedure_ids.append(int(retorno_proc))

        exclude_appt = request.query_params.get('exclude_appointment_id')
        exclude_id = int(exclude_appt) if exclude_appt and str(exclude_appt).isdigit() else None

        resultado = verificar_retorno(
            int(patient_id),
            procedure_ids,
            loja_id,
            exclude_appointment_id=exclude_id,
        )
        config = get_agenda_retorno_config(loja_id)
        payload = resultado.to_dict()
        payload['config'] = AgendaRetornoConfigSerializer(config).data
        regras = RetornoProcedimentoRegra.objects.filter(loja_id=loja_id, is_active=True).select_related('procedure')
        payload['regras_procedimento'] = RetornoProcedimentoRegraSerializer(regras, many=True).data
        return Response(payload)
