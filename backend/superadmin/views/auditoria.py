import logging

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

logger = logging.getLogger(__name__)
import contextlib

from ..cache import cached_stat
from ..models import ViolacaoSeguranca
from ..serializers import ViolacaoSegurancaListSerializer, ViolacaoSegurancaSerializer
from .permissions import IsSuperAdmin


class HistoricoAcessoGlobalViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para Histórico de Acesso Global (APENAS LEITURA)
    Apenas SuperAdmin pode acessar.
    """

    permission_classes = [IsSuperAdmin]

    def get_serializer_class(self):
        from ..serializers import HistoricoAcessoGlobalListSerializer, HistoricoAcessoGlobalSerializer
        if self.action == "list":
            return HistoricoAcessoGlobalListSerializer
        return HistoricoAcessoGlobalSerializer

    def get_queryset(self):
        from datetime import datetime

        from ..models import HistoricoAcessoGlobal

        queryset = HistoricoAcessoGlobal.objects.select_related(
            "user", "loja", "loja__tipo_loja",
        ).all()

        params = self.request.query_params

        usuario_email = params.get("usuario_email")
        if usuario_email:
            queryset = queryset.filter(usuario_email__icontains=usuario_email)

        loja_id = params.get("loja_id")
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)

        loja_slug = params.get("loja_slug")
        if loja_slug:
            queryset = queryset.filter(loja_slug__iexact=loja_slug)

        loja_nome = params.get("loja_nome")
        if loja_nome:
            queryset = queryset.filter(loja_nome__icontains=loja_nome)

        acao = params.get("acao")
        if acao:
            queryset = queryset.filter(acao=acao)

        data_inicio = params.get("data_inicio")
        data_fim = params.get("data_fim")

        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
                queryset = queryset.filter(created_at__gte=data_inicio_dt)
            except ValueError:
                pass

        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
                from datetime import timedelta
                data_fim_dt = data_fim_dt + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=data_fim_dt)
            except ValueError:
                pass

        ip_address = params.get("ip_address")
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)

        sucesso = params.get("sucesso")
        if sucesso is not None:
            sucesso_bool = sucesso.lower() == "true"
            queryset = queryset.filter(sucesso=sucesso_bool)

        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(usuario_nome__icontains=search) |
                Q(usuario_email__icontains=search) |
                Q(loja_nome__icontains=search) |
                Q(loja_slug__icontains=search),
            )

        incluir_integracoes = params.get("incluir_integracoes", "").lower() in ("1", "true", "yes")
        incluir_lojas_removidas = params.get("incluir_lojas_removidas", "").lower() in ("1", "true", "yes")
        if not incluir_integracoes or not incluir_lojas_removidas:
            from ..historico_auditoria_filters import queryset_auditoria_visivel
            queryset = queryset_auditoria_visivel(
                queryset,
                incluir_integracoes=incluir_integracoes,
                incluir_lojas_removidas=incluir_lojas_removidas,
            )

        return queryset.order_by("-created_at")

    @action(detail=False, methods=["get"])
    def estatisticas(self, request):
        """Retorna estatísticas do histórico"""
        from datetime import datetime, timedelta

        from django.db.models import Count

        from ..models import HistoricoAcessoGlobal

        data_inicio = request.query_params.get("data_inicio")
        data_fim = request.query_params.get("data_fim")

        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not data_fim:
            data_fim = datetime.now().strftime("%Y-%m-%d")

        try:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            return Response(
                {"error": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio_dt,
            created_at__lt=data_fim_dt,
        )
        from ..historico_auditoria_filters import (
            queryset_auditoria_visivel,
            queryset_ranking_lojas,
            queryset_ranking_usuarios,
        )
        qs_visivel = queryset_auditoria_visivel(qs)
        qs_lojas = queryset_ranking_lojas(qs)
        qs_usuarios = queryset_ranking_usuarios(qs)

        stats = {
            "periodo": {"inicio": data_inicio, "fim": data_fim},
            "total_acessos": qs_visivel.count(),
            "total_logins": qs_visivel.filter(acao="login").count(),
            "total_sucesso": qs_visivel.filter(sucesso=True).count(),
            "total_erros": qs_visivel.filter(sucesso=False).count(),
            "acoes_por_tipo": list(
                qs_visivel.values("acao").annotate(total=Count("id")).order_by("-total"),
            ),
            "usuarios_mais_ativos": [
                {
                    "usuario_nome": item["usuario_nome"],
                    "usuario_email": item["usuario_email"],
                    "total": item["total"],
                }
                for item in qs_usuarios.values("usuario_email", "usuario_nome")
                .annotate(total=Count("id")).order_by("-total")[:10]
            ],
            "lojas_mais_ativas": [
                {
                    "loja_nome": item["loja__nome"],
                    "loja_id": item["loja_id"],
                    "total": item["total"],
                }
                for item in qs_lojas.values("loja_id", "loja__nome")
                .annotate(total=Count("id")).order_by("-total")[:10]
            ],
            "ips_mais_frequentes": list(
                qs_visivel.values("ip_address").annotate(total=Count("id")).order_by("-total")[:10],
            ),
        }

        return Response(stats)

    @action(detail=False, methods=["get"])
    def atividade_temporal(self, request):
        """Retorna atividade ao longo do tempo (para gráficos)"""
        from datetime import datetime, timedelta

        from django.db.models import Count
        from django.db.models.functions import TruncDate, TruncHour, TruncMonth

        from ..models import HistoricoAcessoGlobal

        data_inicio = request.query_params.get("data_inicio")
        data_fim = request.query_params.get("data_fim")

        if not data_inicio:
            data_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        if not data_fim:
            data_fim = datetime.now().strftime("%Y-%m-%d")

        try:
            data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            return Response(
                {"error": "Formato de data inválido. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dias_diferenca = (data_fim_dt - data_inicio_dt).days

        qs = HistoricoAcessoGlobal.objects.filter(
            created_at__gte=data_inicio_dt,
            created_at__lt=data_fim_dt,
        )

        if dias_diferenca <= 2:
            atividade = list(
                qs.annotate(periodo=TruncHour("created_at"))
                .values("periodo")
                .annotate(
                    total=Count("id"),
                    sucessos=Count("id", filter=Q(sucesso=True)),
                    erros=Count("id", filter=Q(sucesso=False)),
                ).order_by("periodo"),
            )
            granularidade = "hora"
        elif dias_diferenca <= 90:
            atividade = list(
                qs.annotate(periodo=TruncDate("created_at"))
                .values("periodo")
                .annotate(
                    total=Count("id"),
                    sucessos=Count("id", filter=Q(sucesso=True)),
                    erros=Count("id", filter=Q(sucesso=False)),
                ).order_by("periodo"),
            )
            granularidade = "dia"
        else:
            atividade = list(
                qs.annotate(periodo=TruncMonth("created_at"))
                .values("periodo")
                .annotate(
                    total=Count("id"),
                    sucessos=Count("id", filter=Q(sucesso=True)),
                    erros=Count("id", filter=Q(sucesso=False)),
                ).order_by("periodo"),
            )
            granularidade = "mes"

        for item in atividade:
            if granularidade == "hora":
                item["periodo"] = item["periodo"].strftime("%d/%m/%Y %H:00")
            elif granularidade == "dia":
                item["periodo"] = item["periodo"].strftime("%d/%m/%Y")
            else:
                item["periodo"] = item["periodo"].strftime("%m/%Y")

        return Response({
            "periodo": {"inicio": data_inicio, "fim": data_fim},
            "granularidade": granularidade,
            "atividade": atividade,
        })

    @action(detail=False, methods=["get"])
    def exportar(self, request):
        """Exporta histórico em CSV"""
        import csv
        from datetime import datetime

        from django.http import HttpResponse

        queryset = self.get_queryset()[:10000]

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="historico_acessos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Data/Hora", "Usuário", "Email", "Loja", "Ação",
            "Recurso", "IP", "Navegador", "SO", "Sucesso",
        ])

        for item in queryset:
            writer.writerow([
                item.created_at.strftime("%d/%m/%Y %H:%M:%S"),
                item.usuario_nome,
                item.usuario_email,
                item.loja_nome or "SuperAdmin",
                item.get_acao_display(),
                item.recurso or "-",
                item.ip_address,
                item.navegador,
                item.sistema_operacional,
                "Sim" if item.sucesso else "Não",
            ])

        return response

    @action(detail=False, methods=["get"])
    def exportar_json(self, request):
        """Exporta histórico em JSON"""
        from datetime import datetime

        from django.http import JsonResponse

        queryset = self.get_queryset()[:10000]
        serializer = self.get_serializer(queryset, many=True)

        response = JsonResponse({
            "total": queryset.count(),
            "exportado_em": datetime.now().isoformat(),
            "dados": serializer.data,
        }, safe=False)

        response["Content-Disposition"] = f'attachment; filename="historico_acessos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response

    @action(detail=True, methods=["get"])
    def contexto_temporal(self, request, pk=None):
        """Retorna contexto temporal de um log específico"""
        from ..models import HistoricoAcessoGlobal

        log_atual = self.get_object()

        try:
            antes = int(request.query_params.get("antes", 5))
            depois = int(request.query_params.get("depois", 5))
        except ValueError:
            return Response(
                {"error": 'Parâmetros "antes" e "depois" devem ser números inteiros'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        antes = min(antes, 20)
        depois = min(depois, 20)

        logs_anteriores = HistoricoAcessoGlobal.objects.filter(
            usuario_email=log_atual.usuario_email,
            created_at__lt=log_atual.created_at,
        ).select_related("user", "loja").order_by("-created_at")[:antes]

        logs_posteriores = HistoricoAcessoGlobal.objects.filter(
            usuario_email=log_atual.usuario_email,
            created_at__gt=log_atual.created_at,
        ).select_related("user", "loja").order_by("created_at")[:depois]

        from ..serializers import HistoricoAcessoGlobalListSerializer

        return Response({
            "log_atual": HistoricoAcessoGlobalListSerializer(log_atual).data,
            "logs_anteriores": HistoricoAcessoGlobalListSerializer(logs_anteriores, many=True).data,
            "logs_posteriores": HistoricoAcessoGlobalListSerializer(logs_posteriores, many=True).data,
            "total_anteriores": logs_anteriores.count(),
            "total_posteriores": logs_posteriores.count(),
        })

    @action(detail=False, methods=["get"])
    def busca_avancada(self, request):
        """Busca avançada com texto livre"""
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response(
                {"error": 'Parâmetro "q" (termo de busca) é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(
            Q(usuario_nome__icontains=query) |
            Q(usuario_email__icontains=query) |
            Q(loja_nome__icontains=query) |
            Q(loja_slug__icontains=query) |
            Q(recurso__icontains=query) |
            Q(detalhes__icontains=query) |
            Q(url__icontains=query) |
            Q(user_agent__icontains=query) |
            Q(ip_address__icontains=query),
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                "termo_busca": query,
                "total_encontrado": queryset.count(),
                "resultados": serializer.data,
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "termo_busca": query,
            "total_encontrado": queryset.count(),
            "resultados": serializer.data,
        })


class ViolacaoSegurancaViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar violações de segurança"""

    permission_classes = [IsSuperAdmin]

    def get_serializer_class(self):
        if self.action == "list":
            return ViolacaoSegurancaListSerializer
        return ViolacaoSegurancaSerializer

    def get_queryset(self):
        from datetime import datetime

        from django.db.models import Case, IntegerField, When

        queryset = ViolacaoSeguranca.objects.all().select_related(
            "user", "loja", "resolvido_por",
        ).prefetch_related("logs_relacionados")

        params = self.request.query_params
        status_filter = params.get("status")
        criticidade = params.get("criticidade")
        tipo = params.get("tipo")
        loja_id = params.get("loja_id")
        usuario_email = params.get("usuario_email")
        data_inicio = params.get("data_inicio")
        data_fim = params.get("data_fim")

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if criticidade:
            queryset = queryset.filter(criticidade=criticidade)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if loja_id:
            queryset = queryset.filter(loja_id=loja_id)
        if usuario_email:
            queryset = queryset.filter(usuario_email__icontains=usuario_email)
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d")
                queryset = queryset.filter(created_at__gte=data_inicio_dt)
            except ValueError:
                pass
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d")
                from datetime import timedelta
                data_fim_dt = data_fim_dt + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=data_fim_dt)
            except ValueError:
                pass

        created_at_gte = params.get("created_at__gte")
        if created_at_gte:
            try:
                from django.utils.dateparse import parse_datetime
                dt = parse_datetime(created_at_gte)
                if dt:
                    queryset = queryset.filter(created_at__gte=dt)
            except (ValueError, TypeError):
                pass

        criticidade_in = params.get("criticidade__in")
        if criticidade_in:
            queryset = queryset.filter(
                criticidade__in=[c.strip() for c in criticidade_in.split(",") if c.strip()],
            )

        queryset = queryset.annotate(
            criticidade_ordem=Case(
                When(criticidade="critica", then=4),
                When(criticidade="alta", then=3),
                When(criticidade="media", then=2),
                When(criticidade="baixa", then=1),
                default=0,
                output_field=IntegerField(),
            ),
        ).order_by("-criticidade_ordem", "-created_at")

        return queryset

    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        """Marca violação como resolvida"""
        from django.utils import timezone

        violacao = self.get_object()
        violacao.status = "resolvida"
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get("notas", "")
        violacao.save()

        logger.info(f"✅ Violação {violacao.id} resolvida por {request.user.email}")

        return Response({
            "status": "resolvida",
            "resolvido_por": request.user.email,
            "resolvido_em": violacao.resolvido_em,
            "notas": violacao.notas,
        })

    @action(detail=True, methods=["post"])
    def investigar(self, request, pk=None):
        """Marca violação como em investigação"""
        violacao = self.get_object()
        if violacao.status in ("resolvida", "falso_positivo"):
            return Response(
                {"error": "Violação já encerrada"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        violacao.status = "investigando"
        violacao.save(update_fields=["status", "updated_at"])
        logger.info("Violação %s em investigação por %s", violacao.id, request.user.email)
        serializer = ViolacaoSegurancaSerializer(violacao)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def marcar_falso_positivo(self, request, pk=None):
        """Marca violação como falso positivo"""
        from django.utils import timezone

        violacao = self.get_object()
        violacao.status = "falso_positivo"
        violacao.resolvido_por = request.user
        violacao.resolvido_em = timezone.now()
        violacao.notas = request.data.get("notas", "")
        violacao.save()

        logger.info(f"ℹ️  Violação {violacao.id} marcada como falso positivo por {request.user.email}")

        return Response({
            "status": "falso_positivo",
            "resolvido_por": request.user.email,
            "resolvido_em": violacao.resolvido_em,
            "notas": violacao.notas,
        })

    def _stats_queryset(self):
        """Estatísticas globais (ignora filtros de lista, mantém só período opcional)."""
        from datetime import datetime, timedelta


        queryset = ViolacaoSeguranca.objects.all()
        params = self.request.query_params
        data_inicio = params.get("data_inicio")
        data_fim = params.get("data_fim")
        if data_inicio:
            with contextlib.suppress(ValueError):
                queryset = queryset.filter(created_at__gte=datetime.strptime(data_inicio, "%Y-%m-%d"))
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d") + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=data_fim_dt)
            except ValueError:
                pass
        return queryset

    @staticmethod
    def _counts_to_dict(rows, key_field):
        return {row[key_field]: row["count"] for row in rows}

    @action(detail=False, methods=["get"])
    def estatisticas(self, request):
        """Estatísticas de violações (formato dict para o dashboard de alertas)."""
        from datetime import timedelta

        from django.db.models import Count
        from django.utils import timezone

        queryset = self._stats_queryset()

        total = queryset.count()
        nao_resolvidas = queryset.filter(status__in=["nova", "investigando"]).count()

        por_status_rows = list(
            queryset.values("status").annotate(count=Count("id")).order_by("-count"),
        )
        por_criticidade_rows = list(
            queryset.values("criticidade").annotate(count=Count("id")).order_by("-count"),
        )
        por_tipo_rows = list(
            queryset.values("tipo").annotate(count=Count("id")).order_by("-count"),
        )

        cutoff_24h = timezone.now() - timedelta(hours=24)
        ultimas_24h = queryset.filter(created_at__gte=cutoff_24h).count()

        por_status = self._counts_to_dict(por_status_rows, "status")
        por_criticidade = self._counts_to_dict(por_criticidade_rows, "criticidade")
        por_tipo = self._counts_to_dict(por_tipo_rows, "tipo")

        return Response({
            "total": total,
            "nao_resolvidas": nao_resolvidas,
            "por_status": por_status,
            "por_criticidade": por_criticidade,
            "por_tipo": por_tipo,
            "por_status_list": por_status_rows,
            "por_criticidade_list": por_criticidade_rows,
            "por_tipo_list": por_tipo_rows,
            "ultimas_24h": ultimas_24h,
        })


class EstatisticasAuditoriaViewSet(viewsets.ViewSet):
    """ViewSet para estatísticas de auditoria"""

    permission_classes = [IsSuperAdmin]

    @action(detail=False, methods=["get"])
    @cached_stat(ttl=300, key_prefix="acoes_por_dia")
    def acoes_por_dia(self, request):
        """Gráfico de ações por dia"""
        from datetime import datetime, timedelta

        from django.db.models import Count, Q
        from django.db.models.functions import TruncDate
        from django.utils import timezone

        from ..models import HistoricoAcessoGlobal

        data_inicio_param = request.query_params.get("data_inicio")
        data_fim_param = request.query_params.get("data_fim")
        if data_inicio_param and data_fim_param:
            try:
                data_inicio = timezone.make_aware(datetime.strptime(data_inicio_param, "%Y-%m-%d"))
                data_fim = timezone.make_aware(datetime.strptime(data_fim_param + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
            except (ValueError, TypeError):
                dias = 30
                data_inicio = timezone.now() - timedelta(days=dias)
                data_fim = timezone.now()
        else:
            dias = int(request.query_params.get("dias", 30))
            data_inicio = timezone.now() - timedelta(days=dias)
            data_fim = timezone.now()

        from ..historico_auditoria_filters import queryset_auditoria_visivel
        qs = queryset_auditoria_visivel(
            HistoricoAcessoGlobal.objects.filter(
                created_at__gte=data_inicio,
                created_at__lte=data_fim,
            ),
        )
        acoes = qs.annotate(dia=TruncDate("created_at")).values("dia").annotate(
            total=Count("id"),
            sucessos=Count("id", filter=Q(sucesso=True)),
            erros=Count("id", filter=Q(sucesso=False)),
        ).order_by("dia")

        resultado = [
            {
                "periodo": item["dia"].strftime("%Y-%m-%d"),
                "total": item["total"],
                "sucessos": item["sucessos"],
                "erros": item["erros"],
            }
            for item in acoes
        ]
        return Response({"acoes": resultado})

    @action(detail=False, methods=["get"])
    @cached_stat(ttl=300, key_prefix="acoes_por_tipo")
    def acoes_por_tipo(self, request):
        """Distribuição de ações por tipo"""
        from django.db.models import Count

        from ..historico_auditoria_filters import queryset_auditoria_visivel
        from ..models import HistoricoAcessoGlobal

        acoes = queryset_auditoria_visivel(
            HistoricoAcessoGlobal.objects.all(),
        ).values("acao").annotate(
            total=Count("id"),
        ).order_by("-total")

        return Response({"acoes": list(acoes)})

    @action(detail=False, methods=["get"])
    @cached_stat(ttl=300, key_prefix="lojas_mais_ativas")
    def lojas_mais_ativas(self, request):
        """Ranking de lojas mais ativas"""
        from django.db.models import Count

        from ..historico_auditoria_filters import queryset_ranking_lojas
        from ..models import HistoricoAcessoGlobal

        limit = int(request.query_params.get("limit", 10))

        lojas = queryset_ranking_lojas(
            HistoricoAcessoGlobal.objects.all(),
        ).values("loja_id", "loja__nome").annotate(
            total=Count("id"),
        ).order_by("-total")[:limit]

        return Response({
            "lojas": [{"loja_nome": item["loja__nome"], "total": item["total"]} for item in lojas],
        })

    @action(detail=False, methods=["get"])
    @cached_stat(ttl=300, key_prefix="usuarios_mais_ativos")
    def usuarios_mais_ativos(self, request):
        """Ranking de usuários mais ativos"""
        from django.db.models import Count

        from ..historico_auditoria_filters import queryset_ranking_usuarios
        from ..models import HistoricoAcessoGlobal

        limit = int(request.query_params.get("limit", 10))

        usuarios = queryset_ranking_usuarios(
            HistoricoAcessoGlobal.objects.all(),
        ).values(
            "usuario_email", "usuario_nome",
        ).annotate(total=Count("id")).order_by("-total")[:limit]

        return Response({
            "usuarios": [{"usuario_nome": item["usuario_nome"], "total": item["total"]} for item in usuarios],
        })

    @action(detail=False, methods=["get"])
    @cached_stat(ttl=300, key_prefix="horarios_pico")
    def horarios_pico(self, request):
        """Distribuição de ações por hora do dia"""
        from django.db.models import Count
        from django.db.models.functions import ExtractHour

        from ..historico_auditoria_filters import queryset_auditoria_visivel
        from ..models import HistoricoAcessoGlobal

        acoes = queryset_auditoria_visivel(
            HistoricoAcessoGlobal.objects.all(),
        ).annotate(
            hora=ExtractHour("created_at"),
        ).values("hora").annotate(total=Count("id")).order_by("hora")

        return Response({
            "horarios": [{"hora": item["hora"], "total": item["total"]} for item in acoes],
        })

    @action(detail=False, methods=["get"])
    @cached_stat(ttl=300, key_prefix="taxa_sucesso")
    def taxa_sucesso(self, request):
        """Taxa de sucesso vs falha"""
        from ..historico_auditoria_filters import queryset_auditoria_visivel
        from ..models import HistoricoAcessoGlobal

        qs = queryset_auditoria_visivel(HistoricoAcessoGlobal.objects.all())
        total = qs.count()
        sucessos = qs.filter(sucesso=True).count()
        falhas = total - sucessos

        taxa_sucesso = (sucessos / total * 100) if total > 0 else 0

        return Response({
            "total": total,
            "sucessos": sucessos,
            "falhas": falhas,
            "erros": falhas,
            "taxa_sucesso": round(taxa_sucesso, 2),
        })
