import logging
from datetime import date, timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.views import BaseModelViewSet
from .models import Hospede, Quarto, Tarifa, Reserva, GovernancaTarefa, Funcionario, ReservaTemplate, ReservaAssinatura
from .serializers import (
    HospedeSerializer,
    QuartoSerializer,
    TarifaSerializer,
    ReservaSerializer,
    GovernancaTarefaSerializer,
    FuncionarioSerializer,
    ReservaTemplateSerializer,
)

logger = logging.getLogger(__name__)


class HospedeViewSet(BaseModelViewSet):
    serializer_class = HospedeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Hospede.objects.all()


class QuartoViewSet(BaseModelViewSet):
    serializer_class = QuartoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Quarto.objects.filter(is_active=True)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class TarifaViewSet(BaseModelViewSet):
    serializer_class = TarifaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Tarifa.objects.filter(is_active=True)
        tipo_quarto = self.request.query_params.get('tipo_quarto')
        if tipo_quarto:
            qs = qs.filter(tipo_quarto=tipo_quarto)
        return qs


class ReservaViewSet(BaseModelViewSet):
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Reserva.objects.select_related('hospede', 'quarto', 'tarifa').filter(is_active=True)
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
            return Response(
                {'detail': 'Reserva cancelada/no-show não permite check-in.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reserva.status = Reserva.STATUS_CHECKIN
        reserva.save(update_fields=['status', 'updated_at'])
        quarto = reserva.quarto
        quarto.status = Quarto.STATUS_OCUPADO
        quarto.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        reserva = self.get_object()
        if reserva.status != Reserva.STATUS_CHECKIN:
            return Response(
                {'detail': 'Apenas reservas em check-in podem fazer check-out.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reserva.status = Reserva.STATUS_CHECKOUT
        reserva.save(update_fields=['status', 'updated_at'])
        quarto = reserva.quarto
        quarto.status = Quarto.STATUS_LIMPEZA
        quarto.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=['post'])
    def enviar_para_assinatura(self, request, pk=None):
        """Envia confirmação de reserva para assinatura digital do hóspede."""
        from core.assinatura_service import criar_assinatura, enviar_email_parte1
        from .assinatura_adapter import ReservaAssinaturaAdapter
        from tenants.middleware import get_current_loja_id

        reserva = self.get_object()
        loja_id = get_current_loja_id()
        adapter = ReservaAssinaturaAdapter()

        if not reserva.hospede or not reserva.hospede.email:
            return Response({'detail': 'Hóspede não possui email cadastrado.'}, status=status.HTTP_400_BAD_REQUEST)

        if reserva.status_assinatura in ('aguardando_hospede', 'aguardando_funcionario'):
            return Response(
                {'detail': f'Reserva já está em processo de assinatura: {reserva.get_status_assinatura_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Preencher conteudo_confirmacao com template padrão se vazio
        if not reserva.conteudo_confirmacao.strip():
            tpl = ReservaTemplate.objects.filter(loja_id=loja_id, is_padrao=True, ativo=True).first()
            if not tpl:
                tpl = ReservaTemplate.objects.filter(loja_id=loja_id, ativo=True).first()
            if tpl:
                diarias = (reserva.data_checkout - reserva.data_checkin).days if reserva.data_checkin and reserva.data_checkout else 0
                conteudo = tpl.conteudo
                conteudo = conteudo.replace('{hospede}', reserva.hospede.nome if reserva.hospede else '')
                conteudo = conteudo.replace('{quarto}', str(reserva.quarto.numero) if reserva.quarto else '')
                conteudo = conteudo.replace('{checkin}', reserva.data_checkin.strftime('%d/%m/%Y') if reserva.data_checkin else '')
                conteudo = conteudo.replace('{checkout}', reserva.data_checkout.strftime('%d/%m/%Y') if reserva.data_checkout else '')
                conteudo = conteudo.replace('{valor_total}', f'R$ {reserva.valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if reserva.valor_total else 'R$ 0,00')
                conteudo = conteudo.replace('{diarias}', str(diarias))
                reserva.conteudo_confirmacao = conteudo
                reserva.save(update_fields=['conteudo_confirmacao', 'updated_at'])

        assinatura = criar_assinatura(adapter, reserva, 'hospede', loja_id)
        reserva.status_assinatura = 'aguardando_hospede'
        reserva.save(update_fields=['status_assinatura', 'updated_at'])

        ok, err = enviar_email_parte1(adapter, reserva, assinatura, loja_id)
        if ok:
            return Response({
                'message': f'Email de assinatura enviado para {reserva.hospede.email}',
                'status_assinatura': 'aguardando_hospede',
            })

        # Reverter
        reserva.status_assinatura = 'rascunho'
        reserva.save(update_fields=['status_assinatura', 'updated_at'])
        assinatura.delete()
        return Response({'detail': err or 'Erro ao enviar email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def reenviar_para_assinatura(self, request, pk=None):
        """Reenvia link de assinatura."""
        from core.assinatura_service import reenviar_link
        from .assinatura_adapter import ReservaAssinaturaAdapter
        from tenants.middleware import get_current_loja_id

        reserva = self.get_object()
        adapter = ReservaAssinaturaAdapter()
        ok, msg, err = reenviar_link(adapter, reserva, get_current_loja_id())
        if ok:
            return Response({'message': msg})
        return Response({'detail': err or 'Erro ao reenviar.'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Baixa PDF da confirmação de reserva."""
        from django.http import HttpResponse
        from .pdf_reserva import gerar_pdf_reserva

        reserva = self.get_object()
        incluir = reserva.status_assinatura == 'concluido'
        pdf = gerar_pdf_reserva(reserva, incluir_assinaturas=incluir)
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reserva_{reserva.id}.pdf"'
        return response

    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        hoje = date.today()
        qs = self.get_queryset()
        quartos_qs = Quarto.objects.filter(is_active=True)
        quartos_total = quartos_qs.count()
        quartos_ocupados = quartos_qs.filter(status=Quarto.STATUS_OCUPADO).count()

        checkins_hoje = qs.filter(data_checkin=hoje).exclude(
            status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW]
        ).count()
        checkouts_hoje = qs.filter(data_checkout=hoje).exclude(
            status__in=[Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW]
        ).count()

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

        ocupacao_pct = (quartos_ocupados / quartos_total) * 100 if quartos_total else 0

        pendencias = GovernancaTarefa.objects.filter(
            is_active=True,
            status__in=[GovernancaTarefa.STATUS_ABERTA, GovernancaTarefa.STATUS_EM_ANDAMENTO],
        ).count()

        return Response({
            'ocupacao_hoje_percent': round(float(ocupacao_pct), 2),
            'quartos_total': quartos_total,
            'quartos_ocupados': quartos_ocupados,
            'checkins_hoje': checkins_hoje,
            'checkouts_hoje': checkouts_hoje,
            'adr_mes': float(adr),
            'pendencias_governanca': pendencias,
        })


class HotelDashboardViewSet(ViewSet):
    """
    Dashboard do hotel — todas as queries filtradas pelo LojaIsolationManager
    para garantir isolamento multi-tenant.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        hoje = date.today()

        # Querysets isolados por loja (LojaIsolationManager filtra automaticamente)
        quartos_qs = Quarto.objects.filter(is_active=True)
        reservas_qs = Reserva.objects.select_related('hospede', 'quarto', 'tarifa').filter(is_active=True)
        gov_qs = GovernancaTarefa.objects.filter(is_active=True)

        # KPIs
        quartos_total = quartos_qs.count()
        quartos_ocupados = quartos_qs.filter(status=Quarto.STATUS_OCUPADO).count()
        ocupacao_pct = (quartos_ocupados / quartos_total) * 100 if quartos_total else 0

        excluir_status = [Reserva.STATUS_CANCELADA, Reserva.STATUS_NO_SHOW]
        checkins_hoje = reservas_qs.filter(data_checkin=hoje).exclude(status__in=excluir_status).count()
        checkouts_hoje = reservas_qs.filter(data_checkout=hoje).exclude(status__in=excluir_status).count()

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

        pendencias_count = gov_qs.filter(
            status__in=[GovernancaTarefa.STATUS_ABERTA, GovernancaTarefa.STATUS_EM_ANDAMENTO]
        ).count()

        # Listas operacionais
        chegadas = (
            reservas_qs.filter(data_checkin=hoje)
            .exclude(status__in=excluir_status)
            .order_by('status', 'quarto__numero', 'id')[:20]
        )
        saidas = (
            reservas_qs.filter(data_checkout=hoje)
            .exclude(status__in=excluir_status)
            .order_by('status', 'quarto__numero', 'id')[:20]
        )
        pendencias = (
            gov_qs.select_related('quarto')
            .filter(status__in=[GovernancaTarefa.STATUS_ABERTA, GovernancaTarefa.STATUS_EM_ANDAMENTO])
            .order_by('-prioridade', 'status', 'id')[:20]
        )

        # Relatórios
        start_30 = hoje - timedelta(days=29)
        rev_rows = (
            reservas_qs.filter(data_checkin__gte=start_30, data_checkin__lte=hoje)
            .exclude(status__in=excluir_status)
            .values('data_checkin')
            .annotate(total=Sum('valor_total'))
        )
        rev_map = {row['data_checkin']: float(row['total'] or 0) for row in rev_rows}
        receita_diaria = []
        d = start_30
        while d <= hoje:
            receita_diaria.append({'data': d.isoformat(), 'valor': round(rev_map.get(d, 0.0), 2)})
            d += timedelta(days=1)
        receita_total_30d = round(sum(r['valor'] for r in receita_diaria), 2)

        ocup_rows = (
            quartos_qs
            .values('tipo')
            .annotate(total=Count('id'), ocupados=Count('id', filter=Q(status=Quarto.STATUS_OCUPADO)))
            .order_by('-total')
        )
        ocupacao_por_tipo = []
        for row in ocup_rows:
            label = (row.get('tipo') or '').strip() or 'Sem categoria'
            tot = int(row['total'] or 0)
            occ = int(row['ocupados'] or 0)
            pct = round((occ / tot) * 100, 1) if tot else 0.0
            ocupacao_por_tipo.append({'tipo': label, 'total': tot, 'ocupados': occ, 'ocupacao_percent': pct})

        r_mes = reservas_qs.filter(data_checkin__gte=primeiro_dia_mes, data_checkin__lte=hoje)
        reservas_mes = r_mes.count()
        no_show_mes = r_mes.filter(status=Reserva.STATUS_NO_SHOW).count()
        cancelamentos_mes = r_mes.filter(status=Reserva.STATUS_CANCELADA).count()
        tarefas_concluidas_mes = gov_qs.filter(
            status=GovernancaTarefa.STATUS_CONCLUIDA,
            concluido_em__date__gte=primeiro_dia_mes,
            concluido_em__date__lte=hoje,
        ).count()
        base = max(reservas_mes, 1)
        taxa_problema = ((no_show_mes + cancelamentos_mes) / base) * 100
        indice_operacional = max(0.0, min(10.0, round(10.0 - min(5.0, taxa_problema / 10.0), 1)))

        relatorios = {
            'receita_diaria': receita_diaria,
            'receita_total_30d': receita_total_30d,
            'ocupacao_por_tipo': ocupacao_por_tipo,
            'indicadores': {
                'reservas_mes': reservas_mes,
                'no_show_mes': no_show_mes,
                'cancelamentos_mes': cancelamentos_mes,
                'tarefas_concluidas_mes': tarefas_concluidas_mes,
                'indice_operacional': indice_operacional,
            },
        }

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
            'relatorios': relatorios,
        }
        return Response(data)


class GovernancaTarefaViewSet(BaseModelViewSet):
    serializer_class = GovernancaTarefaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = GovernancaTarefa.objects.select_related('quarto').filter(is_active=True)
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


class FuncionarioViewSet(BaseModelViewSet):
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Funcionario.objects.filter(is_active=True)


class ReservaTemplateViewSet(BaseModelViewSet):
    """Templates de confirmação de reserva."""
    serializer_class = ReservaTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReservaTemplate.objects.filter(ativo=True)

    def perform_create(self, serializer):
        instance = serializer.save()
        if instance.is_padrao:
            ReservaTemplate.objects.filter(loja_id=instance.loja_id, is_padrao=True).exclude(pk=instance.pk).update(is_padrao=False)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.is_padrao:
            ReservaTemplate.objects.filter(loja_id=instance.loja_id, is_padrao=True).exclude(pk=instance.pk).update(is_padrao=False)


# ---------------------------------------------------------------------------
# View pública de assinatura de reserva (sem autenticação)
# ---------------------------------------------------------------------------
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings


def _configurar_tenant_reserva(loja_id):
    """Configura tenant para assinatura pública de reserva."""
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from superadmin.models import Loja
    from core.db_config import ensure_loja_database_config

    set_current_loja_id(loja_id)
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        return 'Link de assinatura inválido.'

    db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", "")}'
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        return 'Serviço temporariamente indisponível.'

    set_current_tenant_db(db_name)
    return None


@method_decorator(csrf_exempt, name='dispatch')
class ReservaAssinaturaPublicaView(View):
    """
    View pública para assinatura digital de reservas.
    GET /api/hotel/assinar-reserva/{token}/ — dados da reserva
    POST /api/hotel/assinar-reserva/{token}/ — registra assinatura
    """

    def get(self, request, token):
        from core.assinatura_service import decodificar_token, normalizar_token_url
        from .assinatura_adapter import ReservaAssinaturaAdapter

        token = normalizar_token_url(token)
        payload = decodificar_token(token)
        if not payload or not payload.get('loja_id'):
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        loja_id = payload['loja_id']
        err = _configurar_tenant_reserva(loja_id)
        if err:
            return JsonResponse({'error': err}, status=400)

        adapter = ReservaAssinaturaAdapter()
        assinatura = adapter.buscar_assinatura_por_token(token)
        if not assinatura:
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)
        if assinatura.assinado:
            return JsonResponse({'error': 'Este documento já foi assinado.'}, status=400)
        if assinatura.is_expirado:
            return JsonResponse({'error': 'Este link expirou.'}, status=400)

        reserva = assinatura.reserva
        return JsonResponse({
            'tipo_documento': 'reserva',
            'titulo': adapter.get_titulo(reserva),
            'valor_total': str(reserva.valor_total or '0.00'),
            'nome_assinante': assinatura.nome_assinante,
            'tipo_assinante': assinatura.tipo,
            'tipo_assinante_display': assinatura.get_tipo_display(),
            'hospede_nome': reserva.hospede.nome if reserva.hospede else '',
            'quarto': f'{reserva.quarto.numero} - {reserva.quarto.nome or ""}' if reserva.quarto else '',
            'data_checkin': str(reserva.data_checkin) if reserva.data_checkin else '',
            'data_checkout': str(reserva.data_checkout) if reserva.data_checkout else '',
            'conteudo_confirmacao': reserva.conteudo_confirmacao or '',
        })

    def post(self, request, token):
        from core.assinatura_service import (
            decodificar_token, normalizar_token_url, registrar_assinatura,
            criar_assinatura, enviar_email_parte2, enviar_pdf_final,
        )
        from .assinatura_adapter import ReservaAssinaturaAdapter

        token = normalizar_token_url(token)
        payload = decodificar_token(token)
        if not payload or not payload.get('loja_id'):
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        loja_id = payload['loja_id']
        err = _configurar_tenant_reserva(loja_id)
        if err:
            return JsonResponse({'error': err}, status=400)

        adapter = ReservaAssinaturaAdapter()
        assinatura = adapter.buscar_assinatura_por_token(token)
        if not assinatura:
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)
        if assinatura.assinado:
            return JsonResponse({'error': 'Este documento já foi assinado.'}, status=400)
        if assinatura.is_expirado:
            return JsonResponse({'error': 'Este link expirou.'}, status=400)

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0'))
        if ',' in ip:
            ip = ip.split(',')[0].strip()
        ua = request.META.get('HTTP_USER_AGENT', '')

        novo_status = registrar_assinatura(adapter, assinatura, ip, ua)
        reserva = assinatura.reserva

        # Se hóspede assinou, criar token para funcionário e enviar email
        if novo_status == 'aguardando_funcionario':
            assinatura_func = criar_assinatura(adapter, reserva, 'funcionario', loja_id)
            enviar_email_parte2(adapter, reserva, assinatura_func, loja_id)

        # Se funcionário assinou, enviar PDF final
        if novo_status == 'concluido':
            enviar_pdf_final(adapter, reserva, loja_id)

        STATUS_DISPLAY = {
            'aguardando_funcionario': 'Aguardando Funcionário',
            'concluido': 'Concluído',
        }

        return JsonResponse({
            'success': True,
            'proximo_status': novo_status,
            'proximo_status_display': STATUS_DISPLAY.get(novo_status, novo_status),
        })


@method_decorator(csrf_exempt, name='dispatch')
class ReservaAssinaturaPdfView(View):
    """
    View pública para baixar PDF da reserva (sem autenticação).
    GET /api/hotel/assinar-reserva/{token}/pdf/
    """

    def get(self, request, token):
        from core.assinatura_service import decodificar_token, normalizar_token_url
        from .assinatura_adapter import ReservaAssinaturaAdapter
        from .pdf_reserva import gerar_pdf_reserva
        from django.http import HttpResponse

        token = normalizar_token_url(token)
        payload = decodificar_token(token)
        if not payload or not payload.get('loja_id'):
            return JsonResponse({'error': 'Link inválido.'}, status=400)

        loja_id = payload['loja_id']
        err = _configurar_tenant_reserva(loja_id)
        if err:
            return JsonResponse({'error': err}, status=400)

        adapter = ReservaAssinaturaAdapter()
        assinatura = adapter.buscar_assinatura_por_token(token)
        if not assinatura:
            return JsonResponse({'error': 'Link inválido.'}, status=400)

        reserva = assinatura.reserva
        pdf = gerar_pdf_reserva(reserva, incluir_assinaturas=False)
        response = HttpResponse(pdf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="confirmacao_reserva_{reserva.id}.pdf"'
        return response
