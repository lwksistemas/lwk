from datetime import date

from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.views import BaseModelViewSet
from .models import Hospede, Quarto, Tarifa, Reserva, GovernancaTarefa
from .serializers import (
    HospedeSerializer,
    QuartoSerializer,
    TarifaSerializer,
    ReservaSerializer,
    GovernancaTarefaSerializer,
)


class HospedeViewSet(BaseModelViewSet):
    serializer_class = HospedeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Hospede.objects.all()


class QuartoViewSet(BaseModelViewSet):
    serializer_class = QuartoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Quarto.objects.all()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class TarifaViewSet(BaseModelViewSet):
    serializer_class = TarifaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Tarifa.objects.all()
        tipo_quarto = self.request.query_params.get('tipo_quarto')
        if tipo_quarto:
            qs = qs.filter(tipo_quarto=tipo_quarto)
        return qs


class ReservaViewSet(BaseModelViewSet):
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Reserva.objects.select_related('hospede', 'quarto', 'tarifa').all()
        params = self.request.query_params
        if params.get('status'):
            qs = qs.filter(status=params.get('status'))
        if params.get('data_checkin'):
            qs = qs.filter(data_checkin=params.get('data_checkin'))
        if params.get('data_checkout'):
            qs = qs.filter(data_checkout=params.get('data_checkout'))
        if params.get('quarto_id'):
            qs = qs.filter(quarto_id=params.get('quarto_id'))
        if params.get('hospede_id'):
            qs = qs.filter(hospede_id=params.get('hospede_id'))
        return qs

    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        reserva = self.get_object()
        if reserva.status in (Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW):
            return Response({'detail': 'Reserva cancelada/no-show não permite check-in.'}, status=status.HTTP_400_BAD_REQUEST)
        reserva.status = Reserva.STATUS_CHECKIN
        reserva.save(update_fields=['status', 'updated_at'])
        try:
            quarto = reserva.quarto
            quarto.status = Quarto.STATUS_OCUPADO
            quarto.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        reserva = self.get_object()
        if reserva.status != Reserva.STATUS_CHECKIN:
            return Response({'detail': 'Apenas reservas em check-in podem fazer check-out.'}, status=status.HTTP_400_BAD_REQUEST)
        reserva.status = Reserva.STATUS_CHECKOUT
        reserva.save(update_fields=['status', 'updated_at'])
        try:
            quarto = reserva.quarto
            quarto.status = Quarto.STATUS_LIMPEZA
            quarto.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass
        return Response(self.get_serializer(reserva).data)

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        hoje = date.today()
        qs = self.get_queryset()
        quartos_total = Quarto.objects.count()
        quartos_ocupados = Quarto.objects.filter(status=Quarto.STATUS_OCUPADO).count()

        checkins_hoje = qs.filter(data_checkin=hoje).exclude(status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW]).count()
        checkouts_hoje = qs.filter(data_checkout=hoje).exclude(status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW]).count()

        # ADR simples: média de valor_diaria das reservas confirmadas/checkin/checkout no mês
        primeiro_dia_mes = hoje.replace(day=1)
        adr = (
            qs.filter(
                data_checkin__gte=primeiro_dia_mes,
                data_checkin__lte=hoje,
                status__in=[Reserva.STATUS_CONFIRMADA, Reserva.STATUS_CHECKIN, Reserva.STATUS_CHECKOUT],
            )
            .aggregate(v=Avg('valor_diaria'))
            .get('v')
        ) or 0

        ocupacao_pct = 0
        if quartos_total:
            ocupacao_pct = (quartos_ocupados / quartos_total) * 100

        pendencias = GovernancaTarefa.objects.filter(status__in=[GovernancaTarefa.STATUS_ABERTA, GovernancaTarefa.STATUS_EM_ANDAMENTO]).count()

        return Response(
            {
                'ocupacao_hoje_percent': round(float(ocupacao_pct), 2),
                'quartos_total': quartos_total,
                'quartos_ocupados': quartos_ocupados,
                'checkins_hoje': checkins_hoje,
                'checkouts_hoje': checkouts_hoje,
                'adr_mes': float(adr),
                'pendencias_governanca': pendencias,
            }
        )


class HotelDashboardViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        hoje = date.today()

        # KPIs (mesma base do endpoint /reservas/estatisticas/)
        quartos_total = Quarto.objects.count()
        quartos_ocupados = Quarto.objects.filter(status=Quarto.STATUS_OCUPADO).count()
        ocupacao_pct = (quartos_ocupados / quartos_total) * 100 if quartos_total else 0

        reservas_qs = Reserva.objects.select_related('hospede', 'quarto', 'tarifa').all()
        checkins_hoje = (
            reservas_qs.filter(data_checkin=hoje)
            .exclude(status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW])
            .count()
        )
        checkouts_hoje = (
            reservas_qs.filter(data_checkout=hoje)
            .exclude(status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW])
            .count()
        )

        primeiro_dia_mes = hoje.replace(day=1)
        adr = (
            reservas_qs.filter(
                data_checkin__gte=primeiro_dia_mes,
                data_checkin__lte=hoje,
                status__in=[Reserva.STATUS_CONFIRMADA, Reserva.STATUS_CHECKIN, Reserva.STATUS_CHECKOUT],
            )
            .aggregate(v=Avg('valor_diaria'))
            .get('v')
        ) or 0

        pendencias_count = GovernancaTarefa.objects.filter(
            status__in=[GovernancaTarefa.STATUS_ABERTA, GovernancaTarefa.STATUS_EM_ANDAMENTO]
        ).count()

        # Listas operacionais
        chegadas = (
            reservas_qs.filter(data_checkin=hoje)
            .exclude(status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW])
            .order_by('status', 'quarto__numero', 'id')[:20]
        )
        saidas = (
            reservas_qs.filter(data_checkout=hoje)
            .exclude(status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW])
            .order_by('status', 'quarto__numero', 'id')[:20]
        )
        pendencias = (
            GovernancaTarefa.objects.select_related('quarto')
            .filter(status__in=[GovernancaTarefa.STATUS_ABERTA, GovernancaTarefa.STATUS_EM_ANDAMENTO])
            .order_by('-prioridade', 'status', 'id')[:20]
        )

        data = {
            'kpis': {
                'ocupacao_hoje_percent': round(float(ocupacao_pct), 2),
                'quartos_total': quartos_total,
                'quartos_ocupados': quartos_ocupados,
                'checkins_hoje': checkins_hoje,
                'checkouts_hoje': checkouts_hoje,
                'adr_mes': float(adr),
                'pendencias_governanca': pendencias_count,
            },
            'chegadas_hoje': [
                {
                    'id': r.id,
                    'status': r.status,
                    'hospede_nome': getattr(r.hospede, 'nome', '') if r.hospede_id else '',
                    'quarto_numero': getattr(r.quarto, 'numero', '') if r.quarto_id else '',
                    'quarto_nome': getattr(r.quarto, 'nome', '') if r.quarto_id else '',
                    'data_checkin': r.data_checkin,
                    'data_checkout': r.data_checkout,
                }
                for r in chegadas
            ],
            'saidas_hoje': [
                {
                    'id': r.id,
                    'status': r.status,
                    'hospede_nome': getattr(r.hospede, 'nome', '') if r.hospede_id else '',
                    'quarto_numero': getattr(r.quarto, 'numero', '') if r.quarto_id else '',
                    'quarto_nome': getattr(r.quarto, 'nome', '') if r.quarto_id else '',
                    'data_checkin': r.data_checkin,
                    'data_checkout': r.data_checkout,
                }
                for r in saidas
            ],
            'pendencias_governanca': [
                {
                    'id': t.id,
                    'tipo': t.tipo,
                    'status': t.status,
                    'prioridade': t.prioridade,
                    'descricao': t.descricao,
                    'quarto_numero': getattr(t.quarto, 'numero', '') if t.quarto_id else '',
                }
                for t in pendencias
            ],
        }
        return Response(data)


class GovernancaTarefaViewSet(BaseModelViewSet):
    serializer_class = GovernancaTarefaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = GovernancaTarefa.objects.select_related('quarto').all()
        params = self.request.query_params
        if params.get('status'):
            qs = qs.filter(status=params.get('status'))
        if params.get('tipo'):
            qs = qs.filter(tipo=params.get('tipo'))
        if params.get('quarto_id'):
            qs = qs.filter(quarto_id=params.get('quarto_id'))
        return qs

    @action(detail=True, methods=['post'])
    def concluir(self, request, pk=None):
        tarefa = self.get_object()
        tarefa.status = GovernancaTarefa.STATUS_CONCLUIDA
        tarefa.concluido_em = timezone.now()
        tarefa.save(update_fields=['status', 'concluido_em', 'updated_at'])
        return Response(self.get_serializer(tarefa).data)

