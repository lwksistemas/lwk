"""
Views de Profissionais e Horários de Trabalho — Clínica da Beleza
"""
import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Professional, HorarioTrabalhoProfissional, Appointment, BloqueioHorario
from .serializers import (
    ProfessionalSerializer, ProfessionalCreateWithUserSerializer,
    HorarioTrabalhoProfissionalSerializer,
)
from .utils import LojaContextHelper

logger = logging.getLogger(__name__)


class ProfessionalListView(APIView):
    """
    Listagem e criação de profissionais
    GET /clinica-beleza/professionals/
    POST /clinica-beleza/professionals/
    """
    permission_classes = [IsAuthenticated]

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

        def _empty_to_none(v):
            if isinstance(v, list):
                v = v[0] if len(v) == 1 else None
            if isinstance(v, str) and (v.strip() == '' or v.strip().lower() == 'null'):
                return None
            return v

        data = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in raw.items()}
        for key in ('email', 'phone'):
            if key in data:
                data[key] = _empty_to_none(data[key])
        for key in ('name', 'specialty'):
            if key in data and isinstance(data[key], str):
                data[key] = data[key].strip() or None

        # Criar com acesso (usuário Django)
        if data.get('criar_acesso') and data.get('email'):
            serializer = ProfessionalCreateWithUserSerializer(data=data)
            if serializer.is_valid():
                return Response(
                    ProfessionalSerializer(serializer.save()).data,
                    status=status.HTTP_201_CREATED,
                )
            err_payload = dict(serializer.errors)
            for v in serializer.errors.values():
                msg = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else None)
                if msg:
                    err_payload['detail'] = msg
                    break
            return Response(err_payload, status=status.HTTP_400_BAD_REQUEST)

        # Validação antecipada
        def _str_val(key):
            v = data.get(key)
            if isinstance(v, list):
                v = v[0] if v else ''
            return (v or '').strip() if isinstance(v, str) else ''

        name_val = _str_val('name')
        specialty_val = _str_val('specialty')
        if not name_val or not specialty_val:
            missing = [f for f, v in [('nome', name_val), ('especialidade', specialty_val)] if not v]
            return Response({'detail': f'Preencha {", ".join(missing)}.'}, status=status.HTTP_400_BAD_REQUEST)

        active_val = data.get('active', True)
        if isinstance(active_val, str):
            active_val = active_val.strip().lower() in ('1', 'true', 'yes', 'on')

        payload = {
            'nome': name_val,
            'especialidade': specialty_val,
            'telefone': data.get('phone') or data.get('telefone') or '',
            'email': data.get('email'),
            'is_active': bool(active_val),
        }
        serializer = ProfessionalSerializer(data=payload)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.error('POST professionals 400 payload=%s errors=%s', payload, json.dumps(serializer.errors, ensure_ascii=False))
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalDetailView(APIView):
    """GET /clinica-beleza/professionals/<id>/  PUT  DELETE"""
    permission_classes = [IsAuthenticated]

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
            serializer = ProfessionalSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
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


class HorarioTrabalhoProfissionalView(APIView):
    """
    Dias e horários de trabalho do profissional.
    GET /clinica-beleza/professionals/<id>/horarios-trabalho/
    PUT /clinica-beleza/professionals/<id>/horarios-trabalho/
    """
    permission_classes = [IsAuthenticated]

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
