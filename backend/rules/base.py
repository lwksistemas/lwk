"""
Motor principal de regras automáticas (ETAPA 5).
Executa ações por evento; todas as regras ficam no backend.
"""
from .agenda import regras_agenda
from .financeiro import regras_financeiro
from .notificacoes import regras_notificacao
from .profissionais import regras_profissionais


def _todas_regras():
    return (
        regras_agenda
        + regras_financeiro
        + regras_notificacao
        + regras_profissionais
    )


class MotorRegras:
    """
    Dispara as regras cadastradas para cada evento.
    Uso: motor.executar(evento="AGENDAMENTO_CRIADO", contexto={...})
    Se alguma regra levantar ValidationError, ela é propagada (view retorna 400).
    """

    def __init__(self):
        self._regras = _todas_regras()

    def executar(self, evento, contexto):
        for regra in self._regras:
            if regra.get("evento") == evento and regra.get("ativa", True):
                acao = regra.get("acao")
                if callable(acao):
                    acao(contexto)
