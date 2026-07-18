"""Pacote de envio de recibo de pagamento (email / WhatsApp)."""
from .context import (
    _extrair_desconto_notes,
    _formas_pagamento_html,
    _formas_pagamento_texto,
    _formatar_endereco_loja,
    _label_documento_loja,
    _linha_documento_loja,
    _listar_formas_pagamento,
    _obter_dados_contexto,
)
from .pdf import _gerar_pdf_recibo
from .service import enviar_recibo_pagamento
from .whatsapp_channel import _montar_mensagem_whatsapp

__all__ = [
    "enviar_recibo_pagamento",
    "_extrair_desconto_notes",
    "_formas_pagamento_html",
    "_formas_pagamento_texto",
    "_formatar_endereco_loja",
    "_gerar_pdf_recibo",
    "_label_documento_loja",
    "_linha_documento_loja",
    "_listar_formas_pagamento",
    "_montar_mensagem_whatsapp",
    "_obter_dados_contexto",
]
