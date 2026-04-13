"""
Cliente para webservice ISSNet de Ribeirão Preto
Emissão de NFS-e direta na prefeitura — padrão ABRASF 2.04

Referências:
- WSDL: https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx?wsdl
- Operações: GerarNfse, RecepcionarLoteRpsSincrono, ConsultarNfsePorRps, CancelarNfse
- Cada operação SOAP recebe (nfseCabecMsg: str, nfseDadosMsg: str)
"""
import logging
import os
import re
import time
from datetime import datetime
from xml.sax.saxutils import escape as _xml_escape
from typing import Dict, Any, Optional
from decimal import Decimal

from lxml import etree

logger = logging.getLogger(__name__)

NS_NFSE = 'http://www.abrasf.org.br/nfse.xsd'
COD_MUNICIPIO_RP = '3543402'

ISSNET_RP_NFSE_ASMX = (
    'https://nfse.issnetonline.com.br/abrasf204/ribeiraopreto/nfse.asmx'
)
# Soap.php usa o 2o argumento de send() como SOAPAction (URL completa), nao o nome curto da operacao.
SOAP_ACTION_RECEPCIONAR_LOTE_RPS = 'http://nfse.abrasf.org.br/RecepcionarLoteRps'
ISSNET_URLS = {
    'producao': ISSNET_RP_NFSE_ASMX,
    'homologacao': ISSNET_RP_NFSE_ASMX,
}

CABEC_MSG = (
    '<cabecalho xmlns="http://www.abrasf.org.br/nfse.xsd" versao="2.04">'
    '<versaoDados>2.04</versaoDados>'
    '</cabecalho>'
)


def _somente_digitos(texto: str) -> str:
    return re.sub(r'\D', '', texto or '')


def _soap_xsd_string_payload(payload: str) -> str:
    """
    nfseCabecMsg / nfseDadosMsg são xsd:string: o XML deve ir como *texto* do elemento,
    não como filhos do envelope. Usamos entidades XML (&lt; etc.), padrão compatível com
    ASMX/.NET (equivalente ao que clientes SOAP costumam serializar).
    """
    return _xml_escape(payload or '', {'"': '&quot;', "'": '&apos;'})


def _issnet_corpo_parece_xml(texto: str) -> bool:
    if not (texto or '').strip():
        return False
    return texto.lstrip().startswith('<')


def _issnet_decodificar_corpo(resposta) -> str:
    """Decodifica bytes da resposta HTTP para mensagens de erro legíveis (UTF-8 / Latin-1)."""
    raw = getattr(resposta, 'content', None) or b''
    if not raw:
        return (getattr(resposta, 'text', None) or '').strip()
    for enc in ('utf-8', 'utf-8-sig', 'iso-8859-1', 'windows-1252'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='replace')


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
        else:
            out['detail'] = f'WSDL retornou HTTP {r.status_code}.'
    except Exception as e:
        logger.warning('testar_conexao_issnet: request WSDL: %s', e)
        out['detail'] = f'Nao foi possivel contatar o ISSNet: {e}'
    return out


