"""superadmin/views — pacote refatorado (antes: views.py monolítico com 4029 linhas).

Módulos:
    permissions   — Classes de permissão (IsOwnerOrSuperAdmin, IsSuperAdmin)
    loja          — ViewSets de Loja, TipoLoja, PlanoAssinatura (público e admin)
    financeiro    — FinanceiroLojaViewSet, PagamentoLojaViewSet
    usuarios      — UsuarioSistemaViewSet, EmailRetryViewSet, MercadoPago, recuperar_senha_loja
    auditoria     — HistoricoAcessoGlobalViewSet, ViolacaoSegurancaViewSet, EstatisticasAuditoriaViewSet
    sistema       — Storage, health_check, LoginConfigSistema, atalho_redirect
"""

from .auditoria import (
    EstatisticasAuditoriaViewSet,
    HistoricoAcessoGlobalViewSet,
    ViolacaoSegurancaViewSet,
)
from .financeiro import FinanceiroLojaViewSet, PagamentoLojaViewSet
from .loja import (
    LojaViewSet,
    PlanoAssinaturaPublicoViewSet,
    PlanoAssinaturaViewSet,
    TipoLojaPublicoViewSet,
    TipoLojaViewSet,
)
from .permissions import IsOwnerOrSuperAdmin, IsSuperAdmin
from .sistema import (
    LoginConfigSistemaViewSet,
    atalho_redirect,
    health_check,
    listar_storage_lojas,
    login_config_sistema_publico,
    verificar_storage_loja,
    verificar_storage_todas,
)
from .usuarios import (
    EmailRetryViewSet,
    UsuarioSistemaViewSet,
    mercadopago_config,
    mercadopago_test,
    mercadopago_webhook,
    recuperar_senha_loja,
    sync_mercadopago_loja,
)

__all__ = [
    # Permissions
    "IsOwnerOrSuperAdmin",
    "IsSuperAdmin",
    # Loja
    "TipoLojaPublicoViewSet",
    "PlanoAssinaturaPublicoViewSet",
    "TipoLojaViewSet",
    "PlanoAssinaturaViewSet",
    "LojaViewSet",
    # Financeiro
    "FinanceiroLojaViewSet",
    "PagamentoLojaViewSet",
    # Usuarios
    "UsuarioSistemaViewSet",
    "EmailRetryViewSet",
    "mercadopago_config",
    "mercadopago_test",
    "mercadopago_webhook",
    "sync_mercadopago_loja",
    "recuperar_senha_loja",
    # Auditoria
    "HistoricoAcessoGlobalViewSet",
    "ViolacaoSegurancaViewSet",
    "EstatisticasAuditoriaViewSet",
    # Sistema
    "verificar_storage_loja",
    "verificar_storage_todas",
    "listar_storage_lojas",
    "health_check",
    "LoginConfigSistemaViewSet",
    "login_config_sistema_publico",
    "atalho_redirect",
]
