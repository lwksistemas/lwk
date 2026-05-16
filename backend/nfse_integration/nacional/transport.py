"""
Camada de transporte para NFS-e Nacional (ADN).

Responsabilidades:
- Compressão GZip do XML
- Codificação Base64
- Envio HTTP com mTLS (certificado cliente)
- Parse da resposta JSON
"""
import base64
import gzip
import logging
import os
import tempfile
from typing import Dict, Any, Optional

import requests

from .constants import ADN_URLS

logger = logging.getLogger(__name__)

# Timeout padrão para requisições ao ADN (segundos)
DEFAULT_TIMEOUT = 30


def comprimir_e_codificar(xml_str: str) -> str:
    """
    Comprime XML com GZip e codifica em Base64.
    
    Padrão ADN: GZip com representação base64binary.
    
    Args:
        xml_str: XML assinado como string UTF-8
        
    Returns:
        String Base64 do XML comprimido
    """
    xml_bytes = xml_str.encode('utf-8')
    compressed = gzip.compress(xml_bytes)
    b64 = base64.b64encode(compressed).decode('ascii')
    logger.debug(
        'XML comprimido: %d bytes -> %d bytes GZip -> %d chars Base64',
        len(xml_bytes), len(compressed), len(b64),
    )
    return b64


def descomprimir_e_decodificar(b64_str: str) -> str:
    """
    Decodifica Base64 e descomprime GZip.
    
    Args:
        b64_str: String Base64 do XML comprimido
        
    Returns:
        XML como string UTF-8
    """
    compressed = base64.b64decode(b64_str)
    xml_bytes = gzip.decompress(compressed)
    return xml_bytes.decode('utf-8')


