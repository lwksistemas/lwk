"""Configuração individual da simulação estética. A chave fica na clínica."""
from __future__ import annotations

from core.encryption import decrypt_value, encrypt_value, is_encrypted

from .models import SimulacaoEsteticaConfig


class SimulacaoEsteticaError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def normalizar_chave_youcam(chave: str) -> str:
    return (chave or "").strip()


def chave_youcam_valida(chave: str) -> bool:
    chave = normalizar_chave_youcam(chave)
    if len(chave) < 20 or len(chave) > 500:
        return False
    if any(caractere.isspace() for caractere in chave):
        return False
    if "..." in chave:
        return False
    return True


def _config_da_loja():
    return SimulacaoEsteticaConfig.objects.first()


def _chave_em_claro(config) -> str:
    if not config:
        return ""
    return decrypt_value(config.api_key or "")


def resposta_config(loja_id) -> dict:
    from superadmin.plano_features import loja_plano_permite_simulacao_estetica

    disponivel, mensagem = loja_plano_permite_simulacao_estetica(loja_id)
    config = _config_da_loja()
    return {
        "disponivel": disponivel,
        "mensagem": mensagem or "",
        "provedor": SimulacaoEsteticaConfig.PROVEDOR_YOUCAM,
        "ativa": bool(config and config.ativa and disponivel),
        "chave_configurada": bool(_chave_em_claro(config)),
    }


def salvar_config(loja_id, dados: dict) -> dict:
    from superadmin.plano_features import loja_plano_permite_simulacao_estetica

    disponivel, mensagem = loja_plano_permite_simulacao_estetica(loja_id)
    if not disponivel:
        raise SimulacaoEsteticaError(mensagem or "Plano sem simulação estética.", status=403)

    config = _config_da_loja()
    if config is None:
        config = SimulacaoEsteticaConfig(provedor=SimulacaoEsteticaConfig.PROVEDOR_YOUCAM)

    if dados.get("limpar_chave"):
        config.api_key = ""
        config.ativa = False
        config.save()
        return resposta_config(loja_id)

    if "api_key" in dados:
        bruto = normalizar_chave_youcam(dados.get("api_key") or "")
        if bruto:
            if not chave_youcam_valida(bruto):
                raise SimulacaoEsteticaError(
                    "Informe a chave completa da YouCam API desta clínica, sem espaços.",
                )
            config.api_key = encrypt_value(bruto)

    chave = _chave_em_claro(config)
    if "ativa" in dados:
        config.ativa = bool(dados.get("ativa"))
    if config.ativa and not chave:
        raise SimulacaoEsteticaError("Cole a chave da YouCam API antes de ativar a simulação.")
    if config.api_key and not is_encrypted(config.api_key):
        config.api_key = encrypt_value(chave)
    config.provedor = SimulacaoEsteticaConfig.PROVEDOR_YOUCAM
    config.save()
    return resposta_config(loja_id)
