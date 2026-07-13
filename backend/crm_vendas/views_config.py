"""
Views de configuração, busca global, dashboard e utilitários do CRM.
Re-exporta módulos divididos para compatibilidade com urls.py e views.py.
"""
from .views_crm_busca import crm_busca  # noqa: F401
from .views_crm_config_api import (  # noqa: F401
    crm_config,
    crm_config_asaas_test,
    crm_config_issnet_test,
)
from .views_crm_me_dashboard import (  # noqa: F401
    _empty_dashboard_response,
    crm_me,
    dashboard_data,
)
from .views_crm_whatsapp_login import (  # noqa: F401
    LoginConfigView,
)
