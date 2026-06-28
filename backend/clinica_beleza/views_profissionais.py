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
from .pagination import paginate_queryset
from .views_base import GetObjectMixin, map_field_names

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

# Campos operacionais que o profissional-admin da loja pode alterar (PUT parcial).
_OWNER_PROFESSIONAL_EDITABLE_FIELDS = frozenset({
    'tempo_consulta_minutos',
    'registro_profissional', 'conselho', 'conselho_uf',
    'especialidade', 'telefone', 'email',
    'cpf', 'data_nascimento', 'sexo',
    'nome', 'specialty', 'name', 'phone',
    'registro', 'uf', 'is_profissional',
    'is_active', 'active',
})

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

    if 'is_profissional' in data and isinstance(data['is_profissional'], str):
        data['is_profissional'] = data['is_profissional'].strip().lower() in ('1', 'true', 'yes', 'on')

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

        # Filtrar apenas profissionais que atendem (is_profissional=True)
        # para agenda e agendamentos
        scheduling = request.query_params.get('scheduling', '').lower() == 'true'
        if with_schedule or scheduling:
            queryset = queryset.filter(is_profissional=True)

        admin_professional_ids = LojaContextHelper.get_admin_professional_ids()
        owner_professional_id = LojaContextHelper.get_owner_professional_id()

        # Na agenda: administradores com is_profissional=False não aparecem
        if with_schedule and admin_professional_ids:
            admin_not_professional = Professional.objects.filter(
                id__in=admin_professional_ids, is_profissional=False
            ).values_list('id', flat=True)
            queryset = queryset.exclude(id__in=admin_not_professional)

        return paginate_queryset(
            queryset,
            request,
            ProfessionalSerializer,
            serializer_context={
                'admin_professional_ids': admin_professional_ids,
                'owner_professional_id': owner_professional_id,
            },
        )

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


class ProfessionalDetailView(GetObjectMixin, APIView):
    """GET /clinica-beleza/professionals/<id>/  PUT  DELETE"""
    permission_classes = CLINICA_ADMIN
    model_class = Professional
    not_found_message = 'Profissional não encontrado'

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        admin_professional_ids = LojaContextHelper.get_admin_professional_ids()
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        return Response(ProfessionalSerializer(obj, context={
            'admin_professional_ids': admin_professional_ids,
            'owner_professional_id': owner_professional_id,
        }).data)

    def put(self, request, pk):
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        data = _map_professional_data(request.data)
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            # Bloquear desativação do owner
            if 'is_active' in data and data['is_active'] is False:
                return Response(
                    {'error': 'O administrador vinculado à loja não pode ser desativado.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            keys = set(data.keys())
            if not keys or not keys.issubset(_OWNER_PROFESSIONAL_EDITABLE_FIELDS):
                return Response(
                    {'error': 'O administrador vinculado à loja não pode ser editado.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        obj, err = self.object_or_404(pk)
        if err:
            return err
        serializer = ProfessionalSerializer(obj, data=data, partial=True)
        if serializer.is_valid():
            professional = serializer.save()
            _sync_memed(professional)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        owner_professional_id = LojaContextHelper.get_owner_professional_id()
        if owner_professional_id is not None and int(pk) == owner_professional_id:
            return Response({'error': 'O administrador vinculado à loja não pode ser excluído.'}, status=status.HTTP_403_FORBIDDEN)
        obj, err = self.object_or_404(pk)
        if err:
            return err
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


class HorarioTrabalhoProfissionalView(GetObjectMixin, APIView):
    """
    Dias e horários de trabalho do profissional.
    GET /clinica-beleza/professionals/<id>/horarios-trabalho/
    PUT /clinica-beleza/professionals/<id>/horarios-trabalho/
    """
    permission_classes = CLINICA_ADMIN
    model_class = Professional
    not_found_message = 'Profissional não encontrado'

    def get(self, request, pk):
        professional, err = self.object_or_404(pk)
        if err:
            return err
        queryset = HorarioTrabalhoProfissional.objects.filter(professional_id=pk).order_by('dia_semana')
        return Response(HorarioTrabalhoProfissionalSerializer(queryset, many=True).data)

    def put(self, request, pk):
        professional, err = self.object_or_404(pk)
        if err:
            return err
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


class ProfessionalCommissionView(GetObjectMixin, APIView):
    """
    GET  /clinica-beleza/professionals/<id>/comissoes/ — lista comissões do profissional.
    POST /clinica-beleza/professionals/<id>/comissoes/ — cria/atualiza comissões (recebe lista).
    """
    permission_classes = CLINICA_ADMIN
    model_class = Professional
    not_found_message = 'Profissional não encontrado'

    def get(self, request, pk):
        professional, err = self.object_or_404(pk)
        if err:
            return err
        try:
            qs = ProfessionalCommission.objects.filter(
                professional_id=pk, is_active=True
            ).select_related('procedure', 'convenio', 'local_atendimento').order_by(
                'tipo', 'procedure__nome', 'convenio__nome',
            )
            return Response(ProfessionalCommissionSerializer(qs, many=True).data)
        except Exception:
            logger.exception('Erro ao listar comissões do profissional %s', pk)
            return Response(
                {'error': 'Erro ao carregar comissões do profissional.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request, pk):
        """Recebe uma lista de comissões. Substitui todas as existentes."""
        professional, err = self.object_or_404(pk)
        if err:
            return err

        if not isinstance(request.data, list):
            return Response(
                {'error': 'Envie uma lista de comissões.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            return self._salvar_comissoes(pk, professional, request.data)
        except Exception:
            logger.exception('Erro ao salvar comissões do profissional %s', pk)
            return Response(
                {'error': 'Erro ao salvar comissões. Verifique os dados e tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _salvar_comissoes(self, pk, professional, itens):
        ProfessionalCommission.objects.filter(professional_id=pk).update(is_active=False)
        created = []
        locais_consulta_vistos = set()
        procedimentos_convenio_vistos = set()
        for item in itens:
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
            elif item.get('tipo') == 'procedimento':
                proc_id = item.get('procedure')
                conv_id = item.get('convenio')
                if not conv_id:
                    return Response(
                        {'convenio': 'Informe o convênio para cada comissão de procedimento.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                chave = (proc_id, conv_id)
                if chave in procedimentos_convenio_vistos:
                    return Response(
                        {'convenio': 'Não repita o mesmo procedimento para o mesmo convênio.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                procedimentos_convenio_vistos.add(chave)
            data = {**item, 'professional': pk}
            serializer = ProfessionalCommissionSerializer(data=data)
            if serializer.is_valid():
                obj = serializer.save(professional=professional, is_active=True)
                created.append(ProfessionalCommissionSerializer(obj).data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(created, status=status.HTTP_200_OK)
