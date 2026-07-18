"""Compat: re-exporta o pacote clinica_beleza.recibo.

Imports existentes (`from .recibo_service import ...`) continuam funcionando.
"""
from .recibo import (  # noqa: F401
    _extrair_desconto_notes,
    _formas_pagamento_html,
    _formas_pagamento_texto,
    _formatar_endereco_loja,
    _gerar_pdf_recibo,
    _label_documento_loja,
    _linha_documento_loja,
    _listar_formas_pagamento,
    _montar_mensagem_whatsapp,
    _obter_dados_contexto,
    enviar_recibo_pagamento,
)
from .recibo.context import (  # noqa: F401
    _formatar_cep,
    _formatar_data_recibo,
    _linha_tel_cep,
)
from .recibo.email_channel import (  # noqa: F401
    _enviar_recibo_email,
    _montar_email_html,
    _montar_email_texto,
)
from .recibo.whatsapp_channel import _enviar_recibo_whatsapp  # noqa: F401

__all__ = [
    "enviar_recibo_pagamento",
    "_enviar_recibo_email",
    "_enviar_recibo_whatsapp",
    "_extrair_desconto_notes",
    "_formas_pagamento_html",
    "_formas_pagamento_texto",
    "_formatar_cep",
    "_formatar_data_recibo",
    "_formatar_endereco_loja",
    "_gerar_pdf_recibo",
    "_label_documento_loja",
    "_linha_documento_loja",
    "_linha_tel_cep",
    "_listar_formas_pagamento",
    "_montar_email_html",
    "_montar_email_texto",
    "_montar_mensagem_whatsapp",
    "_obter_dados_contexto",
]