class ISSNetClient:
    """
    Cliente SOAP para webservice ISSNet Ribeirao Preto (ABRASF 2.04).

    Usa GerarNfse (sincrono, 1 RPS) em vez de RecepcionarLoteRps (assincrono).
    Autenticacao: usuario/senha no XML + certificado digital para assinatura.
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

    # ------------------------------------------------------------------
    # Assinatura XML
    # ------------------------------------------------------------------
    def _assinar_xml(self, xml_str: str) -> str:
        """
        Assina XML com certificado digital A1 usando python-xmlsec.

        Dupla assinatura alinhada ao sped-nfse-issnet (PHP): primeiro o ``Rps``
        externo (ListaRps/Rps) com Reference URI vazia e so transform enveloped;
        depois ``EnviarLoteRpsEnvio`` com atributo Id e mesma politica de Reference.
        A Signature fica dentro do no assinado (como no Signer do pacote ISSNET).
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

        # Cancelamento ABRASF: um unico Signer no elemento Pedido (Id), como no sped-nfse-issnet
        if root_local == 'CancelarNfseEnvio':
            pedido = root.find('{%s}Pedido' % ns)
            if pedido is not None:
                pedido_id = (pedido.get('Id') or '').strip() or 'Pedido1'
                pedido.set('Id', pedido_id)
                sig_ped = _template_sig_enveloped_only(pedido, f'#{pedido_id}')
                ctx_c = xmlsec.SignatureContext()
                ctx_c.key = key
                ctx_c.register_id(pedido, 'Id', None)
                ctx_c.sign(sig_ped)
            result = etree.tostring(root, encoding='unicode')
            logger.info('XML assinado com xmlsec (cancelamento Pedido)')
            return result

        lista = root.find('.//{%s}ListaRps' % ns)
        outer_rps = lista.find('{%s}Rps' % ns) if lista is not None else None
        lote_el = root.find('.//{%s}LoteRps' % ns)

        if outer_rps is None:
            logger.warning('Assinatura: ListaRps/Rps externo nao encontrado; XML nao assinado.')
        else:
            sig_rps = _template_sig_enveloped_only(outer_rps, '')
            ctx = xmlsec.SignatureContext()
            ctx.key = key
            ctx.sign(sig_rps)

        if root_local != 'EnviarLoteRpsEnvio':
            logger.warning('Assinatura: raiz inesperada %s; pulando segunda assinatura.', root_local)
        else:
            num_lote = ''
            if lote_el is not None:
                num_lote = (lote_el.findtext('{%s}NumeroLote' % ns) or '').strip()
            if not num_lote:
                num_lote = '1'
            envio_id = root.get('Id') or f'EnviarLoteRpsEnvio{num_lote}'
            root.set('Id', envio_id)

            sig_envio = _template_sig_enveloped_only(root, f'#{envio_id}')
            ctx2 = xmlsec.SignatureContext()
            ctx2.key = key
            ctx2.register_id(root, 'Id', None)
            ctx2.sign(sig_envio)

        result = etree.tostring(root, encoding='unicode')
        logger.info('XML assinado com xmlsec (RSA-SHA1, dupla assinatura ISSNET)')
        return result

    # Metodo antigo mantido como referencia
    # ------------------------------------------------------------------
    # Construir XML ABRASF 2.04 — EnviarLoteRpsEnvio (ISSNet RP)
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
    ) -> str:
        """
        Constroi XML EnviarLoteRpsEnvio no padrao ABRASF 2.04 (ISSNet RP).
        Baseado na lib PHP Focus599Dev/sped-nfse-issnet que funciona.
        """
        cnpj_prest = _somente_digitos(prestador_cnpj)
        doc_tomador = _somente_digitos(tomador_cpf_cnpj)

        valor = Decimal(str(valor_servicos))
        aliquota = Decimal(str(aliquota_iss))
        valor_iss = (valor * aliquota / 100).quantize(Decimal('0.01'))

        ns = NS_NFSE
        # Root: EnviarLoteRpsEnvio
        root = etree.Element('{%s}EnviarLoteRpsEnvio' % ns, nsmap={None: ns})

        # LoteRps com versao
        lote = etree.SubElement(root, '{%s}LoteRps' % ns, versao='2.04')
        etree.SubElement(lote, '{%s}NumeroLote' % ns).text = str(numero_rps)

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
        etree.SubElement(rps_inner, '{%s}DataEmissao' % ns).text = (
            data_emissao.strftime('%Y-%m-%dT%H:%M:%S')
        )
        etree.SubElement(rps_inner, '{%s}Status' % ns).text = '1'

        # --- Competencia ---
        etree.SubElement(inf, '{%s}Competencia' % ns).text = (
            data_emissao.strftime('%Y-%m-%d')
        )

        # --- Servico ---
        servico = etree.SubElement(inf, '{%s}Servico' % ns)

        # Valores (ordem conforme schema ISSNet)
        valores = etree.SubElement(servico, '{%s}Valores' % ns)
        etree.SubElement(valores, '{%s}ValorServicos' % ns).text = f'{valor:.2f}'
        etree.SubElement(valores, '{%s}ValorDeducoes' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}ValorIss' % ns).text = f'{valor_iss:.2f}'
        etree.SubElement(valores, '{%s}Aliquota' % ns).text = f'{aliquota:.2f}'
        etree.SubElement(valores, '{%s}DescontoIncondicionado' % ns).text = '0.00'
        etree.SubElement(valores, '{%s}DescontoCondicionado' % ns).text = '0.00'

        etree.SubElement(servico, '{%s}IssRetido' % ns).text = '2'
        item_lista = servico_codigo or ''
        etree.SubElement(servico, '{%s}ItemListaServico' % ns).text = item_lista
        etree.SubElement(servico, '{%s}CodigoTributacaoMunicipio' % ns).text = item_lista
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

        end = etree.SubElement(tomador, '{%s}Endereco' % ns)
        etree.SubElement(end, '{%s}Endereco' % ns).text = (
            tomador_endereco.get('logradouro', '')
        )
        etree.SubElement(end, '{%s}Numero' % ns).text = (
            tomador_endereco.get('numero', 'S/N')
        )
        bairro = tomador_endereco.get('bairro', '')
        if bairro:
            etree.SubElement(end, '{%s}Bairro' % ns).text = bairro
        etree.SubElement(end, '{%s}CodigoMunicipio' % ns).text = COD_MUNICIPIO_RP
        etree.SubElement(end, '{%s}Uf' % ns).text = (
            tomador_endereco.get('uf', 'SP')
        )
        cep = _somente_digitos(tomador_endereco.get('cep', ''))
        if cep:
            etree.SubElement(end, '{%s}Cep' % ns).text = cep

        # --- Flags ---
        regime = getattr(self, '_regime_especial', '0') or ''
        if regime and regime != '0':
            etree.SubElement(inf, '{%s}RegimeEspecialTributacao' % ns).text = regime
        optante = '1' if self._optante_simples else '2'
        etree.SubElement(inf, '{%s}OptanteSimplesNacional' % ns).text = optante
        incentivo = '1' if self._incentivador_cultural else '2'
        etree.SubElement(inf, '{%s}IncentivoFiscal' % ns).text = incentivo

        xml_str = etree.tostring(root, encoding='unicode', pretty_print=True)
        logger.info('XML EnviarLoteRps construido: RPS %s, Valor R$ %s', numero_rps, valor)
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
    ) -> Dict[str, Any]:
        """Emite NFS-e via GerarNfse (sincrono, 1 RPS)."""
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
            )

            # Assinar XML (dupla: Rps + EnviarLoteRpsEnvio) e enviar
            xml_assinado = self._assinar_xml(xml_rps)
            resultado = self._enviar_soap_direto(xml_assinado)
            return resultado

        except Exception as e:
            logger.exception('Erro ao emitir NFS-e: %s', e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------
    # Enviar via requests direto (formato exato da lib PHP)
    # ------------------------------------------------------------------
    def _enviar_soap_direto(self, xml_dados: str) -> Dict[str, Any]:
        """Envia XML via SOAP 1.1 direto (sem zeep), mTLS + text/xml conforme WSDL ASMX."""
        import os
        import tempfile

        import requests as req

        cabec = (
            '<cabecalho versao="2.04" xmlns="http://www.abrasf.org.br/nfse.xsd">'
            '<versaoDados>2.04</versaoDados>'
            '</cabecalho>'
        )
        soap = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            'xmlns:nfse="http://nfse.abrasf.org.br">'
            '<soap:Header/>'
            '<soap:Body>'
            '<nfse:RecepcionarLoteRps>'
            '<nfseCabecMsg>' + _soap_xsd_string_payload(cabec) + '</nfseCabecMsg>'
            '<nfseDadosMsg>' + _soap_xsd_string_payload(xml_dados) + '</nfseDadosMsg>'
            '</nfse:RecepcionarLoteRps>'
            '</soap:Body>'
            '</soap:Envelope>'
        )
        # WSDL (nfseSOAP): soap:binding transport = http://schemas.xmlsoap.org/soap/http → SOAP 1.1.
        # ASMX/.NET espera Content-Type text/xml; application/soap+xml é SOAP 1.2 e costuma gerar Fault genérico.
        # SOAPAction deve coincidir com soap:operation no WSDL (URI entre aspas, HTTP/1.1).
        # Connection: close evita reuso de socket com servidores ASMX que fecham abruptamente.
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': f'"{SOAP_ACTION_RECEPCIONAR_LOTE_RPS}"',
            'Connection': 'close',
            'Accept': 'text/xml',
            'User-Agent': 'LWK-Sistemas/CRM (ISSNet ABRASF 2.04)',
        }

        cert_path = None
        key_path = None
        logger.info('Enviando SOAP direto ao ISSNet (%d bytes) com mTLS', len(soap))
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

            # (connect, read): Heroku encerra HTTP em ~30s (H12). Uma chamada ISSNet + assinatura
            # precisa ficar abaixo disso; não repetir POST em Fault SOAP (duplicaria tempo).
            http_timeout = (8, 20)
            try:
                r = req.post(
                    self.base_url,
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=http_timeout,
                    cert=(cert_path, key_path),
                )
            except (
                req.exceptions.ConnectionError,
                req.exceptions.ChunkedEncodingError,
                req.exceptions.ReadTimeout,
            ) as e:
                logger.warning('ISSNet SOAP POST: erro de conexao, uma nova tentativa: %s', e)
                time.sleep(1.5)
                r = req.post(
                    self.base_url,
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=http_timeout,
                    cert=(cert_path, key_path),
                )

            logger.info(
                'Resposta ISSNet HTTP %s, preview: %s',
                r.status_code,
                (r.text or '')[:500],
            )
            if r.status_code >= 400 or 'Fault' in (r.text or ''):
                logger.error('ISSNet resposta (ate 8000 chars): %s', (r.text or '')[:8000])

            # 502/503/504 costumam devolver HTML ou texto ("O serviço não está disponível"), não SOAP.
            if r.status_code in (502, 503, 504) and not _issnet_corpo_parece_xml(r.text or ''):
                logger.warning(
                    'ISSNet HTTP %s sem XML; repetindo POST uma vez apos 2s',
                    r.status_code,
                )
                time.sleep(2.0)
                r = req.post(
                    self.base_url,
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=http_timeout,
                    cert=(cert_path, key_path),
                )
                logger.info(
                    'Resposta ISSNet HTTP %s (apos retry), preview: %s',
                    r.status_code,
                    (r.text or '')[:500],
                )

            if not _issnet_corpo_parece_xml(r.text or ''):
                msg = _issnet_decodificar_corpo(r).strip() or '(resposta vazia)'
                msg = ' '.join(msg.split())
                return {
                    'success': False,
                    'error': (
                        f'O webservice ISSNet respondeu HTTP {r.status_code} sem XML '
                        f'(serviço indisponível ou erro no balanceador). {msg[:600]}'
                    ),
                }

            xml_body = self._extrair_body_soap(r.text)
            return self._parse_resposta_xml(xml_body)
        except Exception as e:
            logger.exception('Erro ao enviar SOAP: %s', e)
            return {'success': False, 'error': str(e)}
        finally:
            for p in (cert_path, key_path):
                if p and os.path.isfile(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass

    # ------------------------------------------------------------------
    # Enviar via zeep (mantido como fallback)
    # ------------------------------------------------------------------
    def _enviar_gerar_nfse(self, xml_assinado: str) -> Dict[str, Any]:
        """
        Chama operacao RecepcionarLoteRpsSincrono do webservice ISSNet.
        Sincrono: retorna a NFS-e na mesma chamada (melhor para 1 RPS).
        """
        try:
            client = self._get_soap_client()
            logger.info('XML enviado ao ISSNet (nfseDadosMsg): %s', xml_assinado[:2000])
            with client.settings(raw_response=True):
                response = client.service.RecepcionarLoteRpsSincrono(
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
        """Extrai conteudo do SOAP Body da resposta."""
        try:
            root = etree.fromstring(soap_xml.encode('utf-8') if isinstance(soap_xml, str) else soap_xml)
            # Buscar Body em qualquer namespace SOAP
            body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
            if body is None:
                body = root.find('.//{http://www.w3.org/2003/05/soap-envelope}Body')
            if body is not None and len(body) > 0:
                first = body[0]
                # Verificar se eh SOAP Fault
                tag = etree.QName(first.tag).localname if isinstance(first.tag, str) else ''
                if tag == 'Fault':
                    faultstring = first.findtext(
                        '{http://schemas.xmlsoap.org/soap/envelope/}faultstring', ''
                    ) or first.findtext('faultstring', '')
                    detail = first.findtext(
                        '{http://schemas.xmlsoap.org/soap/envelope/}detail', ''
                    ) or first.findtext('detail', '')
                    msg = faultstring or 'Erro SOAP desconhecido'
                    if (msg or '').strip().lower() == 'error':
                        msg = (
                            'Erro genérico do webservice ISSNet (sem detail). '
                            'Verifique certificado mTLS, cadastro na prefeitura e XML (RPS/assinatura).'
                        )
                    if detail:
                        msg += f' - {detail}'
                    # Retornar XML de erro formatado para o parser
                    ns = NS_NFSE
                    return (
                        f'<ListaMensagemRetorno xmlns="{ns}">'
                        f'<MensagemRetorno>'
                        f'<Codigo>SOAP</Codigo>'
                        f'<Mensagem>{msg}</Mensagem>'
                        f'</MensagemRetorno>'
                        f'</ListaMensagemRetorno>'
                    )
                return etree.tostring(first, encoding='unicode')
            return soap_xml
        except Exception:
            return soap_xml

    def _parse_resposta_xml(self, xml_str: str) -> Dict[str, Any]:
        """Parse da resposta XML do ISSNet para extrair NFS-e ou erros."""
        try:
            root = etree.fromstring(xml_str.encode('utf-8') if isinstance(xml_str, str) else xml_str)
        except etree.XMLSyntaxError:
            amostra = (xml_str or '')[:400].strip()
            amostra = ' '.join(amostra.split())
            if amostra and not amostra.startswith('<'):
                return {
                    'success': False,
                    'error': (
                        'Resposta do ISSNet não é XML válido (provável indisponibilidade do serviço). '
                        f'{amostra}'
                    ),
                }
            return {'success': False, 'error': f'XML inválido na resposta do ISSNet: {amostra}'}

        nsmap = {'ns': NS_NFSE}

        # Verificar erros
        msgs = root.findall('.//ns:MensagemRetorno', nsmap)
        if msgs:
            erros = []
            for msg in msgs:
                codigo = msg.findtext('ns:Codigo', '', nsmap)
                mensagem = msg.findtext('ns:Mensagem', '', nsmap)
                correcao = msg.findtext('ns:Correcao', '', nsmap)
                texto = f'[{codigo}] {mensagem}'
                if correcao:
                    texto += f' - {correcao}'
                erros.append(texto)
            return {'success': False, 'error': '; '.join(erros)}

        # Extrair dados da NFS-e gerada
        nfse_el = root.find('.//ns:CompNfse/ns:Nfse/ns:InfNfse', nsmap)
        if nfse_el is None:
            nfse_el = root.find('.//ns:Nfse/ns:InfNfse', nsmap)
        if nfse_el is None:
            nfse_el = root.find('.//{%s}InfNfse' % NS_NFSE)

        if nfse_el is not None:
            numero = nfse_el.findtext('{%s}Numero' % NS_NFSE, '')
            cod_ver = nfse_el.findtext('{%s}CodigoVerificacao' % NS_NFSE, '')
            dt_text = nfse_el.findtext('{%s}DataEmissao' % NS_NFSE, '')
            dt_emissao = datetime.now()
            if dt_text:
                try:
                    dt_emissao = datetime.fromisoformat(dt_text.replace('Z', '+00:00'))
                except Exception:
                    pass

            return {
                'success': True,
                'numero_nf': numero,
                'codigo_verificacao': cod_ver,
                'data_emissao': dt_emissao,
                'xml_nfse': xml_str,
            }

        return {
            'success': False,
            'error': f'NFS-e nao encontrada na resposta: {xml_str[:500]}'
        }

    def _extrair_erros(self, texto: str) -> str:
        """Extrai mensagens de erro de texto/XML."""
        erros = re.findall(r'<Mensagem>(.*?)</Mensagem>', texto)
        return '; '.join(erros) if erros else texto[:500]

    # ------------------------------------------------------------------
    # Consultar NFS-e por RPS
    # ------------------------------------------------------------------
    def consultar_nfse(self, numero_nf: str) -> Dict[str, Any]:
        """Consulta NFS-e emitida por numero."""
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

    # ------------------------------------------------------------------
    # Cancelar NFS-e
    # ------------------------------------------------------------------
    def cancelar_nfse(self, numero_nf: str, motivo: str) -> Dict[str, Any]:
        """Cancela NFS-e emitida."""
        try:
            xml_cancelar = (
                f'<CancelarNfseEnvio xmlns="{NS_NFSE}">'
                f'<Pedido>'
                f'<InfPedidoCancelamento Id="cancel{numero_nf}">'
                f'<IdentificacaoNfse>'
                f'<Numero>{numero_nf}</Numero>'
                f'<CpfCnpj><Cnpj>{self.usuario}</Cnpj></CpfCnpj>'
                f'<InscricaoMunicipal></InscricaoMunicipal>'
                f'<CodigoMunicipio>{COD_MUNICIPIO_RP}</CodigoMunicipio>'
                f'</IdentificacaoNfse>'
                f'<CodigoCancelamento>1</CodigoCancelamento>'
                f'</InfPedidoCancelamento>'
                f'</Pedido>'
                f'</CancelarNfseEnvio>'
            )
            xml_assinado = self._assinar_xml(xml_cancelar)
            client = self._get_soap_client()
            response = client.service.CancelarNfse(
                nfseCabecMsg=CABEC_MSG,
                nfseDadosMsg=xml_assinado,
            )
            resp_str = str(response)
            if 'MensagemRetorno' in resp_str:
                erros = self._extrair_erros(resp_str)
                return {'success': False, 'error': erros}
            return {'success': True, 'message': 'NFS-e cancelada com sucesso'}
        except Exception as e:
            logger.exception('Erro ao cancelar NFS-e: %s', e)
            return {'success': False, 'error': str(e)}
