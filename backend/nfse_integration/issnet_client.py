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
from nfse_integration.issnet_soap import (
    issnet_corpo_parece_xml,
    issnet_decodificar_corpo,
    issnet_fault_soap_generico,
    montar_soap_envelope_aninhado,
    montar_soap_envelope_cdata,
    montar_soap_envelope_xsd_string,
    strip_xml_declaration,
)

logger = logging.getLogger(__name__)

# Aliases internos (compatibilidade com chamadas existentes no módulo).
_strip_xml_declaration = strip_xml_declaration
_montar_soap_envelope_issnet_xsd_string = montar_soap_envelope_xsd_string
_montar_soap_envelope_issnet = montar_soap_envelope_aninhado
_montar_soap_envelope_issnet_cdata = montar_soap_envelope_cdata
_issnet_fault_soap_generico = issnet_fault_soap_generico
_issnet_corpo_parece_xml = issnet_corpo_parece_xml
_issnet_decodificar_corpo = issnet_decodificar_corpo


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


def _carregar_certificado(pfx_path: str, senha: str):
    """Carrega chave privada e certificado de um arquivo .pfx."""
    from cryptography.hazmat.primitives.serialization import pkcs12
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()
    private_key, certificate, extra = pkcs12.load_key_and_certificates(
        pfx_data, senha.encode()
    )
    if certificate is None:
        raise ValueError('O arquivo .pfx nao contem certificado valido.')
    return private_key, certificate, extra


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
        from zeep import Client
        from zeep.transports import Transport
        from requests import Session

        session = Session()
        session.headers.update({'User-Agent': 'LWK-Sistemas/CRM'})
        transport = Transport(session=session, timeout=30)
        self._soap_client = Client(self.wsdl_url, transport=transport)

        # Forcar URL absoluta (WSDL define endpoint relativo)
        for service in self._soap_client.wsdl.services.values():
            for port in service.ports.values():
                port.binding_options['address'] = self.base_url

        logger.info('Cliente SOAP ISSNet inicializado: %s', self.ambiente)
        return self._soap_client

    def _zeep_chamar_com_mtls(
        self,
        nome_operacao: str,
        dados_xml: str,
        cert_path: str,
        key_path: str,
        timeout_s: int = 25,
    ):
        """
        Uma chamada SOAP via Zeep com certificado cliente (mTLS) na sessao requests.
        Serializa nfseCabecMsg/nfseDadosMsg como xsd:string conforme o WSDL (evita Fault
        generico de desserializacao do ASMX em POSTs manuais).
        """
        from zeep import Client
        from zeep.transports import Transport
        from requests import Session

        session = Session()
        session.cert = (cert_path, key_path)
        session.headers['User-Agent'] = 'LWK-Sistemas/CRM (ISSNet ABRASF 2.04)'
        transport = Transport(session=session, timeout=timeout_s)
        client = Client(self.wsdl_url, transport=transport)
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                port.binding_options['address'] = self.base_url
        op = getattr(client.service, nome_operacao, None)
        if op is None:
            raise AttributeError(f'Operacao {nome_operacao!r} nao existe no WSDL ISSNet')
        dados = _strip_xml_declaration(dados_xml or '')
        with client.settings(raw_response=True, strict=False):
            return op(nfseCabecMsg=CABEC_MSG, nfseDadosMsg=dados)

    # ------------------------------------------------------------------
    # Assinatura XML
    # ------------------------------------------------------------------
    def _assinar_xml(self, xml_str: str) -> str:
        """
        Assina XML com certificado digital A1 usando python-xmlsec.

        Dupla assinatura alinhada ao sped-nfse-issnet (PHP): primeiro o ``Rps`` externo
        (ListaRps/Rps) com Reference URI vazia e transform enveloped; depois a raiz
        ``EnviarLoteRpsEnvio`` tambem com URI vazia. O XSD ABRASF nao declara atributo
        ``Id`` em ``EnviarLoteRpsEnvio`` — colocar ``Id`` invalida o XML e o ASMX costuma
        responder Fault generico. O PHP, sem ``Id`` na raiz, usa URI vazia no 2o Signer.
        """
        import xmlsec

        root = etree.fromstring(xml_str.encode('utf-8'))

        # Carregar chave do certificado PFX (converter para PEM primeiro)
        private_key_obj, cert_obj, _ = _carregar_certificado(
            self.certificado_path, self.senha_certificado
        )
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

        key_pem = private_key_obj.private_bytes(
            Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
        )
        cert_pem = cert_obj.public_bytes(Encoding.PEM)

        # Chave e certificado em PEM separados: o PEM unificado carrega a chave mas
        # nao associa o X509 ao template; load_cert_from_memory preenche X509Data.
        key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
        key.load_cert_from_memory(cert_pem, xmlsec.constants.KeyDataFormatPem)

        def _append_x509_template(sig_node):
            key_info = xmlsec.template.ensure_key_info(sig_node)
            x509_data = xmlsec.template.add_x509_data(key_info)
            xmlsec.template.x509_data_add_certificate(x509_data)

        def _template_sig_enveloped_only(parent_el, ref_uri):
            """Monta Signature como ultimo filho de parent_el; Reference so com enveloped."""
            sig_node = xmlsec.template.create(
                parent_el,
                xmlsec.constants.TransformInclC14N,
                xmlsec.constants.TransformRsaSha1,
            )
            parent_el.append(sig_node)
            ref = xmlsec.template.add_reference(
                sig_node,
                xmlsec.constants.TransformSha1,
                uri=ref_uri,
            )
            xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
            _append_x509_template(sig_node)
            return sig_node

        ns = NS_NFSE
        root_local = etree.QName(root.tag).localname if root.tag else ''

        def _sign_cancelamento_por_pedido(root_el):
            """Assina cancelamento referenciando o elemento Pedido (Id)."""
            pedido = root_el.find('{%s}Pedido' % ns)
            if pedido is None:
                return None
            pedido_id = (pedido.get('Id') or '').strip() or 'Pedido1'
            pedido.set('Id', pedido_id)
            sig_ped = _template_sig_enveloped_only(pedido, f'#{pedido_id}')
            ctx_c = xmlsec.SignatureContext()
            ctx_c.key = key
            ctx_c.register_id(pedido, 'Id', None)
            ctx_c.sign(sig_ped)
            return pedido_id

        def _sign_cancelamento_por_inf_pedido(root_el):
            """
            Assina cancelamento referenciando InfPedidoCancelamento (Id).
            Algumas prefeituras/instâncias ISSNet rejeitam a assinatura no Pedido.
            """
            pedido = root_el.find('{%s}Pedido' % ns)
            if pedido is None:
                return None
            inf = pedido.find('{%s}InfPedidoCancelamento' % ns)
            if inf is None:
                return None
            inf_id = (inf.get('Id') or '').strip() or 's01'
            inf.set('Id', inf_id)
            sig_inf = _template_sig_enveloped_only(pedido, f'#{inf_id}')
            ctx_c = xmlsec.SignatureContext()
            ctx_c.key = key
            ctx_c.register_id(inf, 'Id', None)
            ctx_c.sign(sig_inf)
            return inf_id

        # Cancelamento ABRASF: padrão principal é assinar o elemento Pedido (Id).
        if root_local == 'CancelarNfseEnvio':
            pedido = root.find('{%s}Pedido' % ns)
            inf = pedido.find('{%s}InfPedidoCancelamento' % ns) if pedido is not None else None
            inf_id = (inf.get('Id') or '').strip() if inf is not None else ''
            # Se o chamador marcou um Id "cancel..." no InfPedidoCancelamento, preferimos assinar esse nó.
            if inf_id.lower().startswith('cancel'):
                _sign_cancelamento_por_inf_pedido(root)
                result = etree.tostring(root, encoding='unicode')
                logger.info('XML assinado com xmlsec (cancelamento InfPedidoCancelamento)')
                logger.info('XML CANCELAMENTO ASSINADO COMPLETO: %s', result)
                return result

            pedido_id = _sign_cancelamento_por_pedido(root)
            if not pedido_id:
                _sign_cancelamento_por_inf_pedido(root)
            result = etree.tostring(root, encoding='unicode')
            logger.info('XML assinado com xmlsec (cancelamento Pedido)')
            logger.info('XML CANCELAMENTO ASSINADO COMPLETO: %s', result)
            return result

        # ConsultarUrlNfse: assinatura enveloped na raiz (URI vazia)
        if root_local == 'ConsultarUrlNfseEnvio':
            sig_consulta = _template_sig_enveloped_only(root, '')
            ctx_c = xmlsec.SignatureContext()
            ctx_c.key = key
            ctx_c.sign(sig_consulta)
            result = etree.tostring(root, encoding='unicode')
            logger.info('XML assinado com xmlsec (ConsultarUrlNfse)')
            return result

        lista = root.find('.//{%s}ListaRps' % ns)
        outer_rps = lista.find('{%s}Rps' % ns) if lista is not None else None

        if outer_rps is None:
            logger.warning('Assinatura: ListaRps/Rps externo nao encontrado; XML nao assinado.')
        else:
            sig_rps = _template_sig_enveloped_only(outer_rps, '')
            ctx = xmlsec.SignatureContext()
            ctx.key = key
            ctx.sign(sig_rps)

        if root_local not in ('EnviarLoteRpsEnvio', 'EnviarLoteRpsSincronoEnvio'):
            logger.warning('Assinatura: raiz inesperada %s; pulando segunda assinatura.', root_local)
        else:
            # Nao definir Id na raiz: servico_enviar_lote_rps_envio.xsd nao permite (sem anyAttribute).
            sig_envio = _template_sig_enveloped_only(root, '')
            ctx2 = xmlsec.SignatureContext()
            ctx2.key = key
            ctx2.sign(sig_envio)

        result = etree.tostring(root, encoding='unicode')
        logger.info('XML assinado com xmlsec (RSA-SHA1, dupla assinatura ISSNET)')
        return result

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
        """POST SOAP 1.1 com mTLS; envelope e Content-Type alinhados ao sped-nfse-issnet (PHP)."""
        import os
        import tempfile

        import requests as req

        logger.debug('ISSNet %s SOAPAction=%s', nome_operacao, soap_action_uri)

        cert_path = None
        key_path = None
        try:
            private_key_obj, cert_obj, extra = _carregar_certificado(
                self.certificado_path, self.senha_certificado
            )
            from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

            key_pem = private_key_obj.private_bytes(
                Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
            )
            cert_pem = cert_obj.public_bytes(Encoding.PEM)
            if extra:
                for add in extra:
                    if add is not None:
                        cert_pem += add.public_bytes(Encoding.PEM)
            ktf = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
            ctf = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
            try:
                ktf.write(key_pem)
                ctf.write(cert_pem)
                ktf.flush()
                ctf.flush()
                key_path = ktf.name
                cert_path = ctf.name
            finally:
                ktf.close()
                ctf.close()

            http_timeout = (8, 20)

            # Zeep + mTLS: serializa nfse*Msg como o WSDL exige (xsd:string); evita varios Faults genericos.
            if nome_operacao in (
                'RecepcionarLoteRps',
                'RecepcionarLoteRpsSincrono',
                'ConsultarLoteRps',
                'ConsultarUrlNfse',
                'CancelarNfse',
                'ConsultarNfsePorRps',
            ):
                try:
                    rz = self._zeep_chamar_com_mtls(
                        nome_operacao,
                        dados_xml,
                        cert_path,
                        key_path,
                        timeout_s=http_timeout[1],
                    )
                    txt_z = (getattr(rz, 'text', None) or '') if rz is not None else ''
                    sc = getattr(rz, 'status_code', None)
                    logger.info(
                        'ISSNet %s zeep+mTLS HTTP %s, preview: %s',
                        nome_operacao,
                        sc,
                        txt_z[:400],
                    )
                    if (sc is not None and sc >= 400) or 'Fault' in txt_z:
                        logger.error('ISSNet zeep+mTLS resposta (ate 8000 chars): %s', txt_z[:8000])
                    if _issnet_corpo_parece_xml(txt_z):
                        if not _issnet_fault_soap_generico(txt_z):
                            xml_body = self._extrair_body_soap(txt_z)
                            return self._parse_resposta_xml(xml_body), xml_body
                    logger.warning(
                        'ISSNet %s zeep+mTLS sem sucesso (Fault generico ou resposta nao parseavel); '
                        'tentando POST manual',
                        nome_operacao,
                    )
                except Exception as e:
                    logger.warning('ISSNet %s zeep+mTLS: %s — tentando POST manual', nome_operacao, e)

            def _headers(content_type: str) -> dict:
                return {
                    'Content-Type': content_type,
                    'SOAPAction': f'"{soap_action_uri}"',
                    'Connection': 'close',
                    'Accept': 'text/xml',
                    'User-Agent': 'LWK-Sistemas/CRM (ISSNet ABRASF 2.04)',
                }

            # POST manual: ISSNet varia o esperado por operação.
            #
            # - Em geral, a ordem "XML aninhado" (como lib PHP) funciona bem.
            # - Para ConsultarNfsePorRps, alguns ambientes rejeitam o XML aninhado com E160
            #   e aceitam o payload como xsd:string/CDATA (WSDL/ASMX).
            if nome_operacao == 'ConsultarNfsePorRps':
                strategies = (
                    (
                        _montar_soap_envelope_issnet_xsd_string(nome_operacao, dados_xml),
                        _headers('text/xml; charset=utf-8'),
                        'xsd:string (XML escapado) + text/xml',
                    ),
                    (
                        _montar_soap_envelope_issnet_cdata(nome_operacao, dados_xml),
                        _headers('text/xml; charset=utf-8'),
                        'CDATA + text/xml',
                    ),
                    (
                        _montar_soap_envelope_issnet(nome_operacao, dados_xml),
                        _headers('application/soap+xml; charset=utf-8'),
                        'XML aninhado + application/soap+xml (PHP)',
                    ),
                )
            else:
                # Ordem como lib PHP (aninhado), depois CDATA, por último string escapada.
                strategies = (
                    (
                        _montar_soap_envelope_issnet(nome_operacao, dados_xml),
                        _headers('application/soap+xml; charset=utf-8'),
                        'XML aninhado + application/soap+xml (PHP)',
                    ),
                    (
                        _montar_soap_envelope_issnet_cdata(nome_operacao, dados_xml),
                        _headers('text/xml; charset=utf-8'),
                        'CDATA + text/xml',
                    ),
                    (
                        _montar_soap_envelope_issnet_xsd_string(nome_operacao, dados_xml),
                        _headers('text/xml; charset=utf-8'),
                        'xsd:string (XML escapado) + text/xml',
                    ),
                )

            def _do_post(soap_body: str, hdrs: dict):
                return req.post(
                    self.base_url,
                    data=soap_body.encode('utf-8'),
                    headers=hdrs,
                    timeout=http_timeout,
                    cert=(cert_path, key_path),
                )

            r = None
            for strat_idx, (soap_try, headers_try, label) in enumerate(strategies):
                logger.info(
                    'ISSNet SOAP %s (~%d bytes, %s) com mTLS',
                    nome_operacao,
                    len(soap_try.encode('utf-8')),
                    label,
                )
                try:
                    r = _do_post(soap_try, headers_try)
                except (
                    req.exceptions.ConnectionError,
                    req.exceptions.ChunkedEncodingError,
                    req.exceptions.ReadTimeout,
                ) as e:
                    logger.warning('ISSNet SOAP POST: erro de conexao, uma nova tentativa: %s', e)
                    time.sleep(1.5)
                    r = _do_post(soap_try, headers_try)

                logger.info(
                    'Resposta ISSNet HTTP %s, preview: %s',
                    r.status_code,
                    (r.text or '')[:500],
                )
                if r.status_code >= 400 or 'Fault' in (r.text or ''):
                    logger.error('ISSNet resposta (ate 8000 chars): %s', (r.text or '')[:8000])

                if r.status_code in (502, 503, 504) and not _issnet_corpo_parece_xml(r.text or ''):
                    logger.warning(
                        'ISSNet HTTP %s sem XML; repetindo POST uma vez apos 2s',
                        r.status_code,
                    )
                    time.sleep(2.0)
                    r = _do_post(soap_try, headers_try)
                    logger.info(
                        'Resposta ISSNet HTTP %s (apos retry), preview: %s',
                        r.status_code,
                        (r.text or '')[:500],
                    )

                # ISSNet fora do ar (texto plano) — nao adianta trocar formato do envelope.
                if r.status_code in (502, 503, 504) and not _issnet_corpo_parece_xml(r.text or ''):
                    msg = _issnet_decodificar_corpo(r).strip() or '(sem corpo)'
                    msg = ' '.join(msg.split())
                    return (
                        {
                            'success': False,
                            'error': (
                                f'Servico ISSNet indisponivel (HTTP {r.status_code}). '
                                f'Tente novamente em instantes. {msg[:400]}'
                            ),
                        },
                        '',
                    )

                # Para ConsultarNfsePorRps: se o ISSNet responder E160 (schema),
                # tentar o próximo formato de envelope ao invés de parar na 1ª resposta.
                if (
                    nome_operacao == 'ConsultarNfsePorRps'
                    and strat_idx < len(strategies) - 1
                    and re.search(r'<\s*Codigo\s*>\s*E160\s*<\s*/\s*Codigo\s*>', (r.text or ''), re.I)
                ):
                    logger.warning(
                        'ISSNet %s retornou E160 (schema) com %r; tentando formato alternativo',
                        nome_operacao,
                        label,
                    )
                    continue

                if not (
                    _issnet_corpo_parece_xml(r.text or '')
                    and _issnet_fault_soap_generico(r.text or '')
                ):
                    break
                if strat_idx >= len(strategies) - 1:
                    break
                logger.warning(
                    'ISSNet Fault generico com estrategia %r; tentando formato alternativo',
                    label,
                )

            if not _issnet_corpo_parece_xml(r.text or ''):
                msg = _issnet_decodificar_corpo(r).strip() or '(resposta vazia)'
                msg = ' '.join(msg.split())
                return (
                    {
                        'success': False,
                        'error': (
                            f'O webservice ISSNet respondeu HTTP {r.status_code} sem XML '
                            f'(serviço indisponível ou erro no balanceador). {msg[:600]}'
                        ),
                    },
                    '',
                )

            xml_body = self._extrair_body_soap(r.text)
            return self._parse_resposta_xml(xml_body), xml_body
        except Exception as e:
            logger.exception('Erro ao enviar SOAP: %s', e)
            return {'success': False, 'error': str(e)}, ''
        finally:
            for p in (cert_path, key_path):
                if p and os.path.isfile(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

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
