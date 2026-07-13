"""Service layer para Relatório de Comissões — Clínica da Beleza.

Re-exporta o pacote comissao_relatorio/ para compatibilidade com imports existentes.
"""
from .comissao_relatorio.alocacao import _alocar_valores_pagamento
from .comissao_relatorio.atendimento import calcular_comissao_payment_atendimento
from .comissao_relatorio.constants import CHAVE_CONSULTA, LABEL_CONSULTA
from .comissao_relatorio.formatting import (
    _combinar_formas_pagamento,
    _formatar_regra,
    _formatar_regra_brl,
    _label_forma_pagamento,
)
from .comissao_relatorio.local_consulta import (
    _escolher_local_consulta_comissao,
    _resolver_local_atendimento_efetivo,
    _resolver_valor_consulta_cadastro,
    _taxa_consulta_do_local,
)
from .comissao_relatorio.pagamentos import (
    _agrupar_pagamentos_por_agendamento,
    _obter_ou_criar_detalhe,
)
from .comissao_relatorio.procedimentos import _procedimentos_vinculados_consulta
from .comissao_relatorio.regras import (
    _calcular_comissao_regra,
    _regras_profissional,
    _resolver_regra_consulta,
    _resolver_regra_procedimento,
    _rotulo_convenio_comissao,
)
from .comissao_relatorio.relatorio import calcular_comissoes
from .convenio_service import resolver_convenio_atendimento_comissao

__all__ = [
    "CHAVE_CONSULTA",
    "LABEL_CONSULTA",
    "_agrupar_pagamentos_por_agendamento",
    "_alocar_valores_pagamento",
    "_calcular_comissao_regra",
    "_combinar_formas_pagamento",
    "_escolher_local_consulta_comissao",
    "_formatar_regra",
    "_formatar_regra_brl",
    "_label_forma_pagamento",
    "_obter_ou_criar_detalhe",
    "_procedimentos_vinculados_consulta",
    "_regras_profissional",
    "_resolver_local_atendimento_efetivo",
    "_resolver_regra_consulta",
    "_resolver_regra_procedimento",
    "_resolver_valor_consulta_cadastro",
    "_rotulo_convenio_comissao",
    "_taxa_consulta_do_local",
    "calcular_comissao_payment_atendimento",
    "calcular_comissoes",
    "resolver_convenio_atendimento_comissao",
]
