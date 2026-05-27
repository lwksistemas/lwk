"""Helpers para obter a URL oficial da DANFE/NFS-e."""
import logging
import os
import re
import tempfile
from typing import Any

logger = logging.getLogger(__name__)

URL_INVALID_MARKERS = ('xmlsoap', 'w3.org', 'schemas.', 'abrasf')


def url_danfe_valida(url: str | None) -> bool:
    """Retorna True quando a URL parece ser do portal/PDF, nao de schema SOAP."""
    if not url or not str(url).startswith('http'):
        return False
    return not any(marker in str(url) for marker in URL_INVALID_MARKERS)


def _extrair_prestador_do_xml(xml_nfse: str) -> tuple[str, str]:
    cnpj = ''
    inscricao_municipal = ''

    if xml_nfse:
        cnpj_match = re.search(r'<Cnpj>(\d+)</Cnpj>', xml_nfse)
        im_match = re.search(r'<InscricaoMunicipal>(\d+)</InscricaoMunicipal>', xml_nfse)
        if cnpj_match:
            cnpj = cnpj_match.group(1)
        if im_match:
            inscricao_municipal = im_match.group(1)

    return cnpj, inscricao_municipal


def _salvar_pdf_url(nfse: Any, url: str) -> None:
    if not nfse or not url:
        return

    try:
        nfse.pdf_url = url[:1000]
        nfse.save(update_fields=['pdf_url'])
    except Exception as exc:
        logger.debug('Nao foi possivel salvar pdf_url da NFS-e id=%s: %s', getattr(nfse, 'id', None), exc)


def buscar_url_danfe_issnet(
    nfse: Any | None = None,
    *,
    numero_nf: str = '',
    loja_id: int | None = None,
    loja: Any | None = None,
    config: Any | None = None,
    salvar: bool = True,
) -> str:
    """
    Consulta o ISSNet para obter a URL oficial da DANFE.

    Pode receber uma instancia de NFSe ja persistida ou apenas numero/config
    para caminhos onde a nota acabou de ser emitida.
    """
    numero_nf = numero_nf or getattr(nfse, 'numero_nf', '')
    if not numero_nf:
        return ''

    if nfse and getattr(nfse, 'provedor', '') != 'issnet':
        return ''

    pdf_url = getattr(nfse, 'pdf_url', '') if nfse else ''
    if url_danfe_valida(pdf_url):
        return pdf_url

    try:
        if config is None:
            from crm_vendas.models_config import CRMConfig

            effective_loja_id = loja_id or getattr(nfse, 'loja_id', None)
            if not effective_loja_id:
                return ''
            config = CRMConfig.get_or_create_for_loja(effective_loja_id)

        cert_data = (
            getattr(config, 'issnet_certificado', None)
            or getattr(config, 'nacional_certificado', None)
        )
        if not cert_data:
            return ''

        senha_cert = (
            getattr(config, 'issnet_senha_certificado', '')
            or getattr(config, 'nacional_senha_certificado', '')
            or ''
        )
        usuario = getattr(config, 'issnet_usuario', '') or ''
        senha = getattr(config, 'issnet_senha', '') or ''
        ambiente = 'homologacao' if getattr(config, 'issnet_ambiente_homologacao', False) else 'producao'

        cnpj_prestador = getattr(config, 'cnpj_prestador', '') or ''
        if not cnpj_prestador and loja is not None:
            cnpj_prestador = re.sub(r'\D', '', getattr(loja, 'cpf_cnpj', '') or '')
        im_prestador = getattr(config, 'inscricao_municipal', '') or getattr(loja, 'inscricao_municipal', '') or ''

        xml_nfse = getattr(nfse, 'xml_nfse', '') if nfse else ''
        xml_cnpj, xml_im = _extrair_prestador_do_xml(xml_nfse)
        cnpj_prestador = xml_cnpj or cnpj_prestador
        im_prestador = xml_im or im_prestador

        cert_tmp = tempfile.NamedTemporaryFile(suffix='.pfx', delete=False)
        try:
            cert_tmp.write(bytes(cert_data))
            cert_tmp.close()

            from .issnet_client import ISSNetClient

            client = ISSNetClient(
                usuario=usuario,
                senha=senha,
                certificado_path=cert_tmp.name,
                senha_certificado=senha_cert,
                ambiente=ambiente,
            )
            resultado = client.consultar_url_nfse(
                numero_nf=numero_nf,
                prestador_cnpj=cnpj_prestador,
                inscricao_municipal=im_prestador,
            )
        finally:
            try:
                os.unlink(cert_tmp.name)
            except OSError:
                pass

        url = resultado.get('url') if resultado.get('success') else ''
        if not url_danfe_valida(url):
            return ''

        if salvar:
            _salvar_pdf_url(nfse, url)
        return url
    except Exception as exc:
        logger.warning('Erro ao buscar URL DANFE ISSNet: %s', exc)
        return ''


