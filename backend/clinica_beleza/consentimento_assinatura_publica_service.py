"""Helpers compartilhados das views públicas de assinatura de consentimento."""
from __future__ import annotations

from .consentimento_service import garantir_termos_procedimento, montar_conteudo_termo_procedimento
from .models import ConsultaTermoProcedimento

STATUS_DISPLAY = {
    "aguardando_profissional": "Aguardando Profissional",
    "concluido": "Concluído",
}


def configurar_tenant_publico_clinica(loja_id: int) -> str | None:
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    loja = Loja.objects.using("default").filter(id=loja_id, is_active=True).first()
    if not loja:
        return "Loja não encontrada."
    db_name = loja.database_name
    if not ensure_loja_database_config(db_name):
        return "Banco da loja indisponível."
    set_current_tenant_db(db_name)
    set_current_loja_id(loja_id)
    return None


def resolver_termo_procedimento(consulta, procedure_id) -> ConsultaTermoProcedimento | None:
    termos = garantir_termos_procedimento(consulta)
    for t in termos:
        if t.procedure_id == int(procedure_id):
            return t
    return None


def preencher_termo_se_vazio(termo_proc: ConsultaTermoProcedimento) -> None:
    if not (termo_proc.conteudo_termo or "").strip():
        termo_proc.conteudo_termo = montar_conteudo_termo_procedimento(
            termo_proc.consulta, termo_proc.procedure,
        )
        termo_proc.save(update_fields=["conteudo_termo", "updated_at"])


def documento_da_assinatura(adapter, assinatura):
    try:
        return adapter.get_documento_da_assinatura(assinatura)
    except ValueError:
        return None
