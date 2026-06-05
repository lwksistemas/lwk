"""
Views de Profissionais e Horários de Trabalho — Clínica da Beleza
"""
import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_ADMIN
from rest_framework import status

from .models import Professional, HorarioTrabalhoProfissional, Appointment, BloqueioHorario, ProfessionalCommission
from .serializers import (
    ProfessionalSerializer, ProfessionalCreateWithUserSerializer,
    HorarioTrabalhoProfissionalSerializer, ProfessionalCommissionSerializer,
)
from .utils import LojaContextHelper
from .views_base import map_field_names

logger = logging.getLogger(__name__)


def _sync_memed(professional):
    """Dispara o auto-cadastro do prescritor na Memed (best-effort; nunca quebra o save)."""
    try:
        from .memed_service import sincronizar_prescritor
        resultado = sincronizar_prescritor(professional)
        if resultado.get('ok') is False and resultado.get('status'):
            logger.info('Memed auto-cadastro prof %s: %s', getattr(professional, 'id', None), resultado)
    except Exception as e:  # noqa: BLE001 — sincronização é opcional.
        logger.warning('Memed auto-cadastro ignorado (prof %s): %s', getattr(professional, 'id', None), e)


_PROFESSIONAL_FIELD_MAP = {
    'name': 'nome',
    'specialty': 'especialidade',
    'phone': 'telefone',
    'active': 'is_active',
}


def _map_professional_data(raw_data):
    """Normaliza campos legados (inglês) para os nomes do model."""
    data = raw_data.copy() if hasattr(raw_data, 'copy') else dict(raw_data)
    data = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in data.items()}

    def _empty_to_none(v):
        if isinstance(v, list):
            v = v[0] if len(v) == 1 else None
        if isinstance(v, str) and (v.strip() == '' or v.strip().lower() == 'null'):
            return None
        return v

    data = map_field_names(data, _PROFESSIONAL_FIELD_MAP)

    for key in ('email', 'telefone', 'data_nascimento', 'sexo'):
        if key in data:
            data[key] = _empty_to_none(data[key])
    if 'telefone' in data and data['telefone'] is None:
        data['telefone'] = ''

    for key in ('nome', 'especialidade'):
        if key in data and isinstance(data[key], str):
            data[key] = data[key].strip() or None

    if 'is_active' in data and isinstance(data['is_active'], str):
        data['is_active'] = data['is_active'].strip().lower() in ('1', 'true', 'yes', 'on')

    for key in ('criar_acesso', 'perfil'):
        data.pop(key, None)

    return data