def buscar_url_danfe_issnet_superadmin(nfse: Any, config: Any | None = None, *, salvar: bool = True) -> str:
    """
    Consulta ISSNet usando configuracao global do superadmin (NFSeEmitida).
    """
    if not nfse or getattr(nfse, 'provedor', '') != 'issnet':
        return ''

    numero_nf = getattr(nfse, 'numero_nf', '') or ''
    if not numero_nf:
        return ''

    pdf_url = getattr(nfse, 'pdf_url', '') or ''
    if url_danfe_valida(pdf_url):
        return pdf_url

    try:
        if config is None:
            from asaas_integration.models_nfse_config import SuperadminNFSeConfig

            config = SuperadminNFSeConfig.get_config()

        cert_data = getattr(config, 'issnet_certificado', None) or getattr(config, 'nacional_certificado', None)
        if not cert_data:
            return ''

        senha_cert = (
            getattr(config, 'issnet_senha_certificado', '')
            or getattr(config, 'nacional_senha_certificado', '')
            or ''
        )
        usuario = getattr(config, 'issnet_usuario', '') or ''
        senha = getattr(config, 'issnet_senha', '') or ''
        ambiente = getattr(config, 'nacional_ambiente', None) or 'producao'

        cnpj_prestador = getattr(config, 'prestador_cnpj', '') or ''
        im_prestador = getattr(config, 'prestador_inscricao_municipal', '') or ''
        xml_nfse = getattr(nfse, 'xml_nfse', '') or ''
        xml_cnpj, xml_im = _extrair_prestador_do_xml(xml_nfse)
        cnpj_prestador = xml_cnpj or cnpj_prestador
        im_prestador = xml_im or im_prestador

        cert_tmp = tempfile.NamedTemporaryFile(suffix='.pfx', delete=False)
        try:
            cert_tmp.write(bytes(cert_data))
            cert_tmp.close()

            from .issnet_client import ISSNetClient

            client = ISSNetClient(
                usuario=usuario,
                senha=senha,
                certificado_path=cert_tmp.name,
                senha_certificado=senha_cert,
                ambiente=ambiente,
            )
            resultado = client.consultar_url_nfse(
                numero_nf=numero_nf,
                prestador_cnpj=cnpj_prestador,
                inscricao_municipal=im_prestador,
            )
        finally:
            try:
                os.unlink(cert_tmp.name)
            except OSError:
                pass

        url = resultado.get('url') if resultado.get('success') else ''
        if not url_danfe_valida(url):
            return ''

        if salvar:
            try:
                nfse.pdf_url = url[:500]
                nfse.save(update_fields=['pdf_url'])
            except Exception as exc:
                logger.debug('Nao foi possivel salvar pdf_url superadmin id=%s: %s', getattr(nfse, 'id', None), exc)
        return url
    except Exception as exc:
        logger.warning('Erro ao buscar URL DANFE ISSNet (superadmin): %s', exc)
        return ''
