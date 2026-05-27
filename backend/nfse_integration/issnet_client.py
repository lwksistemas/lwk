"""
Cliente para webservice ISSNet de Ribeirão Preto
Emissão de NFS-e direta na prefeitura — padrão ABRASF 2.04

Referências:
- WSDL: https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx?wsdl
- Operações: RecepcionarLoteRps (EnviarLoteRpsEnvio) + ConsultarLoteRps se vier só Protocolo;
  fallback RecepcionarLoteRpsSincrono (mesmo XML) se Fault genérico no assíncrono.
- WSDL: nfseCabecMsg e nfseDadosMsg sao ``xsd:string``. O ASMX costuma desserializar corretamente quando o
  XML ABRASF vai como *texto* (entidades ``&lt;...&gt;``), CDATA, ou filhos — tentamos nessa ordem em Fault generico.
- Envelope ``nfse:Operacao`` (namespace http://nfse.abrasf.org.br) + mTLS.
"""
import logging
import os
import re
import time
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape
from typing import Any, Dict, Optional
from decimal import Decimal

from lxml import etree

from nfse_integration.issnet_constants import (
    CABEC_MSG,
    COD_MUNICIPIO_RP,
    ISSNET_RP_NFSE_ASMX,
    ISSNET_RP_NFSE_HOMOLOG,
    ISSNET_URLS,
    NS_NFSE,
    NS_NFSE_WSDL,
    SOAP_ACTION_CONSULTAR_LOTE_RPS,
    SOAP_ACTION_RECEPCIONAR_LOTE_RPS,
    SOAP_ACTION_RECEPCIONAR_LOTE_RPS_SINCRONO,
)
from nfse_integration.issnet_response import (
    extrair_body_soap,
    extrair_erros,
    interpretar_cancelamento,
    parse_resposta_cancelamento,
    parse_resposta_xml,
)
from nfse_integration.issnet_cert import carregar_certificado
from nfse_integration.issnet_soap_transport import criar_soap_client, post_soap_operacao
from nfse_integration.issnet_xml_signer import assinar_xml_issnet

logger = logging.getLogger(__name__)

_carregar_certificado = carregar_certificado


def _xml_envio_para_raiz_sincrono_sem_assinar(xml_envio: str) -> str:
    """
    RecepcionarLoteRpsSincrono exige a raiz ``EnviarLoteRpsSincronoEnvio``; o mesmo ``LoteRps`` do envio
    assincrono, com segunda assinatura na raiz (ver ``_assinar_xml``).
    """
    s = (xml_envio or '').strip()
    if 'EnviarLoteRpsSincronoEnvio' in s:
        return s
    s = s.replace(
        f'<EnviarLoteRpsEnvio xmlns="{NS_NFSE}">',
        f'<EnviarLoteRpsSincronoEnvio xmlns="{NS_NFSE}">',
        1,
    )
    s = s.replace('</EnviarLoteRpsEnvio>', '</EnviarLoteRpsSincronoEnvio>', 1)
    return s


def _issnet_erro_parece_negocio_abrasf(erro: str) -> bool:
    """Retorno com ``ListaMensagemRetorno`` (codigo entre colchetes) ou resposta sem NF — nao reenviar lote."""
    err = (erro or '').strip()
    if re.search(r'\[[A-Za-z]?\d+\]', err):
        return True
    if 'NFS-e nao encontrada na resposta' in err:
        return True
    return False


def _somente_digitos(texto: str) -> str:
    return re.sub(r'\D', '', texto or '')


def _normalizar_item_lista_servico_abrasf(codigo: Optional[str]) -> str:
    """
    ItemListaServico (LC 116 / ABRASF tsItemListaServico): enumeracao ``NN.MM``.
    Cadastros costumam usar ``170602`` ou ``1401`` sem ponto — invalido no XSD.
    """
    raw = (codigo or '').strip()
    if re.fullmatch(r'\d{2}\.\d{2}', raw):
        return raw
    digits = _somente_digitos(raw)
    if len(digits) >= 4:
        return f'{digits[0:2]}.{digits[2:4]}'
    return '14.01'


def _codigo_tributacao_municipio_xml(
    raw_codigo: Optional[str], _item_lista_abrasf: str
) -> str:
    """
    CodigoTributacaoMunicipio (tsCodigoTributacao): string 1..20.
    Prefeituras costumam exigir o codigo municipal completo (ex.: 170602), distinto
    do ItemListaServico em formato LC (17.06).
    """
    raw = (raw_codigo or '').strip()
    digits = _somente_digitos(raw)
    if len(digits) >= 5:
        return digits[:20]
    if len(digits) == 4:
        return digits
    if re.fullmatch(r'\d{2}\.\d{2}', raw):
        return digits[:20] if digits else raw.replace('.', '')
    fb = _somente_digitos(_item_lista_abrasf)
    return (fb[:20] if fb else '1401')


