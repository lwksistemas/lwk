from decimal import Decimal


def _escolher_local_consulta_comissao(consulta, regras: dict) -> tuple[int | None, str]:
    """Escolhe o local de atendimento para aplicar a regra de comissão da consulta."""
    if consulta.local_atendimento_id:
        nome = consulta.local_atendimento.nome if consulta.local_atendimento else ''
        return consulta.local_atendimento_id, nome

    locais_regra_ids = list(regras.get('consultas_local', {}).keys())
    if not locais_regra_ids:
        return None, ''

    from ..models import LocalAtendimento

    qs = LocalAtendimento.objects.filter(pk__in=locais_regra_ids, is_active=True).order_by('nome')
    consultorio = qs.filter(nome__icontains='consult').first()
    if consultorio:
        return consultorio.id, consultorio.nome

    local = qs.first()
    if local:
        return local.id, local.nome
    return None, ''


def _taxa_consulta_do_local(local_id: int | None) -> Decimal:
    if not local_id:
        return Decimal('0')
    from ..models import LocalAtendimento

    local = LocalAtendimento.objects.filter(pk=local_id, is_active=True).first()
    if not local:
        return Decimal('0')
    return Decimal(str(local.valor_consulta or 0))


def _resolver_valor_consulta_cadastro(
    consulta,
    amount: Decimal | None = None,
    procedimentos: list[dict] | None = None,
    regras: dict | None = None,
) -> Decimal:
    """
    Valor da taxa de consulta usado no relatório de comissões.

    Consultas criadas pela agenda costumam gravar valor_consulta=0 quando há
    procedimentos; usa o local de atendimento, o restante do pagamento ou a
    taxa do local quando o profissional tem comissão de consulta cadastrada.
    """
    vc = Decimal(str(getattr(consulta, 'valor_consulta', None) or 0))
    if vc > 0:
        return vc

    local = getattr(consulta, 'local_atendimento', None)
    if local is not None:
        local_vc = Decimal(str(getattr(local, 'valor_consulta', None) or 0))
        if local_vc > 0:
            return local_vc

    if amount is not None and amount > 0 and procedimentos:
        soma_proc = sum(Decimal(str(p.get('valor') or 0)) for p in procedimentos)
        restante = amount - soma_proc
        if restante > 0:
            return restante.quantize(Decimal('0.01'))

        if regras and regras.get('consultas_local') and soma_proc >= amount:
            local_id, _ = _escolher_local_consulta_comissao(consulta, regras)
            taxa = _taxa_consulta_do_local(local_id)
            if taxa > 0 and amount >= taxa:
                return taxa

    return Decimal('0')


def _resolver_local_atendimento_efetivo(
    consulta,
    regras: dict,
    taxa: Decimal,
) -> tuple[int | None, str]:
    """
    Local usado no relatório de comissões.

    Consultas da agenda costumam não gravar local_atendimento; tenta inferir
    pela taxa de consulta entre os locais com regra cadastrada do profissional.
    """
    if consulta.local_atendimento_id:
        nome = consulta.local_atendimento.nome if consulta.local_atendimento else ''
        return consulta.local_atendimento_id, nome

    locais_regra_ids = list(regras.get('consultas_local', {}).keys())
    if not locais_regra_ids:
        return None, ''

    from ..models import LocalAtendimento

    if taxa > 0:
        matches = [
            local for local in LocalAtendimento.objects.filter(pk__in=locais_regra_ids, is_active=True)
            if Decimal(str(local.valor_consulta or 0)) == taxa
        ]
        if len(matches) == 1:
            return matches[0].id, matches[0].nome

    return _escolher_local_consulta_comissao(consulta, regras)
