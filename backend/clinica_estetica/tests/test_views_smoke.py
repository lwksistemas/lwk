"""Smoke tests para views da clinica_estetica — verifica importação e configuração."""
import pytest


class TestImportsSmoke:
    """Verifica que todos os módulos importam sem erro."""

    def test_import_views_agenda(self):
        from clinica_estetica.views_agenda import (
            AgendamentoViewSet,
            BloqueioAgendaViewSet,
            ConsultaViewSet,
        )
        assert AgendamentoViewSet is not None
        assert BloqueioAgendaViewSet is not None
        assert ConsultaViewSet is not None

    def test_import_views_cadastros(self):
        from clinica_estetica.views_cadastros import (
            ClienteViewSet,
            ProfissionalViewSet,
            ProcedimentoViewSet,
        )
        assert ClienteViewSet is not None

    def test_import_views_financeiro(self):
        from clinica_estetica.views_financeiro import (
            CategoriaFinanceiraViewSet,
            TransacaoViewSet,
        )
        assert CategoriaFinanceiraViewSet is not None
        assert TransacaoViewSet is not None

    def test_import_views_config(self):
        from clinica_estetica.views_config import (
            HistoricoLoginViewSet,
            HistoricoAcessosLojaViewSet,
            LoginConfigView,
        )
        assert HistoricoLoginViewSet is not None
        assert LoginConfigView is not None

    def test_import_serializers_package(self):
        from clinica_estetica.serializers import (
            ClienteSerializer,
            AgendamentoSerializer,
            BloqueioAgendaSerializer,
            ConsultaSerializer,
            CategoriaFinanceiraSerializer,
            TransacaoSerializer,
            TransacaoResumoSerializer,
        )
        assert ClienteSerializer is not None
        assert AgendamentoSerializer is not None


class TestViewSetConfig:
    """Verifica configuração básica dos ViewSets."""

    def test_agendamento_queryset_has_select_related(self):
        from clinica_estetica.views_agenda import AgendamentoViewSet
        qs = AgendamentoViewSet.queryset
        # Verifica que select_related foi aplicado no queryset de classe
        assert qs.query.select_related is not False

    def test_transacao_queryset_has_select_related(self):
        from clinica_estetica.views_financeiro import TransacaoViewSet
        qs = TransacaoViewSet.queryset
        assert qs.query.select_related is not False

    def test_agendamento_has_throttle_on_dashboard(self):
        """Dashboard endpoint deve ter DashboardRateThrottle."""
        from clinica_estetica.views_agenda import AgendamentoViewSet
        # O action decorator armazena throttle_classes no método
        dashboard_method = getattr(AgendamentoViewSet, 'dashboard', None)
        assert dashboard_method is not None
        kwargs = getattr(dashboard_method, 'kwargs', {})
        throttle_classes = kwargs.get('throttle_classes', [])
        from core.throttling import DashboardRateThrottle
        assert DashboardRateThrottle in throttle_classes