def testar_conexao_issnet(
    usuario: str,
    senha: str,
    certificado_path: str,
    senha_certificado: str,
    ambiente: str = 'producao',
) -> Dict[str, Any]:
    """Teste nao destrutivo: valida PFX/senha e tenta acessar o WSDL."""
    import requests as req

    out: Dict[str, Any] = {
        'success': False, 'message': '', 'detail': '',
        'ambiente': 'homologacao' if ambiente == 'homologacao' else 'producao',
    }
    if not (usuario or '').strip() or not (senha or '').strip():
        out['detail'] = 'Informe usuario e senha ISSNet.'
        return out
    path = (certificado_path or '').strip()
    if not path or not os.path.isfile(path):
        out['detail'] = 'Certificado .pfx nao encontrado no servidor.'
        return out
    if not (senha_certificado or ''):
        out['detail'] = 'Informe a senha do certificado (.pfx).'
        return out

    amb = 'homologacao' if ambiente == 'homologacao' else 'producao'
    base = ISSNET_URLS.get(amb)
    if not base:
        out['detail'] = f'Ambiente ISSNet desconhecido: {ambiente}'
        return out

    try:
        _key, cert, _ = _carregar_certificado(path, senha_certificado)
        try:
            out['certificado_subject'] = cert.subject.rfc4514_string()[:500]
        except Exception:
            pass
    except Exception as e:
        logger.warning('testar_conexao_issnet: falha PFX: %s', e)
        out['detail'] = 'Nao foi possivel abrir o certificado. Verifique .pfx e senha.'
        return out

    try:
        r = req.get(f'{base}?wsdl', timeout=25, headers={'User-Agent': 'LWK-Sistemas/CRM'})
        body = (r.text or '')[:2000].lower()
        if r.status_code == 200 and ('definitions' in body or 'wsdl' in body):
            out['success'] = True
            out['message'] = (
                'Certificado OK e WSDL ISSNet Online (ABRASF 2.04) acessivel. '
                'Credenciais serao validadas na primeira emissao.'
            )
            if amb == 'homologacao':
                out['message'] += (
                    ' Em Ribeirao Preto este WSDL e o mesmo da producao; homologacao de negocio depende '
                    'da prefeitura (liberacao / credenciais de teste), nao de outro hostname.'
                )
        else:
            out['detail'] = f'WSDL retornou HTTP {r.status_code}.'
    except Exception as e:
        logger.warning('testar_conexao_issnet: request WSDL: %s', e)
        out['detail'] = f'Nao foi possivel contatar o ISSNet: {e}'
    return out


