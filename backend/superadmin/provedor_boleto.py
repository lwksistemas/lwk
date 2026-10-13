"""Provedor de boleto das lojas novas.

O padrão marcado em Recebimento das assinaturas vale para o cadastro público.
O superadmin pode escolher outro provedor ao criar a loja pelo painel.
"""


def provedor_boleto_padrao() -> str:
    """Cora ou Mercado Pago quando estão marcados e ligados. Senão, Asaas."""
    from .models import CoraConfig, MercadoPagoConfig

    cora = CoraConfig.get_config()
    if cora.use_for_boletos and cora.enabled:
        return "cora"
    mercado_pago = MercadoPagoConfig.get_config()
    if mercado_pago.use_for_boletos and mercado_pago.enabled:
        return "mercadopago"
    return "asaas"


def provedor_no_cadastro(usuario, informado: str | None) -> str:
    """Cadastro público segue o padrão. Superadmin usa o valor enviado."""
    if getattr(usuario, "is_superuser", False):
        escolhido = (informado or "").strip()
        return escolhido or "asaas"
    return provedor_boleto_padrao()
