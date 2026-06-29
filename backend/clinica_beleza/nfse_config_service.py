"""
Service layer para configuração de NFS-e da Clínica da Beleza.
"""
import logging
import os
import tempfile

from .models import ClinicaBelezaNFSeConfig

logger = logging.getLogger(__name__)


def get_or_create_nfse_config(loja_id: int) -> ClinicaBelezaNFSeConfig:
    """Busca ou cria a configuração de NFS-e para a loja."""
    config = ClinicaBelezaNFSeConfig.objects.filter(loja_id=loja_id).first()
    if config is None:
        config = ClinicaBelezaNFSeConfig(loja_id=loja_id)
        config.save()
    return config


def test_issnet_connection(request, config: ClinicaBelezaNFSeConfig) -> dict:
    """
    Testa conexão com o WebService ISSNet usando certificado da loja.
    Valida PFX/senha e tenta acessar o WSDL.
    Retorna dict com 'success', 'message'/'detail'.
    """
    # Certificado: do upload ou do banco
    cert_file = request.FILES.get('issnet_certificado')
    if cert_file:
        cert_data = cert_file.read()
    else:
        cert_data = getattr(config, 'issnet_certificado', None)
        if cert_data:
            cert_data = bytes(cert_data)

    senha = (request.data.get('issnet_senha_certificado') or '').strip()
    if not senha:
        senha = getattr(config, 'issnet_senha_certificado', '') or ''

    if not cert_data:
        return {'success': False, 'detail': 'Certificado .pfx não configurado.'}
    if not senha:
        return {'success': False, 'detail': 'Senha do certificado não informada.'}

    try:
        from nfse_integration.issnet_client import testar_conexao_issnet

        usuario = (
            (request.data.get('issnet_usuario') or '').strip()
            or getattr(config, 'issnet_usuario', '') or ''
        )
        senha_ws = (
            (request.data.get('issnet_senha') or '').strip()
            or getattr(config, 'issnet_senha', '') or ''
        )
        ambiente = 'homologacao' if getattr(config, 'issnet_ambiente_homologacao', False) else 'producao'

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
        tmp.write(cert_data)
        tmp.close()

        try:
            resultado = testar_conexao_issnet(
                usuario=usuario,
                senha=senha_ws,
                certificado_path=tmp.name,
                senha_certificado=senha,
                ambiente=ambiente,
            )
        finally:
            os.unlink(tmp.name)

        if resultado.get('success'):
            return {
                'success': True,
                'message': resultado.get('message', 'Conexão ISSNet OK.'),
                'ambiente': ambiente,
            }
        else:
            return {
                'success': False,
                'detail': resultado.get('detail', 'Falha ao conectar ao ISSNet.'),
            }

    except Exception as e:
        logger.warning('test_issnet_connection (clinica_beleza): %s', e)
        return {'success': False, 'detail': str(e)}