class ISSNetClient:
    """
    Cliente SOAP para webservice ISSNet Ribeirao Preto (ABRASF 2.04).

    Emissão: RecepcionarLoteRps + EnviarLoteRpsEnvio (ABRASF 2.04), SOAP + mTLS como sped-nfse-issnet (Focus599Dev).
    Credenciais ISSNet (usuario/senha) são exigidas na configuração; o envelope segue NFePHP envelopSOAP.
    """

    def __init__(
        self,
        usuario: str,
        senha: str,
        certificado_path: str,
        senha_certificado: str,
        ambiente: str = 'producao',
    ):
        self.usuario = usuario
        self.senha = senha
        self.certificado_path = certificado_path
        self.senha_certificado = senha_certificado
        self.ambiente = 'homologacao' if ambiente == 'homologacao' else 'producao'
        self.base_url = ISSNET_URLS[self.ambiente]
        self.wsdl_url = f'{self.base_url}?wsdl'
        self._soap_client = None
        if self.ambiente == 'homologacao':
            logger.warning(
                'ISSNet RP ABRASF 2.04: ambiente homologacao — mesmo WSDL de producao (%s). '
                'Liberacao municipal (ex. E138) e cadastro continuam valendo; confirme com a prefeitura '
                'se existe ambiente de testes separado.',
                self.base_url,
            )

        # Campos configuraveis (setados pelo service.py)
        self._regime_especial = '0'
        self._optante_simples = True
        self._incentivador_cultural = False

    def _get_soap_client(self):
        """Cliente SOAP zeep com lazy loading."""
        if self._soap_client is not None:
            return self._soap_client
        self._soap_client = criar_soap_client(self.wsdl_url, self.base_url)
        logger.info('Cliente SOAP ISSNet inicializado: %s', self.ambiente)
        return self._soap_client

    def _assinar_xml(self, xml_str: str) -> str:
        return assinar_xml_issnet(xml_str, self.certificado_path, self.senha_certificado)

    # Metodo antigo mantido como referencia
    # ------------------------------------------------------------------
    # Construir XML ABRASF 2.04 — EnviarLoteRpsEnvio (ISSNet RP, op. RecepcionarLoteRps)
    # ------------------------------------------------------------------
    def _construir_xml_gerar_nfse(
        self,
        prestador_cnpj: str,
        prestador_inscricao_municipal: str,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_endereco: Dict[str, str],
        servico_codigo: str,
        servico_descricao: str,
        valor_servicos: Decimal,
        aliquota_iss: Decimal,
        numero_rps: int,
        serie_rps: str,
        tipo_rps: int,
        data_emissao: datetime,
        codigo_cnae: Optional[str] = None,
    ) -> str:
        """
        Constroi XML EnviarLoteRpsEnvio no padrao ABRASF 2.04 (ISSNet Ribeirao Preto / sped-nfse-issnet).
        """
        cnpj_prest = _somente_digitos(prestador_cnpj)
        doc_tomador = _somente_digitos(tomador_cpf_cnpj)

        valor = Decimal(str(valor_servicos))
        aliquota = Decimal(str(aliquota_iss))
        valor_iss = (valor * aliquota / 100).quantize(Decimal('0.01'))

        ns = NS_NFSE
        # Root: EnviarLoteRpsEnvio (fluxo oficial PHP ISSNET para RP)
        root = etree.Element('{%s}EnviarLoteRpsEnvio' % ns, nsmap={None: ns})

        # LoteRps: somente versao="2.04" (2a assinatura e enveloped na raiz, sem Id — ver XSD)
        lote = etree.SubElement(root, '{%s}LoteRps' % ns, versao='2.04')
        nlote_cfg = int(getattr(self, '_numero_lote_config', 0) or 0)
        numero_lote = nlote_cfg if nlote_cfg > 0 else int(numero_rps)
        etree.SubElement(lote, '{%s}NumeroLote' % ns).text = str(numero_lote)

        # Prestador no LoteRps
        prest_lote = etree.SubElement(lote, '{%s}Prestador' % ns)
        cpf_cnpj_pl = etree.SubElement(prest_lote, '{%s}CpfCnpj' % ns)
        etree.SubElement(cpf_cnpj_pl, '{%s}Cnpj' % ns).text = cnpj_prest
        etree.SubElement(prest_lote, '{%s}InscricaoMunicipal' % ns).text = (
            prestador_inscricao_municipal
        )

        etree.SubElement(lote, '{%s}QuantidadeRps' % ns).text = '1'

        # ListaRps > Rps > InfDeclaracaoPrestacaoServico
        lista = etree.SubElement(lote, '{%s}ListaRps' % ns)
        rps_el = etree.SubElement(lista, '{%s}Rps' % ns)
        inf = etree.SubElement(
            rps_el, '{%s}InfDeclaracaoPrestacaoServico' % ns,
            Id=f'rps{numero_rps}'
        )

        # --- Rps (identificacao) ---
        rps_inner = etree.SubElement(inf, '{%s}Rps' % ns)
        id_rps = etree.SubElement(rps_inner, '{%s}IdentificacaoRps' % ns)
        etree.SubElement(id_rps, '{%s}Numero' % ns).text = str(numero_rps)
        etree.SubElement(id_rps, '{%s}Serie' % ns).text = serie_rps
        etree.SubElement(id_rps, '{%s}Tipo' % ns).text = str(tipo_rps)
        # ABRASF tcInfRps: DataEmissao e xsd:date (AAAA-MM-DD), nao dateTime.
        etree.SubElement(rps_inner, '{%s}DataEmissao' % ns).text = data_emissao.strftime('%Y-%m-%d')
        etree.SubElement(rps_inner, '{%s}Status' % ns).text = '1'

        # --- Competencia ---
        etree.SubElement(inf, '{%s}Competencia' % ns).text = (
            data_emissao.strftime('%Y-%m-%d')
        )

        # --- Servico ---
        servico = etree.SubElement(inf, '{%s}Servico' % ns)

        # Valores: sequencia alinhada ao manual ISSNet/ABRASF 2.04 (retencoes federais antes de ValorIss).
        valores = etree.SubElement(servico, '{%s}Valores' % ns)
        etree.SubElement(valores, '{%s}ValorServicos' % ns).text = f'{valor:.2f}'
        etree.SubElement(valores, '{%s}ValorDeducoes' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}ValorPis' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}ValorCofins' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}ValorInss' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}ValorIr' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}ValorCsll' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}OutrasRetencoes' % ns).text = '0.00'
        # ValTotTributos: sequencia alinhada ao sped-nfse-issnet Make::buildValores (antes de ValorIss).
        etree.SubElement(valores, '{%s}ValTotTributos' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}ValorIss' % ns).text = f'{valor_iss:.2f}'
        etree.SubElement(valores, '{%s}Aliquota' % ns).text = f'{aliquota:.2f}'
        etree.SubElement(valores, '{%s}DescontoIncondicionado' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}DescontoCondicionado' % ns).text = '0.00'

        etree.SubElement(servico, '{%s}IssRetido' % ns).text = '2'
        item_lista = _normalizar_item_lista_servico_abrasf(servico_codigo)
        cod_tributacao = _codigo_tributacao_municipio_xml(servico_codigo, item_lista)
        if (servico_codigo or '').strip() and (
            (servico_codigo or '').strip() != item_lista
            or _somente_digitos(servico_codigo or '') != cod_tributacao
        ):
            logger.info(
                'ISSNet codigo servico: config %r -> ItemListaServico %r, '
                'CodigoTributacaoMunicipio %r',
                servico_codigo,
                item_lista,
                cod_tributacao,
            )
        etree.SubElement(servico, '{%s}ItemListaServico' % ns).text = item_lista
        cnae_digits = _somente_digitos(codigo_cnae or '')
        if cnae_digits:
            etree.SubElement(servico, '{%s}CodigoCnae' % ns).text = cnae_digits
        etree.SubElement(servico, '{%s}CodigoTributacaoMunicipio' % ns).text = cod_tributacao
        etree.SubElement(servico, '{%s}Discriminacao' % ns).text = servico_descricao
        etree.SubElement(servico, '{%s}CodigoMunicipio' % ns).text = COD_MUNICIPIO_RP
        etree.SubElement(servico, '{%s}ExigibilidadeISS' % ns).text = '1'
        etree.SubElement(servico, '{%s}MunicipioIncidencia' % ns).text = COD_MUNICIPIO_RP

        # --- Prestador ---
        prestador = etree.SubElement(inf, '{%s}Prestador' % ns)
        cpf_cnpj_prest = etree.SubElement(prestador, '{%s}CpfCnpj' % ns)
        etree.SubElement(cpf_cnpj_prest, '{%s}Cnpj' % ns).text = cnpj_prest
        etree.SubElement(prestador, '{%s}InscricaoMunicipal' % ns).text = (
            prestador_inscricao_municipal
        )

        # --- TomadorServico (nao Tomador!) ---
        tomador = etree.SubElement(inf, '{%s}TomadorServico' % ns)
        id_tom = etree.SubElement(tomador, '{%s}IdentificacaoTomador' % ns)
        cpf_cnpj_tom = etree.SubElement(id_tom, '{%s}CpfCnpj' % ns)
        if len(doc_tomador) == 11:
            etree.SubElement(cpf_cnpj_tom, '{%s}Cpf' % ns).text = doc_tomador
        else:
            etree.SubElement(cpf_cnpj_tom, '{%s}Cnpj' % ns).text = doc_tomador
        etree.SubElement(tomador, '{%s}RazaoSocial' % ns).text = tomador_nome

        # tcEndereco (ABRASF): Bairro e Cep sao obrigatorios (minOccurs=1); tsCep = [0-9]{8}.
        end = etree.SubElement(tomador, '{%s}Endereco' % ns)
        etree.SubElement(end, '{%s}Endereco' % ns).text = (
            (tomador_endereco.get('logradouro') or '').strip() or 'Nao informado'
        )
        etree.SubElement(end, '{%s}Numero' % ns).text = (
            (tomador_endereco.get('numero') or '').strip() or 'S/N'
        )
        compl = (tomador_endereco.get('complemento') or '').strip()
        if compl:
            etree.SubElement(end, '{%s}Complemento' % ns).text = compl
        bairro = (tomador_endereco.get('bairro') or '').strip() or 'Nao informado'
        etree.SubElement(end, '{%s}Bairro' % ns).text = bairro[:60]
        # Código IBGE do município do tomador (se fornecido no endereço, senão usa RP)
        cod_mun_tomador = (tomador_endereco.get('codigo_municipio') or '').strip()
        if not cod_mun_tomador:
            cod_mun_tomador = COD_MUNICIPIO_RP
        etree.SubElement(end, '{%s}CodigoMunicipio' % ns).text = cod_mun_tomador
        etree.SubElement(end, '{%s}Uf' % ns).text = (
            (tomador_endereco.get('uf') or 'SP').strip()[:2] or 'SP'
        )
        cep = _somente_digitos(tomador_endereco.get('cep', ''))[:8]
        if len(cep) != 8:
            cep = '00000000'
        etree.SubElement(end, '{%s}Cep' % ns).text = cep

        # Contato do tomador (email e telefone)
        tomador_email = (tomador_endereco.get('email') or '').strip()
        tomador_telefone = _somente_digitos(tomador_endereco.get('telefone', ''))[:11]
        if tomador_email or tomador_telefone:
            contato = etree.SubElement(tomador, '{%s}Contato' % ns)
            if tomador_telefone:
                etree.SubElement(contato, '{%s}Telefone' % ns).text = tomador_telefone
            if tomador_email:
                etree.SubElement(contato, '{%s}Email' % ns).text = tomador_email[:80]

        # --- Flags ---
        regime = getattr(self, '_regime_especial', '0') or ''
        if regime and regime != '0':
            etree.SubElement(inf, '{%s}RegimeEspecialTributacao' % ns).text = regime
        optante = '1' if self._optante_simples else '2'
        etree.SubElement(inf, '{%s}OptanteSimplesNacional' % ns).text = optante
        incentivo = '1' if self._incentivador_cultural else '2'
        etree.SubElement(inf, '{%s}IncentivoFiscal' % ns).text = incentivo

        # Sem pretty_print: evita espaços extras no XML assinado (C14N / validação).
        xml_str = etree.tostring(root, encoding='unicode', pretty_print=False)
        logger.info(
            'XML EnviarLoteRpsEnvio construido: RPS %s serie %r lote %s, Valor R$ %s',
            numero_rps,
            serie_rps,
            numero_lote,
            valor,
        )
        return xml_str

    # ------------------------------------------------------------------
    # Emitir NFS-e
    # ------------------------------------------------------------------
    def emitir_nfse(
        self,
        prestador_cnpj: str,
        prestador_inscricao_municipal: str,
        prestador_razao_social: str,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_endereco: Dict[str, str],
        servico_codigo: str,
        servico_descricao: str,
        valor_servicos: Decimal,
        aliquota_iss: Decimal,
        numero_rps: int,
        serie_rps: str = 'E',
        tipo_rps: int = 1,
        data_emissao: Optional[datetime] = None,
        codigo_cnae: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Emite NFS-e (1 RPS): tenta ``RecepcionarLoteRpsSincrono`` com raiz ABRASF correta; se falha de
        transporte/SOAP, usa ``RecepcionarLoteRps`` e consulta o lote quando vier apenas protocolo.
        """
        try:
            if data_emissao is None:
                data_emissao = datetime.now()

            xml_rps = self._construir_xml_gerar_nfse(
                prestador_cnpj=prestador_cnpj,
                prestador_inscricao_municipal=prestador_inscricao_municipal,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                servico_codigo=servico_codigo,
                servico_descricao=servico_descricao,
                valor_servicos=valor_servicos,
                aliquota_iss=aliquota_iss,
                numero_rps=numero_rps,
                serie_rps=serie_rps,
                tipo_rps=tipo_rps,
                data_emissao=data_emissao,
                codigo_cnae=codigo_cnae,
            )

            xml_sinc_u = _xml_envio_para_raiz_sincrono_sem_assinar(xml_rps)
            xml_sinc_assinado = self._assinar_xml(xml_sinc_u)
            logger.info('ISSNet: tentando RecepcionarLoteRpsSincrono (EnviarLoteRpsSincronoEnvio assinado)')
            parsed_s, _body_s = self._post_soap_operacao(
                nome_operacao='RecepcionarLoteRpsSincrono',
                soap_action_uri=SOAP_ACTION_RECEPCIONAR_LOTE_RPS_SINCRONO,
                dados_xml=xml_sinc_assinado,
            )
            if parsed_s.get('success'):
                resultado = parsed_s
            elif _issnet_erro_parece_negocio_abrasf(parsed_s.get('error') or ''):
                resultado = parsed_s
            else:
                xml_assinado = self._assinar_xml(xml_rps)
                resultado = self._enviar_soap_direto(
                    xml_assinado,
                    prestador_cnpj=prestador_cnpj,
                    prestador_inscricao_municipal=prestador_inscricao_municipal,
                )
            resultado['numero_rps'] = numero_rps
            if resultado.get('success'):
                resultado['valor'] = valor_servicos
                resultado.setdefault('tomador_nome', tomador_nome)
                resultado.setdefault('tomador_cpf_cnpj', tomador_cpf_cnpj)
                resultado.setdefault(
                    'servico_descricao',
                    (servico_descricao or '')[:500],
                )
            return resultado

        except Exception as e:
            logger.exception('Erro ao emitir NFS-e: %s', e)
            return {'success': False, 'error': str(e), 'numero_rps': numero_rps}

    # ------------------------------------------------------------------
    # Protocolo / consulta de lote (fluxo assincrono ABRASF)
    # ------------------------------------------------------------------
    @staticmethod
    def _extrair_protocolo_lote(xml_abrasf: str) -> Optional[str]:
        """Numero do protocolo em EnviarLoteRpsResposta (qualquer namespace)."""
        if not (xml_abrasf or '').strip():
            return None
        try:
            root = etree.fromstring(
                xml_abrasf.encode('utf-8') if isinstance(xml_abrasf, str) else xml_abrasf
            )
            for el in root.iter():
                if etree.QName(el.tag).localname == 'Protocolo':
                    t = (el.text or '').strip()
                    if t:
                        return t
        except Exception:
            return None
        return None

    def _consultar_lote_rps_ate_nfse(
        self,
        protocolo: str,
        prestador_cnpj: str,
        prestador_inscricao_municipal: str,
        tentativas: int = 20,
        intervalo_s: float = 3.0,
    ) -> Dict[str, Any]:
        """ConsultarLoteRps ate obter CompNfse ou esgotar tentativas."""
        cnpj = _somente_digitos(prestador_cnpj)
        im = (prestador_inscricao_municipal or '').strip()
        xml_consulta = (
            f'<ConsultarLoteRpsEnvio xmlns="{NS_NFSE}">'
            f'<Prestador><CpfCnpj><Cnpj>{cnpj}</Cnpj></CpfCnpj>'
            f'<InscricaoMunicipal>{_xml_escape(im)}</InscricaoMunicipal></Prestador>'
            f'<Protocolo>{_xml_escape((protocolo or "").strip())}</Protocolo>'
            f'</ConsultarLoteRpsEnvio>'
        )
        for tent in range(tentativas):
            if tent > 0:
                time.sleep(intervalo_s)
            out, _xml_b = self._post_soap_operacao(
                nome_operacao='ConsultarLoteRps',
                soap_action_uri=SOAP_ACTION_CONSULTAR_LOTE_RPS,
                dados_xml=xml_consulta,
            )
            if out.get('success'):
                return out
            err = out.get('error') or ''
            # E178 = lote aguardando processamento — continuar tentando
            pode_retry = (
                'NFS-e nao encontrada na resposta' in err
                or 'E178' in err
                or 'aguardando processamento' in err.lower()
            )
            if pode_retry and tent < tentativas - 1:
                logger.info(
                    'ISSNet consulta lote protocolo %s tentativa %s/%s — %s',
                    protocolo,
                    tent + 1,
                    tentativas,
                    'aguardando processamento' if 'E178' in err else 'sem NF ainda',
                )
                continue
            return out
        return {'success': False, 'error': 'Tempo esgotado aguardando NFS-e apos envio do lote (60s).'}

    def _post_soap_operacao(
        self,
        nome_operacao: str,
        soap_action_uri: str,
        dados_xml: str,
    ):
        return post_soap_operacao(
            base_url=self.base_url,
            wsdl_url=self.wsdl_url,
            certificado_path=self.certificado_path,
            senha_certificado=self.senha_certificado,
            nome_operacao=nome_operacao,
            soap_action_uri=soap_action_uri,
            dados_xml=dados_xml,
        )

    # ------------------------------------------------------------------
    # Enviar via requests direto (formato exato da lib PHP)
    # ------------------------------------------------------------------
    def _enviar_soap_direto(
        self,
        xml_dados: str,
        prestador_cnpj: str = '',
        prestador_inscricao_municipal: str = '',
    ) -> Dict[str, Any]:
        """RecepcionarLoteRps; se vier apenas Protocolo, consulta o lote ate obter a NFSe."""
        parsed, xml_body = self._post_soap_operacao(
            nome_operacao='RecepcionarLoteRps',
            soap_action_uri=SOAP_ACTION_RECEPCIONAR_LOTE_RPS,
            dados_xml=xml_dados,
        )
        if parsed.get('success'):
            return parsed
        err0 = (parsed.get('error') or '')
        if 'Erro genérico do webservice ISSNet' in err0 or 'sem detail' in err0.lower():
            logger.info(
                'ISSNet: falha generica no RecepcionarLoteRps; fluxo sincrono e feito em emitir_nfse '
                '(raiz EnviarLoteRpsSincronoEnvio). Segue apenas consulta por protocolo se houver.'
            )
        proto = self._extrair_protocolo_lote(xml_body)
        if proto and prestador_cnpj and prestador_inscricao_municipal:
            logger.info('ISSNet envio retornou protocolo %s; consultando lote...', proto)
            return self._consultar_lote_rps_ate_nfse(
                proto,
                prestador_cnpj,
                prestador_inscricao_municipal,
            )
        return parsed

    # ------------------------------------------------------------------
    # Enviar via zeep (mantido como fallback)
    # ------------------------------------------------------------------
    def _enviar_gerar_nfse(self, xml_assinado: str) -> Dict[str, Any]:
        """
        Chama operacao RecepcionarLoteRps do webservice ISSNet (fallback zeep).
        """
        try:
            client = self._get_soap_client()
            logger.info('XML enviado ao ISSNet (nfseDadosMsg): %s', xml_assinado[:2000])
            with client.settings(raw_response=True):
                response = client.service.RecepcionarLoteRps(
                    nfseCabecMsg=CABEC_MSG,
                    nfseDadosMsg=xml_assinado,
                )
            # response eh um requests.Response
            resp_text = response.text if hasattr(response, 'text') else str(response)
            logger.info('Resposta ISSNet HTTP %s, preview: %s',
                        getattr(response, 'status_code', '?'), resp_text[:500])

            # Extrair conteudo do SOAP Body
            xml_body = self._extrair_body_soap(resp_text)
            return self._parse_resposta_xml(xml_body)
        except Exception as e:
            logger.exception('Erro ao enviar GerarNfse: %s', e)
            return {'success': False, 'error': str(e)}

    def _extrair_body_soap(self, soap_xml: str) -> str:
        return extrair_body_soap(soap_xml)

    def _parse_resposta_xml(self, xml_str: str) -> Dict[str, Any]:
        return parse_resposta_xml(xml_str)

    def _extrair_erros(self, texto: str) -> str:
        return extrair_erros(texto)

    def _parse_resposta_cancelamento(self, xml_str: str) -> Dict[str, Any]:
        return parse_resposta_cancelamento(xml_str)

    def _interpretar_cancelamento(self, parsed: Dict[str, Any], xml_body: str) -> Dict[str, Any]:
        return interpretar_cancelamento(parsed, xml_body)

    # ------------------------------------------------------------------
    # Consultar NFS-e por RPS
    # ------------------------------------------------------------------
    def consultar_url_nfse(self, numero_nf: str, prestador_cnpj: str = '', inscricao_municipal: str = '') -> Dict[str, Any]:
        """
        Chama ConsultarUrlNfse para obter a URL do PDF/portal oficial da NFS-e no ISSNet.
        Retorna {'success': True, 'url': '...'} ou {'success': False, 'error': '...'}.
        """
        try:
            cnpj = _somente_digitos(prestador_cnpj or self.usuario or '')
            im = (inscricao_municipal or '').strip()
            # Formato conforme modelo do suporte Nota Control:
            # Usar NumeroNfse como opção de busca + Pagina obrigatório
            xml_consulta = (
                f'<ConsultarUrlNfseEnvio xmlns="{NS_NFSE}">'
                f'<Pedido>'
                f'<Prestador>'
                f'<CpfCnpj><Cnpj>{cnpj}</Cnpj></CpfCnpj>'
                f'<InscricaoMunicipal>{_xml_escape(im)}</InscricaoMunicipal>'
                f'</Prestador>'
                f'<NumeroNfse>{_xml_escape(str(numero_nf))}</NumeroNfse>'
                f'<Pagina>1</Pagina>'
                f'</Pedido>'
                f'</ConsultarUrlNfseEnvio>'
            )
            # Assinar o XML completo (Signature fica fora do Pedido, dentro do ConsultarUrlNfseEnvio)
            try:
                xml_consulta = self._assinar_xml(xml_consulta)
            except Exception as e:
                logger.warning('Erro ao assinar ConsultarUrlNfse (tentando sem assinatura): %s', e)
            parsed, xml_body = self._post_soap_operacao(
                nome_operacao='ConsultarUrlNfse',
                soap_action_uri='http://nfse.abrasf.org.br/ConsultarUrlNfse',
                dados_xml=xml_consulta,
            )
            # Logar resposta bruta completa para diagnóstico
            logger.info('ConsultarUrlNfse resposta bruta completa: %s', xml_body)
            logger.info('ConsultarUrlNfse parsed: %s', parsed)

            resp_str = xml_body or ''

            # Tentar extrair URL da resposta XML — vários formatos possíveis
            for tag in ('Url', 'url', 'Link', 'link', 'UrlNfse', 'urlNfse'):
                url_match = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', resp_str, re.IGNORECASE | re.DOTALL)
                if url_match:
                    url = url_match.group(1).strip()
                    # Ignorar namespaces e URLs de schema
                    if url and url.startswith('http') and not any(x in url for x in ['abrasf.org.br', 'xmlsoap.org', 'w3.org', 'schemas.']):
                        logger.info('ConsultarUrlNfse URL encontrada: %s', url)
                        return {'success': True, 'url': url}

            # Procurar qualquer URL http que não seja o namespace
            for http_match in re.finditer(r'(https?://[^\s<>"&]+)', resp_str):
                url = http_match.group(1)
                if 'abrasf.org.br' not in url and 'xmlsoap.org' not in url and 'w3.org' not in url and 'schemas.' not in url:
                    logger.info('ConsultarUrlNfse URL via fallback: %s', url)
                    return {'success': True, 'url': url}

            if parsed.get('success') is False:
                return {'success': False, 'error': parsed.get('error', ''), 'raw': resp_str[:500]}
            return {'success': False, 'error': f'URL não encontrada na resposta', 'raw': resp_str[:500]}
        except Exception as e:
            logger.warning('Erro ao consultar URL NFS-e ISSNet: %s', e)
            return {'success': False, 'error': str(e)}

    def inferir_cancelada_por_url(self, *, url: str) -> Dict[str, Any]:
        """
        Busca a página do portal/visualização oficial retornada pelo ISSNet e tenta inferir se a nota
        está cancelada (ex.: "CANCELADA", "SEM VALOR LEGAL").

        Isso é um fallback de sincronização quando a consulta por RPS falha (E160/E183).
        """
        try:
            import requests

            u = (url or '').strip()
            if not u.startswith('http'):
                return {'success': False, 'error': 'URL inválida para verificação.'}

            r = requests.get(u, timeout=(6, 18), headers={'User-Agent': 'LWK-Sistemas/CRM'})
            txt = (r.text or '')[:200000]  # limitar
            up = txt.upper()
            cancelada = ('SEM VALOR LEGAL' in up) or ('CANCELAD' in up)
            return {'success': True, 'cancelada': bool(cancelada)}
        except Exception as e:
            logger.warning('Erro ao verificar cancelamento via URL ISSNet: %s', e)
            return {'success': False, 'error': str(e)}

    def consultar_nfse(self, numero_nf: str) -> Dict[str, Any]:
        """Consulta NFS-e emitida por RPS (compat: método legado)."""
        try:
            xml_consulta = (
                f'<ConsultarNfseRpsEnvio xmlns="{NS_NFSE}">'
                f'<IdentificacaoRps>'
                f'<Numero>{numero_nf}</Numero>'
                f'<Serie>E</Serie>'
                f'<Tipo>1</Tipo>'
                f'</IdentificacaoRps>'
                f'<Prestador>'
                f'<CpfCnpj><Cnpj>{self.usuario}</Cnpj></CpfCnpj>'
                f'</Prestador>'
                f'</ConsultarNfseRpsEnvio>'
            )
            client = self._get_soap_client()
            response = client.service.ConsultarNfsePorRps(
                nfseCabecMsg=CABEC_MSG,
                nfseDadosMsg=xml_consulta,
            )
            return {'success': True, 'data': str(response)}
        except Exception as e:
            logger.exception('Erro ao consultar NFS-e: %s', e)
            return {'success': False, 'error': str(e)}

    def consultar_nfse_por_rps(
        self,
        *,
        numero_rps: int,
        serie_rps: str,
        tipo_rps: str = '1',
        prestador_cnpj: str,
        inscricao_municipal: str,
    ) -> Dict[str, Any]:
        """
        Consulta NFS-e por RPS (ABRASF 2.04 / ISSNet).
        Usado para sincronizar status (ex.: cancelada no portal).
        """
        try:
            cnpj_digits = re.sub(r'\D', '', prestador_cnpj or self.usuario or '')
            im = (inscricao_municipal or '').strip()
            serie = (serie_rps or '').strip() or '1'
            xml_consulta = (
                f'<ConsultarNfseRpsEnvio xmlns="{NS_NFSE}">'
                f'<IdentificacaoRps>'
                f'<Numero>{int(numero_rps)}</Numero>'
                f'<Serie>{serie}</Serie>'
                f'<Tipo>{tipo_rps}</Tipo>'
                f'</IdentificacaoRps>'
                f'<Prestador>'
                f'<CpfCnpj><Cnpj>{cnpj_digits}</Cnpj></CpfCnpj>'
                f'<InscricaoMunicipal>{im}</InscricaoMunicipal>'
                f'</Prestador>'
                f'</ConsultarNfseRpsEnvio>'
            )

            parsed, xml_body = self._post_soap_operacao(
                nome_operacao='ConsultarNfsePorRps',
                soap_action_uri='http://nfse.abrasf.org.br/ConsultarNfsePorRps',
                dados_xml=xml_consulta,
            )

            resp_str = (xml_body or str(parsed or '')).strip()
            if not resp_str:
                return {'success': False, 'error': 'Resposta vazia ao consultar NFS-e por RPS.'}

            # Erro de negócio (ListaMensagemRetorno), não confundir com sucesso de consulta.
            if re.search(r'<\s*ListaMensagemRetorno\b', resp_str, re.I):
                return {'success': False, 'error': self._extrair_erros(resp_str), 'raw': resp_str[:500]}

            cancelada = bool(
                re.search(
                    r'<\s*(Cancelamento|NfseCancelada|ConfirmacaoCancelamento)\b',
                    resp_str,
                    re.I,
                )
                or re.search(r'DataHoraCancelamento', resp_str, re.I)
            )
            if cancelada:
                return {'success': True, 'cancelada': True, 'raw_xml': resp_str[:8000]}

            if parsed and parsed.get('success'):
                return {'success': True, 'cancelada': False, 'raw_xml': resp_str[:8000]}

            if parsed and parsed.get('success') is False:
                return parsed

            return {'success': True, 'cancelada': False, 'raw_xml': resp_str[:8000]}
        except Exception as e:
            logger.exception('Erro ao consultar NFS-e por RPS: %s', e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------
    # Cancelar NFS-e
    # ------------------------------------------------------------------
    def cancelar_nfse(self, numero_nf: str, motivo: str, prestador_cnpj: str = '', inscricao_municipal: str = '', codigo_cancelamento: str = '1') -> Dict[str, Any]:
        """Cancela NFS-e emitida via ISSNet."""
        try:
            cnpj_digits = re.sub(r'\D', '', prestador_cnpj or self.usuario or '')
            im = (inscricao_municipal or '').strip()
            
            def _tentar_cancelamento(xml_payload: str, *, label: str):
                xml_assinado = self._assinar_xml(xml_payload)
                parsed_raw, xml_body = self._post_soap_operacao(
                    nome_operacao='CancelarNfse',
                    soap_action_uri='http://nfse.abrasf.org.br/CancelarNfse',
                    dados_xml=xml_assinado,
                )
                parsed = self._interpretar_cancelamento(parsed_raw or {}, xml_body or '')
                if parsed.get('success') is False:
                    logger.warning('ISSNet cancelar_nfse falhou (%s): %s', label, parsed.get('error'))
                elif parsed.get('success'):
                    logger.info('ISSNet cancelar_nfse OK (%s)', label)
                return parsed, xml_body

            # Tentativa 1 (padrão): assina Pedido (Id=Pedido1) com InfPedidoCancelamento Id=s01.
            xml_cancelar_1 = (
                f'<CancelarNfseEnvio xmlns="{NS_NFSE}">'
                f'<Pedido>'
                f'<InfPedidoCancelamento Id="s01">'
                f'<IdentificacaoNfse>'
                f'<Numero>{numero_nf}</Numero>'
                f'<CpfCnpj><Cnpj>{cnpj_digits}</Cnpj></CpfCnpj>'
                f'<InscricaoMunicipal>{im}</InscricaoMunicipal>'
                f'<CodigoMunicipio>{COD_MUNICIPIO_RP}</CodigoMunicipio>'
                f'</IdentificacaoNfse>'
                f'<CodigoCancelamento>{codigo_cancelamento}</CodigoCancelamento>'
                f'</InfPedidoCancelamento>'
                f'</Pedido>'
                f'</CancelarNfseEnvio>'
            )

            parsed, xml_body = _tentar_cancelamento(xml_cancelar_1, label='pedido')

            # Tentativa 2 (fallback): assina InfPedidoCancelamento (Id=cancelNNN).
            if parsed and parsed.get('success') is False:
                nf_digits = re.sub(r'\D', '', str(numero_nf))
                inf_id = f'cancel{nf_digits}' if nf_digits else 'cancels01'
                xml_cancelar_2 = (
                    f'<CancelarNfseEnvio xmlns="{NS_NFSE}">'
                    f'<Pedido>'
                    f'<InfPedidoCancelamento Id="{inf_id}">'
                    f'<IdentificacaoNfse>'
                    f'<Numero>{numero_nf}</Numero>'
                    f'<CpfCnpj><Cnpj>{cnpj_digits}</Cnpj></CpfCnpj>'
                    f'<InscricaoMunicipal>{im}</InscricaoMunicipal>'
                    f'<CodigoMunicipio>{COD_MUNICIPIO_RP}</CodigoMunicipio>'
                    f'</IdentificacaoNfse>'
                    f'<CodigoCancelamento>{codigo_cancelamento}</CodigoCancelamento>'
                    f'</InfPedidoCancelamento>'
                    f'</Pedido>'
                    f'</CancelarNfseEnvio>'
                )
                parsed, xml_body = _tentar_cancelamento(xml_cancelar_2, label='inf_pedido')

            if parsed.get('success'):
                return parsed

            return self._interpretar_cancelamento(parsed, xml_body or '')
        except Exception as e:
            logger.exception('Erro ao cancelar NFS-e: %s', e)
            return {'success': False, 'error': str(e)}