class ProfessionalListView(APIView):
    """
    Listagem e criação de profissionais
    GET /clinica-beleza/professionals/
    POST /clinica-beleza/professionals/
    """
    permission_classes = CLINICA_ADMIN

    def get(self, request):
        active_only = request.query_params.get('active', 'true').lower() == 'true'
        with_schedule = request.query_params.get('with_schedule', 'false').lower() == 'true'

        queryset = Professional.objects.all().order_by('nome')
        if active_only:
            queryset = queryset.filter(is_active=True)
        if with_schedule:
            queryset = queryset.filter(
                id__in=HorarioTrabalhoProfissional.objects.filter(ativo=True)
                .values_list('professional_id', flat=True).distinct()
            )

        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        # Na agenda: administrador não aparece como profissional de atendimento
        if with_schedule and owner_professional_id is not None:
            queryset = queryset.exclude(id=owner_professional_id)

        return Response(ProfessionalSerializer(
            queryset, many=True,
            context={'owner_professional_id': owner_professional_id}
        ).data)

    def post(self, request):
        raw = request.data if isinstance(request.data, dict) else dict(request.data)

        # Criar com acesso (usuário Django) — serializer usa campos em inglês
        data = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in raw.items()}
        if data.get('criar_acesso') and data.get('email'):
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
                    err_payload['detail'] = msg
                    break
            return Response(err_payload, status=status.HTTP_400_BAD_REQUEST)

        payload = _map_professional_data(raw)
        name_val = (payload.get('nome') or '').strip()
        specialty_val = (payload.get('especialidade') or '').strip()
        if not name_val or not specialty_val:
            missing = [f for f, v in [('nome', name_val), ('especialidade', specialty_val)] if not v]
            return Response({'detail': f'Preencha {", ".join(missing)}.'}, status=status.HTTP_400_BAD_REQUEST)

        payload['nome'] = name_val
        payload['especialidade'] = specialty_val
        payload.setdefault('is_active', True)

        serializer = ProfessionalSerializer(data=payload)
        if serializer.is_valid():
            professional = serializer.save()
            _sync_memed(professional)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error('POST professionals 400 payload=%s errors=%s', payload, json.dumps(serializer.errors, ensure_ascii=False))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalDetailView(APIView):
    """GET /clinica-beleza/professionals/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_ADMIN

    def get(self, request, pk):
        try:
            obj = Professional.objects.get(pk=pk)
            owner_professional_id = LojaContextHelper.get_owner_professional_id()
            return Response(ProfessionalSerializer(obj, context={'owner_professional_id': owner_professional_id}).data)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            return Response({'error': 'O administrador vinculado à loja não pode ser editado.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            obj = Professional.objects.get(pk=pk)
            data = _map_professional_data(request.data)
            serializer = ProfessionalSerializer(obj, data=data, partial=True)
            if serializer.is_valid():
                professional = serializer.save()
                _sync_memed(professional)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            return Response({'error': 'O administrador vinculado à loja não pode ser excluído.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            obj = Professional.objects.get(pk=pk)
            from django.utils import timezone
            agora = timezone.now()
            count = Appointment.objects.filter(professional=obj, date__gte=agora).count()
            Appointment.objects.filter(professional=obj, date__gte=agora).delete()
            HorarioTrabalhoProfissional.objects.filter(professional=obj).delete()
            BloqueioHorario.objects.filter(professional=obj).delete()
            obj.is_active = False
            obj.save()
            return Response({
                'message': f'Profissional desativado. {count} agendamento(s) futuro(s) excluído(s).'
            }, status=status.HTTP_200_OK)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ProfessionalMemedStatusView(APIView):
    """
    Status Memed dos prescritores da loja (consulta em lote via API Memed).
    GET /clinica-beleza/professionals/memed-status/
    Retorna dict { "<professional_id>": { state, label, status?, ... } }.
    """
    permission_classes = CLINICA_ADMIN

    def get(self, request):
        from concurrent.futures import ThreadPoolExecutor, as_completed

        from .memed_service import consultar_status_memed

        active_only = request.query_params.get('active', 'true').lower() == 'true'
        qs = Professional.objects.all().order_by('id')
        if active_only:
            qs = qs.filter(is_active=True)

        professionals = list(qs)
        results = {}

        def _fetch(prof):
            info = consultar_status_memed(prof)
            return str(prof.id), info

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(_fetch, p) for p in professionals]
            for future in as_completed(futures):
                pid, info = future.result()
                results[pid] = info

        return Response(results)


class HorarioTrabalhoProfissionalView(APIView):
    """
    Dias e horários de trabalho do profissional.
    GET /clinica-beleza/professionals/<id>/horarios-trabalho/
    PUT /clinica-beleza/professionals/<id>/horarios-trabalho/
    """
    permission_classes = CLINICA_ADMIN

    def get(self, request, pk):
        try:
            Professional.objects.get(pk=pk)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        queryset = HorarioTrabalhoProfissional.objects.filter(professional_id=pk).order_by('dia_semana')
        return Response(HorarioTrabalhoProfissionalSerializer(queryset, many=True).data)

    def put(self, request, pk):
        try:
            professional = Professional.objects.get(pk=pk)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Envie uma lista de horários. Ex.: [{"dia_semana": 0, "hora_entrada": "08:00", "hora_saida": "18:00", "ativo": true}]'},
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


class ProfessionalCommissionView(APIView):
    """
    GET  /clinica-beleza/professionals/<id>/comissoes/ — lista comissões do profissional.
    POST /clinica-beleza/professionals/<id>/comissoes/ — cria/atualiza comissões (recebe lista).
    """
    permission_classes = CLINICA_ADMIN

    def get(self, request, pk):
        try:
            Professional.objects.get(pk=pk)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        qs = ProfessionalCommission.objects.filter(
            professional_id=pk, is_active=True
        ).select_related('procedure').order_by('tipo', 'procedure__nome')
        return Response(ProfessionalCommissionSerializer(qs, many=True).data)

    def post(self, request, pk):
        """Recebe uma lista de comissões. Substitui todas as existentes."""
        try:
            professional = Professional.objects.get(pk=pk)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if not isinstance(request.data, list):
            return Response(
                {'error': 'Envie uma lista de comissões.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Desativar comissões existentes e criar novas
        ProfessionalCommission.objects.filter(professional_id=pk).update(is_active=False)
        created = []
        locais_consulta_vistos = set()
        for item in request.data:
            if item.get('tipo') == 'consulta':
                local_id = item.get('local_atendimento')
                if not local_id:
                    return Response(
                        {'local_atendimento': 'Informe o local para cada comissão de consulta.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if local_id in locais_consulta_vistos:
                    return Response(
                        {'local_atendimento': 'Não repita o mesmo local de atendimento.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                locais_consulta_vistos.add(local_id)
            data = {**item, 'professional': pk}
            serializer = ProfessionalCommissionSerializer(data=data)
            if serializer.is_valid():
                obj = serializer.save(professional=professional, is_active=True)
                created.append(ProfessionalCommissionSerializer(obj).data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(created, status=status.HTTP_200_OK)
