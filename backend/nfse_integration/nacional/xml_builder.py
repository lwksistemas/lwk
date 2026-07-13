"""
Construção do XML da DPS (Declaração de Prestação de Serviço) - NFS-e Nacional.
Baseado no XML real emitido pelo Portal Contribuinte (nfse.gov.br).
Namespace: http://www.sped.fazenda.gov.br/nfse
"""
import logging
import re
from datetime import datetime
from decimal import Decimal

from lxml import etree

from .constants import (
    NS_NFSE,
    VERSAO_DPS,
)

logger = logging.getLogger(__name__)


def _somente_digitos(texto: str) -> str:
    return re.sub(r'\D', '', texto or '')


def _formatar_decimal(valor: Decimal, casas: int = 2) -> str:
    return f'{valor:.{casas}f}'


def _el(parent, tag: str, text: str = None):
    """Cria subelemento com namespace e texto opcional."""
    el = etree.SubElement(parent, f'{{{NS_NFSE}}}{tag}')
    if text is not None:
        el.text = str(text)
    return el


def construir_xml_dps(
    # Identificação
    numero_dps: int,
    serie_dps: str,
    codigo_municipio_prestador: str,
    ambiente: str = 'producao',
    # Prestador
    prestador_cnpj: str = '',
    prestador_inscricao_municipal: str = '',
    prestador_razao_social: str = '',
    prestador_nome_fantasia: str = '',
    prestador_endereco: dict[str, str] | None = None,
    prestador_telefone: str = '',
    prestador_email: str = '',
    # Tomador
    tomador_cpf_cnpj: str = '',
    tomador_nome: str = '',
    tomador_endereco: dict[str, str] | None = None,
    tomador_telefone: str = '',
    tomador_email: str = '',
    # Serviço
    codigo_servico: str = '14.01',
    descricao_servico: str = '',
    codigo_cnae: str = '',
    codigo_municipio_incidencia: str = '',
    # Valores
    valor_servicos: Decimal = Decimal('0.00'),
    aliquota_iss: Decimal = Decimal('0.00'),
    valor_deducoes: Decimal = Decimal('0.00'),
    valor_desconto_incondicionado: Decimal = Decimal('0.00'),
    valor_desconto_condicionado: Decimal = Decimal('0.00'),
    # Tributação
    natureza_tributacao: int = 1,
    iss_retido: bool = False,
    optante_simples_nacional: bool = True,
    regime_especial: int = 0,
    incentivador_cultural: bool = False,
    # Código numérico
    codigo_numerico: int = 0,
    # Data
    data_competencia: datetime | None = None,
) -> str:
    """Constrói o XML da DPS conforme formato real do Portal Contribuinte."""
    if data_competencia is None:
        data_competencia = datetime.now()

    cnpj_digits = _somente_digitos(prestador_cnpj)
    tomador_doc = _somente_digitos(tomador_cpf_cnpj)
    valor = Decimal(str(valor_servicos))
    aliquota = Decimal(str(aliquota_iss))

    # Série formatada com 5 dígitos (zeros à esquerda)
    serie_formatada = _somente_digitos(serie_dps or '1').zfill(5)[:5]

    nsmap = {None: NS_NFSE}

    # Root: DPS com versao
    root = etree.Element(f'{{{NS_NFSE}}}DPS', nsmap=nsmap)
    root.set('versao', VERSAO_DPS)

    # infDPS com Id (formato TSIdDPS: DPS + CodMun7 + TipoInsc1 + InscFed14 + Serie5 + NumDPS15)
    tipo_insc = '2' if len(cnpj_digits) == 14 else '1'
    insc_fed = cnpj_digits.ljust(14, '0')[:14]
    num_dps_id = str(numero_dps).zfill(15)[:15]
    inf_id = f'DPS{codigo_municipio_prestador[:7].ljust(7, "0")}{tipo_insc}{insc_fed}{serie_formatada}{num_dps_id}'

    inf_dps = etree.SubElement(root, f'{{{NS_NFSE}}}infDPS', Id=inf_id)

    # --- Identificação (ordem conforme XML real) ---
    # Nota: em produção restrita (homologação), usar tpAmb=1 conforme comportamento do portal
    _el(inf_dps, 'tpAmb', '1')
    _el(inf_dps, 'dhEmi', data_competencia.strftime('%Y-%m-%dT00:00:00-03:00'))
    _el(inf_dps, 'verAplic', '1.00')
    _el(inf_dps, 'serie', serie_formatada)
    _el(inf_dps, 'nDPS', str(numero_dps))
    _el(inf_dps, 'dCompet', data_competencia.strftime('%Y-%m-%d'))
    _el(inf_dps, 'tpEmit', '1')  # 1=Prestador
    _el(inf_dps, 'cLocEmi', codigo_municipio_prestador)

    # === PRESTADOR (prest) - conforme XML real ===
    prest = _el(inf_dps, 'prest')
    _el(prest, 'CNPJ', cnpj_digits)
    if prestador_inscricao_municipal:
        _el(prest, 'IM', _somente_digitos(prestador_inscricao_municipal))
    if prestador_telefone:
        _el(prest, 'fone', _somente_digitos(prestador_telefone)[:11])
    if prestador_email:
        _el(prest, 'email', prestador_email[:80])
    # regTrib (regime tributário) - obrigatório conforme XML real
    reg_trib = _el(prest, 'regTrib')
    if optante_simples_nacional:
        _el(reg_trib, 'opSimpNac', '3')  # 3=Optante ME/EPP
        _el(reg_trib, 'regApTribSN', '1')  # 1=Regime de apuração
    else:
        _el(reg_trib, 'opSimpNac', '1')  # 1=Não optante
    _el(reg_trib, 'regEspTrib', str(regime_especial))

    # === TOMADOR (toma) - conforme XML real ===
    toma = _el(inf_dps, 'toma')
    if len(tomador_doc) == 11:
        _el(toma, 'CPF', tomador_doc)
    elif len(tomador_doc) == 14:
        _el(toma, 'CNPJ', tomador_doc)
    if tomador_nome:
        _el(toma, 'xNome', tomador_nome[:150])
    # Endereço do tomador
    if tomador_endereco:
        end_toma = _el(toma, 'end')
        end_nac = _el(end_toma, 'endNac')
        cep = _somente_digitos(tomador_endereco.get('cep', ''))[:8]
        cod_mun = tomador_endereco.get('codigo_municipio', '')
        if cod_mun:
            _el(end_nac, 'cMun', cod_mun[:7])
        if cep:
            _el(end_nac, 'CEP', cep.zfill(8))
        logradouro = (tomador_endereco.get('logradouro') or '').strip()
        if logradouro:
            _el(end_toma, 'xLgr', logradouro[:60])
        numero = (tomador_endereco.get('numero') or 'S/N').strip()
        _el(end_toma, 'nro', numero[:10])
        bairro = (tomador_endereco.get('bairro') or '').strip()
        if bairro:
            _el(end_toma, 'xBairro', bairro[:60])
    if tomador_telefone:
        _el(toma, 'fone', _somente_digitos(tomador_telefone)[:11])
    if tomador_email:
        _el(toma, 'email', tomador_email[:80])

    # === SERVIÇO (serv) ===
    serv = _el(inf_dps, 'serv')

    # locPrest
    loc_prest = _el(serv, 'locPrest')
    mun_incidencia = codigo_municipio_incidencia or codigo_municipio_prestador
    _el(loc_prest, 'cLocPrestacao', mun_incidencia)

    # cServ
    c_serv = _el(serv, 'cServ')
    codigo_trib_nac = _normalizar_codigo_servico_6dig(codigo_servico)
    _el(c_serv, 'cTribNac', codigo_trib_nac)
    _el(c_serv, 'xDescServ', (descricao_servico or 'Serviço prestado')[:2000])

    # === VALORES (valores) ===
    valores = _el(inf_dps, 'valores')

    # vServPrest
    v_serv_prest = _el(valores, 'vServPrest')
    _el(v_serv_prest, 'vServ', _formatar_decimal(valor))

    # trib
    trib = _el(valores, 'trib')

    # tribMun
    trib_mun = _el(trib, 'tribMun')
    _el(trib_mun, 'tribISSQN', str(natureza_tributacao))
    # tpRetISSQN: 1=Não Retido, 2=Retido pelo Tomador
    _el(trib_mun, 'tpRetISSQN', '2' if iss_retido else '1')
    # pAliq
    _el(trib_mun, 'pAliq', _formatar_decimal(aliquota))

    # totTrib - usar indTotTrib=0 (conforme XML real)
    tot_trib = _el(trib, 'totTrib')
    _el(tot_trib, 'indTotTrib', '0')

    # Gerar XML string
    xml_str = etree.tostring(root, encoding='unicode', xml_declaration=False)
    logger.info(
        'XML DPS construído: nDPS=%s, serie=%s, Id=%s, valor=R$%s',
        numero_dps, serie_formatada, inf_id, valor,
    )
    return xml_str


def _normalizar_codigo_servico_6dig(codigo: str) -> str:
    """
    Normaliza código de serviço para 6 dígitos (cTribNac).
    Ex: '14.01' -> '140101', '1401' -> '140100', '14.01.01' -> '140101'
    """
    raw = (codigo or '').strip()
    digits = _somente_digitos(raw)

    if len(digits) == 6:
        return digits
    if len(digits) == 4:
        return digits + '01'  # Desdobro padrão 01
    if len(digits) >= 6:
        return digits[:6]
    if len(digits) >= 4:
        return digits[:4] + '01'

    return '140101'  # Default: 14.01.01
