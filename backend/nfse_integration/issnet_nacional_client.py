"""
Cliente ISSNet Nacional (WebService Municipal no padrão Nacional NFS-e).

Endpoint: https://nfse.issnetonline.com.br/wsnfsenacional/homologacao/nfse.asmx
WSDL: mesmo endpoint + ?wsdl (requer mTLS)

Operações:
- GerarNfse (síncrono, 1 DPS)
- RecepcionarLoteDpsSincrono (síncrono, lote)
- ConsultarNfseDps
- CancelarNfse

Formato: SOAP 1.1 com nfseCabecMsg + nfseDadosMsg (xsd:string).
O XML da DPS é o mesmo padrão nacional (namespace http://www.sped.fazenda.gov.br/nfse).
"""
import logging
import os
import re
import tempfile
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional
from xml.sax.saxutils import escape as xml_escape

from lxml import etree

logger = logging.getLogger(__name__)

# URLs
ISSNET_NACIONAL_URLS = {
    'homologacao': 'https://nfse.issnetonline.com.br/wsnfsenacional/homologacao/nfse.asmx',
    'producao': 'https://nfse.issnetonline.com.br/wsnfsenacional/ribeiraopreto/nfse.asmx',
}

NS_NFSE = 'http://www.sped.fazenda.gov.br/nfse'
NS_SOAP = 'http://schemas.xmlsoap.org/soap/envelope/'

# Cabeçalho padrão nacional - versão 1.01 conforme ISSNet Nacional
CABEC_MSG = (
    '<cabecalho versao="1.01" xmlns="http://www.sped.fazenda.gov.br/nfse">'
    '<versaoDados>1.01</versaoDados>'
    '</cabecalho>'
)


def _preparar_cert_mtls(pfx_bytes: bytes, senha_pfx: str):
    """Extrai cert e key PEM do PFX para mTLS."""
    from cryptography.hazmat.primitives.serialization import (
        pkcs12, Encoding, PrivateFormat, NoEncryption,
    )

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_bytes, senha_pfx.encode()
    )
    if not private_key or not certificate:
        raise ValueError('Certificado .pfx inválido')

    key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    cert_pem = certificate.public_bytes(Encoding.PEM)

    cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem', prefix='issnet_cert_')
    cert_tmp.write(cert_pem)
    cert_tmp.close()

    key_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem', prefix='issnet_key_')
    key_tmp.write(key_pem)
    key_tmp.close()

    return cert_tmp.name, key_tmp.name


def _limpar_temp(cert_path, key_path):
    """Remove arquivos temporários PEM."""
    for path in (cert_path, key_path):
        if path:
            try:
                if os.path.isfile(path) and path.startswith(tempfile.gettempdir()):
                    os.unlink(path)
            except OSError:
                pass


def _montar_soap_envelope(operacao: str, cabec_msg: str, dados_msg: str) -> str:
    """Monta envelope SOAP 1.1 para o ISSNet Nacional.
    Tenta formato com entidades XML (padrão xsd:string do ASMX).
    """
    cabec_escaped = xml_escape(cabec_msg)
    dados_escaped = xml_escape(dados_msg)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ws="http://www.sped.fazenda.gov.br/nfse">'
        '<soapenv:Body>'
        f'<ws:{operacao}>'
        f'<ws:nfseCabecMsg>{cabec_escaped}</ws:nfseCabecMsg>'
        f'<ws:nfseDadosMsg>{dados_escaped}</ws:nfseDadosMsg>'
        f'</ws:{operacao}>'
        '</soapenv:Body>'
        '</soapenv:Envelope>'
    )


def _parse_soap_response(response_text: str) -> str:
    """Extrai conteúdo da resposta SOAP (GerarNfseResposta ou outputXML)."""
    try:
        root = etree.fromstring(response_text.encode('utf-8'))
        # Buscar GerarNfseResposta (resposta específica do ISSNet Nacional)
        for el in root.iter():
            local = etree.QName(el.tag).localname
            if local in ('GerarNfseResposta', 'RecepcionarLoteDpsSincronoResposta'):
                return etree.tostring(el, encoding='unicode')
            if local == 'outputXML':
                return el.text or ''
        # Fallback: retornar Body inteiro
        body = root.find(f'.//{{{NS_SOAP}}}Body')
        if body is not None and len(body) > 0:
            return etree.tostring(body[0], encoding='unicode')
    except Exception as e:
        logger.warning('Erro ao parsear resposta SOAP: %s', e)
    return response_text


