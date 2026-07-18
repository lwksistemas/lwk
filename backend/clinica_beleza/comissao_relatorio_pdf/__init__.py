"""Pacote PDF do relatório de comissões."""

from .blocos import (
    _bloco_consultas_pdf,
    _bloco_procedimentos_pdf,
    _bloco_resumo_profissional,
    _bloco_totais_final,
)
from .constants import _CINZA, _COR_PRIMARIA, _LARGURA_UTIL, LABEL_CONSULTA
from .formatting import (
    _codigo_pagamento_pdf,
    _fmt_brl,
    _fmt_data_br,
    _fmt_regra_comissao,
    _is_linha_consulta,
)
from .generator import gerar_pdf_comissoes
from .tables import _legenda_pagamento_pdf, _make_data_table, _titulo_secao
from ..pdf_common import logo_image as _logo_image
from ..pdf_common import merge_timbrado_fundo as _merge_timbrado_fundo

__all__ = [
    "LABEL_CONSULTA",
    "_CINZA",
    "_COR_PRIMARIA",
    "_LARGURA_UTIL",
    "_bloco_consultas_pdf",
    "_bloco_procedimentos_pdf",
    "_bloco_resumo_profissional",
    "_bloco_totais_final",
    "_codigo_pagamento_pdf",
    "_fmt_brl",
    "_fmt_data_br",
    "_fmt_regra_comissao",
    "_is_linha_consulta",
    "_legenda_pagamento_pdf",
    "_logo_image",
    "_make_data_table",
    "_merge_timbrado_fundo",
    "_titulo_secao",
    "gerar_pdf_comissoes",
]
