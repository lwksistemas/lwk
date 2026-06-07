"""
superadmin/views — pacote refatorado (antes: views.py monolítico com 4029 linhas).

Módulos:
    permissions   — Classes de permissão (IsOwnerOrSuperAdmin, IsSuperAdmin)
    loja          — ViewSets de Loja, TipoLoja, PlanoAssinatura (público e admin)
    financeiro    — FinanceiroLojaViewSet, PagamentoLojaViewSet
    usuarios      — UsuarioSistemaViewSet, EmailRetryViewSet, MercadoPago, recuperar_senha_loja
    auditoria     — HistoricoAcessoGlobalViewSet, ViolacaoSegurancaViewSet, EstatisticasAuditoriaViewSet
    sistema       — Storage, health_check, LoginConfigSistema, atalho_redirect
"""

from .permissions import IsOwnerOrSuperAdmin, IsSuperAdmin
from .loja import (
    TipoLojaPublicoViewSet,
    PlanoAssinaturaPublicoViewSet,
    TipoLojaViewSet,
    PlanoAssinaturaViewSet,
    LojaViewSet,
)
from .financeiro import FinanceiroLojaViewSet, PagamentoLojaViewSet
from .usuarios import (
    UsuarioSistemaViewSet,
    EmailRetryViewSet,
    mercadopago_config,
    mercadopago_test,
    mercadopago_webhook,
    sync_mercadopago_loja,
    recuperar_senha_loja,
)
from .auditoria import (
    HistoricoAcessoGlobalViewSet,
    ViolacaoSegurancaViewSet,
    EstatisticasAuditoriaViewSet,
)
from .sistema import (
    verificar_storage_loja,
    verificar_storage_todas,
    listar_storage_lojas,
    health_check,
    LoginConfigSistemaViewSet,
    login_config_sistema_publico,
    atalho_redirect,
)

__all__ = [
    # Permissions
    'IsOwnerOrSuperAdmin',
    'IsSuperAdmin',
    # Loja
    'TipoLojaPublicoViewSet',
    'PlanoAssinaturaPublicoViewSet',
    'TipoLojaViewSet',
    'PlanoAssinaturaViewSet',
    'LojaViewSet',
    # Financeiro
    'FinanceiroLojaViewSet',
    'PagamentoLojaViewSet',
    # Usuarios
    'UsuarioSistemaViewSet',
    'EmailRetryViewSet',
    'mercadopago_config',
    'mercadopago_test',
    'mercadopago_webhook',
    'sync_mercadopago_loja',
    'recuperar_senha_loja',
    # Auditoria
    'HistoricoAcessoGlobalViewSet',
    'ViolacaoSegurancaViewSet',
    'EstatisticasAuditoriaViewSet',
    # Sistema
    'verificar_storage_loja',
    'verificar_storage_todas',
    'listar_storage_lojas',
    'health_check',
    'LoginConfigSistemaViewSet',
    'login_config_sistema_publico',
    'atalho_redirect',
]