class ISSNetNacionalClient:
    """
    Cliente para emissão de NFS-e via WebService ISSNet no padrão Nacional.
    Usa o mesmo XML DPS do padrão nacional, enviado via SOAP com mTLS.
    """

    def __init__(
        self,
        pfx_bytes: bytes,
        senha_pfx: str,
        ambiente: str = 'homologacao',
    ):
        self.pfx_bytes = pfx_bytes
        self.senha_pfx = senha_pfx
        self.ambiente = 'homologacao' if ambiente == 'homologacao' else 'producao'
        self.base_url = ISSNET_NACIONAL_URLS.get(self.ambiente, ISSNET_NACIONAL_URLS['homologacao'])

    def _soap_request(self, operacao: str, dados_xml: str) -> Dict[str, Any]:
        """Faz request SOAP com mTLS."""
        import requests

        cert_path = None
        key_path = None

        try:
            cert_path, key_path = _preparar_cert_mtls(self.pfx_bytes, self.senha_pfx)

            envelope = _montar_soap_envelope(operacao, CABEC_MSG, dados_xml)
            soap_action = f'{NS_NFSE}/{operacao}'

            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': soap_action,
                'User-Agent': 'LWK-Sistemas/1.0 (ISSNet Nacional)',
            }

            logger.info(
                'ISSNet Nacional SOAP: operacao=%s, url=%s, soap_action=%s',
                operacao, self.base_url, soap_action,
            )
            logger.debug('ISSNet Nacional: envelope (primeiros 500): %s', envelope[:500])

            response = requests.post(
                self.base_url,
                data=envelope.encode('utf-8'),
                headers=headers,
                cert=(cert_path, key_path),
                timeout=30,
                verify=True,
            )

            logger.info('ISSNet Nacional: HTTP %d, content_length=%s', response.status_code, len(response.text))

            if response.status_code == 200:
                output_xml = _parse_soap_response(response.text)
                return {
                    'success': True,
                    'status_code': 200,
                    'output_xml': output_xml,
                    'raw_response': response.text[:5000],
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}: {response.reason}',
                    'raw_response': response.text[:3000],
                }

        except requests.exceptions.SSLError as e:
            logger.error('ISSNet Nacional: erro SSL/mTLS: %s', e)
            return {'success': False, 'error': f'Erro certificado (mTLS): {e}'}
        except Exception as e:
            logger.exception('ISSNet Nacional: erro inesperado: %s', e)
            return {'success': False, 'error': str(e)}
        finally:
            _limpar_temp(cert_path, key_path)

    def emitir_nfse(
        self,
        xml_dps_assinado: str,
    ) -> Dict[str, Any]:
        """
        Emite NFS-e via GerarNfse (síncrono, 1 DPS).
        
        Args:
            xml_dps_assinado: XML da DPS já assinado digitalmente
            
        Returns:
            Dict com success, numero_nf, codigo_verificacao, xml_nfse, error
        """
        result = {
            'success': False,
            'numero_nf': '',
            'codigo_verificacao': '',
            'xml_nfse': '',
            'error': None,
            'raw_response': '',
        }

        try:
            # Envelopar DPS para envio
            # Remover <?xml ...?> declaration se presente
            dps_xml = xml_dps_assinado
            if dps_xml.startswith('<?xml'):
                dps_xml = dps_xml[dps_xml.index('?>') + 2:].strip()

            # Enviar DPS diretamente como nfseDadosMsg (sem envelope GerarNfseEnvio)
            dados_msg = dps_xml

            resposta = self._soap_request('GerarNfse', dados_msg)
            result['raw_response'] = resposta.get('raw_response', '')

            if not resposta.get('success'):
                result['error'] = resposta.get('error', 'Erro na comunicação SOAP')
                return result

            output_xml = resposta.get('output_xml', '')
            if not output_xml:
                result['error'] = 'Resposta vazia do ISSNet'
                return result

            # Parse da resposta
            return self._parse_resposta_nfse(output_xml, result)

        except Exception as e:
            logger.exception('ISSNet Nacional emitir_nfse erro: %s', e)
            result['error'] = str(e)
            return result

    def _parse_resposta_nfse(self, output_xml: str, result: Dict) -> Dict[str, Any]:
        """Parse da resposta XML do ISSNet Nacional."""
        try:
            # O output pode ser XML escapado ou direto
            xml_to_parse = output_xml
            if xml_to_parse.startswith('&lt;') or '&lt;' in xml_to_parse[:50]:
                from html import unescape
                xml_to_parse = unescape(xml_to_parse)

            root = etree.fromstring(xml_to_parse.encode('utf-8') if isinstance(xml_to_parse, str) else xml_to_parse)

            # Buscar erros (ListaMensagemRetorno / MensagemRetorno)
            erros = []
            for el in root.iter():
                local = etree.QName(el.tag).localname
                if local == 'MensagemRetorno':
                    codigo = ''
                    descricao = ''
                    correcao = ''
                    for child in el:
                        child_local = etree.QName(child.tag).localname
                        if child_local == 'Codigo':
                            codigo = child.text or ''
                        elif child_local == 'Mensagem':
                            descricao = child.text or ''
                        elif child_local == 'Correcao':
                            correcao = child.text or ''
                    msg = f'[{codigo}] {descricao}'
                    if correcao:
                        msg += f' ({correcao})'
                    erros.append(msg)

            if erros:
                result['error'] = '; '.join(erros)
                return result

            # Buscar número da NFS-e (sucesso)
            numero_nf = ''
            codigo_verificacao = ''
            for el in root.iter():
                local = etree.QName(el.tag).localname
                if local == 'nNFSe' and not numero_nf:
                    numero_nf = el.text or ''
                elif local == 'cVerif' and not codigo_verificacao:
                    codigo_verificacao = el.text or ''
                elif local == 'CodigoVerificacao' and not codigo_verificacao:
                    codigo_verificacao = el.text or ''
                elif local == 'nDFSe' and not numero_nf:
                    numero_nf = el.text or ''

            if numero_nf:
                result['success'] = True
                result['numero_nf'] = numero_nf
                result['codigo_verificacao'] = codigo_verificacao
                result['xml_nfse'] = xml_to_parse
            else:
                result['error'] = 'Resposta sem número de NFS-e e sem erros explícitos'

        except etree.XMLSyntaxError as e:
            logger.warning('ISSNet Nacional: resposta não é XML válido: %s', e)
            result['error'] = f'Resposta inválida: {output_xml[:500]}'

        return result

    def validar_xml(self, xml_dps: str) -> Dict[str, Any]:
        """Valida XML da DPS sem emitir (operação ValidarXml)."""
        return self._soap_request('ValidarXml', xml_dps)

    def testar_conexao(self) -> Dict[str, Any]:
        """Testa conexão mTLS com o WebService."""
        import requests

        cert_path = None
        key_path = None
        try:
            cert_path, key_path = _preparar_cert_mtls(self.pfx_bytes, self.senha_pfx)
            r = requests.get(
                f'{self.base_url}?wsdl',
                cert=(cert_path, key_path),
                timeout=15,
            )
            if r.status_code == 200 and 'wsdl' in r.text[:500].lower():
                return {
                    'success': True,
                    'message': f'Conexão mTLS OK. WSDL acessível ({self.ambiente}). Endpoint: {self.base_url}',
                }
            return {
                'success': False,
                'detail': f'HTTP {r.status_code} ao acessar WSDL',
            }
        except Exception as e:
            return {'success': False, 'detail': str(e)}
        finally:
            _limpar_temp(cert_path, key_path)
