from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.views import BaseModelViewSet
from tenants.middleware import get_current_loja_id

from .models import Agendamento, Cliente, Profissional, Servico
from .serializers import (
    AgendamentoSerializer,
    ClienteSerializer,
    ProfissionalSerializer,
    ServicoSerializer,
)


class ClienteViewSet(BaseModelViewSet):
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["nome", "telefone", "email", "cpf"]

    def get_queryset(self):
        return Cliente.objects.filter(is_active=True).order_by("nome")


class ProfissionalViewSet(BaseModelViewSet):
    serializer_class = ProfissionalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Profissional.objects.filter(is_active=True).order_by("nome")


class ServicoViewSet(BaseModelViewSet):
    serializer_class = ServicoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Servico.objects.filter(is_active=True).order_by("categoria", "nome")


class AgendamentoViewSet(BaseModelViewSet):
    serializer_class = AgendamentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            Agendamento.objects.filter(is_active=True)
            .select_related("cliente", "profissional", "servico")
            .order_by("data", "hora_inicio")
        )
        data = self.request.query_params.get("data")
        if data:
            qs = qs.filter(data=data)
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        profissional_id = self.request.query_params.get("profissional")
        if profissional_id:
            qs = qs.filter(profissional_id=profissional_id)
        return qs

    def perform_create(self, serializer):
        ag = serializer.save()
        from .whatsapp_agenda import enviar_confirmacao_agendamento_salao

        enviar_confirmacao_agendamento_salao(ag, user=self.request.user)

    @action(detail=True, methods=["post"], url_path="confirmar-chegada")
    def confirmar_chegada(self, request, pk=None):
        ag = self.get_object()
        if ag.status in (Agendamento.STATUS_DONE, Agendamento.STATUS_CANCELLED, Agendamento.STATUS_NO_SHOW):
            return Response(
                {"detail": "Agendamento não pode confirmar chegada neste status."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ag.status = Agendamento.STATUS_ARRIVED
        ag.save(update_fields=["status", "updated_at"])
        return Response(AgendamentoSerializer(ag).data)

    @action(detail=True, methods=["post"], url_path="reenviar-mensagem")
    def reenviar_mensagem(self, request, pk=None):
        """Reenvia confirmação WhatsApp (mesmo fluxo da clínica)."""
        ag = self.get_object()
        if ag.status not in (Agendamento.STATUS_SCHEDULED, Agendamento.STATUS_CLIENT_CONFIRMED):
            return Response(
                {"detail": "Só é possível reenviar para agendamentos aguardando ou já confirmados."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if ag.status == Agendamento.STATUS_CLIENT_CONFIRMED:
            # Clínica só reenvia em STATUS_ACIONAVEIS; alinhamos a só SCHEDULED
            return Response(
                {"detail": "Cliente já confirmou. Crie novo agendamento se precisar remarcar."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .whatsapp_agenda import enviar_confirmacao_agendamento_salao

        ok, err = enviar_confirmacao_agendamento_salao(ag, user=request.user)
        if not ok:
            return Response({"detail": err or "Falha ao enviar WhatsApp."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "detail": "Mensagem reenviada."})


class SalaoDashboardViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Próximos agendamentos de hoje + contadores simples."""
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=status.HTTP_400_BAD_REQUEST)

        hoje = timezone.localdate()
        agora = timezone.localtime().time()
        qs = (
            Agendamento.objects.filter(
                is_active=True,
                data=hoje,
                status__in=(
                    Agendamento.STATUS_SCHEDULED,
                    Agendamento.STATUS_CLIENT_CONFIRMED,
                    Agendamento.STATUS_ARRIVED,
                    Agendamento.STATUS_IN_PROGRESS,
                ),
            )
            .select_related("cliente", "profissional", "servico")
            .order_by("hora_inicio")
        )
        # Preferir os que ainda não passaram; se todos passaram, mostrar os 3 próximos da lista
        futuros = [a for a in qs if a.hora_inicio >= agora][:3]
        proximos = futuros or list(qs[:3])

        total_hoje = Agendamento.objects.filter(is_active=True, data=hoje).exclude(
            status=Agendamento.STATUS_CANCELLED,
        ).count()
        concluidos = Agendamento.objects.filter(
            is_active=True, data=hoje, status=Agendamento.STATUS_DONE,
        ).count()

        return Response({
            "data": hoje.isoformat(),
            "total_hoje": total_hoje,
            "concluidos_hoje": concluidos,
            "proximos": AgendamentoSerializer(proximos, many=True).data,
            "loja_id": loja_id,
        })
