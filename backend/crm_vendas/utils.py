"""Utilitários do CRM Vendas.
"""
import logging
import re

from tenants.middleware import ensure_loja_context, get_current_loja_id

logger = logging.getLogger(__name__)


def _digits_cpf_cnpj(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def gerar_titulo_proposta(lead) -> str:
    """Título padrão da proposta: nome (CPF) ou razão social (CNPJ) do cliente.
    Espelha frontend/lib/crm-utils.ts gerarTituloProposta.
    """
    conta = getattr(lead, "conta", None)
    cpf_cnpj = ""
    if conta and getattr(conta, "cnpj", None):
        cpf_cnpj = conta.cnpj
    elif getattr(lead, "cpf_cnpj", None):
        cpf_cnpj = lead.cpf_cnpj

    is_cnpj = len(_digits_cpf_cnpj(cpf_cnpj)) > 11
    if is_cnpj:
        for candidate in (
            getattr(conta, "razao_social", None) if conta else None,
            getattr(conta, "nome", None) if conta else None,
            getattr(lead, "empresa", None),
            getattr(lead, "nome", None),
        ):
            text = (candidate or "").strip()
            if text:
                return text
        return ""

    for candidate in (
        getattr(conta, "nome", None) if conta else None,
        getattr(lead, "nome", None),
    ):
        text = (candidate or "").strip()
        if text:
            return text
    return ""


def titulo_proposta_corrigido(titulo_atual: str, lead, prestadora_nomes=None) -> str | None:
    """Retorna o novo título se a proposta deve ser atualizada; None se já estiver ok.
    Remove prefixo da prestadora (ex.: "ULTRASIS INFORMATICA LTDA - Cliente").
    """
    atual = (titulo_atual or "").strip()
    novo = gerar_titulo_proposta(lead)
    if not novo:
        return None
    if atual == novo:
        return None

    prefixes = []
    for name in prestadora_nomes or []:
        text = (name or "").strip()
        if text and text not in prefixes:
            prefixes.append(text)

    for prefix in prefixes:
        for sep in (" - ", " — ", " – "):
            marker = f"{prefix}{sep}"
            if atual.startswith(marker):
                candidato = atual[len(marker):].strip()
                if candidato and candidato != atual:
                    return candidato

    for sep in (" - ", " — ", " – "):
        if sep in atual:
            suffix = atual.split(sep, 1)[1].strip()
            if suffix and suffix.lower() == novo.lower():
                return suffix

    if any(sep in atual for sep in (" - ", " — ", " – ")):
        return novo

    return None


def get_loja_from_context(request=None):
    """Obtém a loja do contexto atual (thread-local) ou, se necessário, via headers.

    Ordem alinhada ao TenantMiddleware / ensure_loja_context:
    1. ``get_current_loja_id()`` (já preenchido pelo middleware na maioria dos casos)
    2. Se houver ``request`` e ainda não houver loja: ``ensure_loja_context(request)``
       (slug antes de X-Loja-ID, e configuração do banco do tenant)

    Args:
        request: Request object (opcional)

    Returns:
        Loja object ou None se não encontrar

    """
    from superadmin.models import Loja

    loja_id = get_current_loja_id()
    if not loja_id and request:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()

    if not loja_id:
        logger.warning("get_loja_from_context: contexto de loja não encontrado")
        return None

    try:
        return Loja.objects.using("default").get(id=loja_id)
    except Loja.DoesNotExist:
        logger.warning("get_loja_from_context: loja_id=%s não existe", loja_id)
        return None


def get_current_vendedor_id(request):
    """Retorna o ID do vendedor logado.
    - Se for vendedor (VendedorUsuario): retorna vendedor_id
    - Se for proprietário da loja COM vendedor vinculado: retorna vendedor_id
    - Se for proprietário da loja SEM vendedor vinculado: retorna None (vê todos os dados)

    IMPORTANTE: Owner COM vendedor vinculado pode fazer vendas.
    Owner SEM vendedor vinculado tem acesso total (apenas gerencia).
    """
    if not request or not request.user or not request.user.is_authenticated:
        logger.debug("get_current_vendedor_id: usuário não autenticado")
        return None
    loja_id = get_current_loja_id()
    if not loja_id and request:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()
    if not loja_id:
        logger.warning(
            "get_current_vendedor_id: loja_id ausente no contexto (user_id=%s). "
            "Vendedor não será atribuído em criações.",
            getattr(request.user, "id", None),
        )
        return None
    try:
        from superadmin.models import Loja, VendedorUsuario

        # Verificar se tem VendedorUsuario (funciona para owner E vendedores)
        vu = VendedorUsuario.objects.using("default").filter(
            user=request.user,
            loja_id=loja_id,
        ).first()

        if vu:
            # Tem vendedor vinculado (pode ser owner ou vendedor)
            return vu.vendedor_id

        # Verificar se é proprietário SEM vendedor vinculado
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            # Owner SEM vendedor: retorna None para ver TODOS os dados
            return None

        logger.debug(
            "get_current_vendedor_id: VendedorUsuario não encontrado para user_id=%s, loja_id=%s",
            request.user.id, loja_id,
        )
    except Exception as e:
        logger.warning("get_current_vendedor_id: erro ao buscar vendedor: %s", e)
    return None


def is_owner(request):
    """Verifica se o usuário é o proprietário da loja.
    Owner SEMPRE tem acesso total, mesmo se tiver VendedorUsuario vinculado.

    Returns:
        bool: True se for owner, False caso contrário

    """
    if not request or not request.user or not request.user.is_authenticated:
        return False
    loja_id = get_current_loja_id()
    if not loja_id:
        ensure_loja_context(request)
        loja_id = get_current_loja_id()
    if not loja_id:
        return False
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        return loja and loja.owner_id == request.user.id
    except Exception:
        return False


def get_vendedor_padrao_admin_loja(request):
    """ID do Vendedor a usar quando o dono da loja cria oportunidade sem informar vendedor.

    - Se já existir VendedorUsuario, get_current_vendedor_id resolve (retorno direto).
    - Se o dono NÃO tiver vínculo VendedorUsuario, get_current_vendedor_id retorna None e
      as vendas ficavam sem vendedor; neste caso usamos o registro Vendedor da loja com
      is_admin=True (administrador), ou o vendedor cujo e-mail coincide com o do owner.

    Assim relatórios e dashboard atribuem as vendas ao administrador (ex.: LUIZ HENRIQUE FELIX).
    """
    vid = get_current_vendedor_id(request)
    if vid:
        return vid
    if not request or not getattr(request.user, "is_authenticated", False):
        return None
    if not is_owner(request):
        return None
    loja_id = get_current_loja_id()
    if not loja_id:
        return None
    try:
        from .models import Vendedor

        v = (
            Vendedor.objects.filter(loja_id=loja_id, is_active=True, is_admin=True)
            .order_by("id")
            .first()
        )
        if v:
            return v.id
        email = (getattr(request.user, "email", None) or "").strip().lower()
        if email:
            v = Vendedor.objects.filter(loja_id=loja_id, is_active=True, email__iexact=email).first()
            if v:
                return v.id
    except Exception as e:
        logger.warning("get_vendedor_padrao_admin_loja: %s", e)
    return None


def get_vendedor_destino_merge_loja(loja_id: int):
    """Vendedor ativo que deve receber, nos relatórios e no dashboard, a soma das vendas
    sem vendedor ou com vendedor inativo.

    Ordem: ``is_admin=True`` → vendedor com o mesmo e-mail do dono da loja → primeiro ativo por id.
    Assim o dono (ex.: Luiz) continua sendo o destino mesmo sem a flag ``is_admin`` no cadastro.
    """
    if not loja_id:
        return None
    try:
        from superadmin.models import Loja

        from .models import Vendedor

        qs = Vendedor.objects.filter(loja_id=loja_id, is_active=True).order_by("id")
        v = qs.filter(is_admin=True).first()
        if v:
            return v
        loja = Loja.objects.using("default").select_related("owner").filter(id=loja_id).first()
        if loja and loja.owner:
            email = (loja.owner.email or "").strip().lower()
            if email:
                v = qs.filter(email__iexact=email).first()
                if v:
                    return v
        return qs.first()
    except Exception as e:
        logger.warning("get_vendedor_destino_merge_loja: %s", e)
        return None


def is_vendedor_usuario(request):
    """Verifica se o usuário logado é um vendedor (VendedorUsuario), não o owner.
    Retorna True apenas se for um vendedor real, False para owner ou outros.

    IMPORTANTE: Owner SEMPRE retorna False, mesmo se tiver VendedorUsuario vinculado.
    """
    if not request or not request.user or not request.user.is_authenticated:
        return False

    # Owner NUNCA é vendedor
    if is_owner(request):
        return False

    # Verificar se tem vendedor_id (já faz a verificação de VendedorUsuario)
    return get_current_vendedor_id(request) is not None