def enviar_lote_dfe(
    lote_xml_b64: list,
    ambiente: str = 'producao',
    pfx_path: Optional[str] = None,
    pfx_bytes: Optional[bytes] = None,
    senha_pfx: str = '',
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Envia lote de DPS ao ADN via POST /DFe com mTLS.
    
    O request body é JSON:
    {
        "LoteXmlGZipB64": ["<xml_gzip_b64_1>", "<xml_gzip_b64_2>", ...]
    }
    
    Args:
        lote_xml_b64: Lista de strings Base64 (cada uma é um XML DPS comprimido)
        ambiente: 'producao' ou 'homologacao'
        pfx_path: Caminho para o .pfx (mTLS)
        pfx_bytes: Bytes do .pfx (alternativa ao path)
        senha_pfx: Senha do certificado
        timeout: Timeout em segundos
        
    Returns:
        Dict com a resposta do ADN (RecepcaoResponseLote)
    """
    url = ADN_URLS.get(ambiente, ADN_URLS['homologacao'])
    cert_path = None
    key_path = None

    try:
        # Preparar certificado para mTLS
        cert_path, key_path = _preparar_cert_mtls(pfx_path, pfx_bytes, senha_pfx)

        # Payload JSON
        payload = {
            'LoteXmlGZipB64': lote_xml_b64,
        }

        # Headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'LWK-Sistemas/1.0 (NFS-e Nacional)',
        }

        logger.info(
            'Enviando lote DFe ao ADN: url=%s, ambiente=%s, qtd_docs=%d',
            url, ambiente, len(lote_xml_b64),
        )

        # Request com mTLS
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            cert=(cert_path, key_path),
            timeout=timeout,
            verify=True,
        )

        logger.info(
            'Resposta ADN: status=%d, content_length=%s',
            response.status_code, response.headers.get('content-length', '?'),
        )

        # Parse resposta
        if response.status_code in (200, 201):
            data = response.json()
            return {
                'success': True,
                'status_code': response.status_code,
                'data': data,
            }
        elif response.status_code == 400:
            try:
                data = response.json()
            except Exception:
                data = {'raw': response.text[:2000]}
            return {
                'success': False,
                'status_code': response.status_code,
                'error': 'Requisição rejeitada pelo ADN',
                'data': data,
            }
        else:
            return {
                'success': False,
                'status_code': response.status_code,
                'error': f'HTTP {response.status_code}: {response.reason}',
                'data': {'raw': response.text[:2000]},
            }

    except requests.exceptions.SSLError as e:
        logger.error('Erro SSL/mTLS ao conectar ao ADN: %s', e)
        return {
            'success': False,
            'error': f'Erro de certificado (mTLS): {e}',
            'data': None,
        }
    except requests.exceptions.ConnectionError as e:
        logger.error('Erro de conexão ao ADN: %s', e)
        return {
            'success': False,
            'error': f'Não foi possível conectar ao ADN: {e}',
            'data': None,
        }
    except requests.exceptions.Timeout:
        logger.error('Timeout ao conectar ao ADN (%ds)', timeout)
        return {
            'success': False,
            'error': f'Timeout ({timeout}s) ao conectar ao ADN',
            'data': None,
        }
    except Exception as e:
        logger.exception('Erro inesperado ao enviar DFe: %s', e)
        return {
            'success': False,
            'error': str(e),
            'data': None,
        }
    finally:
        # Limpar arquivos temporários
        _limpar_temp(cert_path, key_path, pfx_path)


def consultar_dfe_nsu(
    nsu: int,
    cnpj_consulta: str,
    ambiente: str = 'producao',
    pfx_path: Optional[str] = None,
    pfx_bytes: Optional[bytes] = None,
    senha_pfx: str = '',
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """
    Consulta documento fiscal por NSU (Número Sequencial Único).
    GET /DFe/{NSU}?cnpjConsulta={cnpj}
    
    Returns:
        Dict com resposta (LoteDistribuicaoNSUResponse)
    """
    base_url = ADN_URLS.get(ambiente, ADN_URLS['homologacao'])
    # A URL de consulta usa o endpoint de contribuintes, não o de recepção
    # Ajustar conforme ambiente
    url = f'{base_url}/{nsu}?cnpjConsulta={cnpj_consulta}'

    cert_path = None
    key_path = None

    try:
        cert_path, key_path = _preparar_cert_mtls(pfx_path, pfx_bytes, senha_pfx)

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'LWK-Sistemas/1.0 (NFS-e Nacional)',
        }

        response = requests.get(
            url,
            headers=headers,
            cert=(cert_path, key_path),
            timeout=timeout,
            verify=True,
        )

        if response.status_code == 200:
            return {
                'success': True,
                'status_code': 200,
                'data': response.json(),
            }
        else:
            return {
                'success': False,
                'status_code': response.status_code,
                'error': f'HTTP {response.status_code}',
                'data': response.text[:2000],
            }

    except Exception as e:
        logger.exception('Erro ao consultar DFe NSU %d: %s', nsu, e)
        return {'success': False, 'error': str(e), 'data': None}
    finally:
        _limpar_temp(cert_path, key_path, pfx_path)


def _preparar_cert_mtls(
    pfx_path: Optional[str],
    pfx_bytes: Optional[bytes],
    senha_pfx: str,
) -> tuple:
    """
    Prepara arquivos PEM (cert + key) para mTLS a partir do .pfx.
    
    Returns:
        Tuple (cert_pem_path, key_pem_path)
    """
    from cryptography.hazmat.primitives.serialization import (
        pkcs12, Encoding, PrivateFormat, NoEncryption,
    )

    # Carregar PFX
    if pfx_bytes:
        pfx_data = pfx_bytes
    elif pfx_path and os.path.isfile(pfx_path):
        with open(pfx_path, 'rb') as f:
            pfx_data = f.read()
    else:
        raise ValueError('Certificado .pfx não fornecido (nem path nem bytes)')

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data, senha_pfx.encode()
    )
    if not private_key or not certificate:
        raise ValueError('Certificado .pfx inválido ou sem chave privada')

    # Exportar para PEM temporário
    key_pem = private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    cert_pem = certificate.public_bytes(Encoding.PEM)

    cert_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem', prefix='nfse_cert_')
    cert_tmp.write(cert_pem)
    cert_tmp.close()

    key_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem', prefix='nfse_key_')
    key_tmp.write(key_pem)
    key_tmp.close()

    return cert_tmp.name, key_tmp.name


def _limpar_temp(cert_path: Optional[str], key_path: Optional[str], pfx_original: Optional[str]) -> None:
    """Remove arquivos temporários PEM (não remove o PFX original)."""
    for path in (cert_path, key_path):
        if path and path != pfx_original:
            try:
                if os.path.isfile(path) and path.startswith(tempfile.gettempdir()):
                    os.unlink(path)
            except OSError:
                pass
