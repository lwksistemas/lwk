"""Ações de NFS-e no contexto da loja (CRM / ViewSet)."""
from decimal import Decimal
from typing import Any

from rest_framework import status


class ReenvioNFSeLojaError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ExclusaoNFSeLojaError(Exception):
    def __init__(self, message: str, http_status: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.http_status = http_status
        super().__init__(message)


def reenviar_email_nfse_loja(nfse: Any, loja: Any, loja_id: int) -> str:
    """Reenvia e-mail da NFS-e ao tomador (formato loja/CRM). Retorna o e-mail enviado."""
    from nfse_integration.danfe import buscar_url_danfe_issnet
    from nfse_integration.email_nfse import enviar_email_nfse_tomador

    if not nfse.tomador_email:
        raise ReenvioNFSeLojaError('NFS-e não possui email do tomador')

    url_danfe = buscar_url_danfe_issnet(nfse, loja_id=loja_id, loja=loja)
    enviar_email_nfse_tomador(
        loja=loja,
        tomador_email=nfse.tomador_email,
        tomador_nome=nfse.tomador_nome,
        numero_nf=nfse.numero_nf,
        valor=nfse.valor,
        descricao=nfse.servico_descricao,
        url_danfe=url_danfe,
        codigo_verificacao=nfse.codigo_verificacao,
        xml_content=nfse.xml_nfse or nfse.xml_rps or '',
        fail_silently=False,
    )
    return nfse.tomador_email


def validar_exclusao_nfse_loja(nfse: Any) -> None:
    """Levanta ExclusaoNFSeLojaError se a nota não puder ser excluída."""
    if nfse.status == 'emitida':
        raise ExclusaoNFSeLojaError(
            'Nota fiscal emitida não pode ser excluída. Use a opção Cancelar.'
        )
    if nfse.status == 'cancelada':
        raise ExclusaoNFSeLojaError(
            'Nota fiscal cancelada não pode ser excluída (manter para histórico).'
        )


def xml_nfse_conteudo(nfse: Any) -> str:
    return nfse.xml_nfse or nfse.xml_rps or ''


def processar_emissao_nfse_loja(
    loja: Any,
    loja_id: int,
    validated_data: dict[str, Any],
) -> tuple[dict[str, Any], int]:
    """
    Emite NFS-e para a loja atual.
    Retorna (corpo da resposta, status HTTP).
    """
    from nfse_integration.emissao import montar_dados_tomador_nfse
    from nfse_integration.models import NFSe
    from nfse_integration.serializers import NFSeSerializer
    from nfse_integration.service import NFSeService

    tomador = montar_dados_tomador_nfse(validated_data, loja_id)
    service = NFSeService(loja)

    codigo_cnae = (validated_data.get('codigo_cnae') or '').strip() or None
    codigo_servico = (validated_data.get('codigo_servico') or '').strip() or None

    resultado = service.emitir_nfse(
        tomador_cpf_cnpj=tomador.cpf_cnpj,
        tomador_nome=tomador.nome,
        tomador_email=tomador.email,
        tomador_endereco=tomador.endereco,
        servico_descricao=validated_data['servico_descricao'],
        valor_servicos=Decimal(str(validated_data['valor_servicos'])),
        enviar_email=validated_data.get('enviar_email', True),
        codigo_cnae=codigo_cnae,
        codigo_servico=codigo_servico,
    )

    if resultado['success']:
        nfse = NFSe.objects.filter(
            loja_id=loja_id,
            numero_nf=resultado['numero_nf'],
        ).first()
        if nfse:
            body = {
                'success': True,
                'message': 'NFS-e emitida com sucesso',
                'nfse': NFSeSerializer(nfse).data,
            }
        else:
            body = {
                'success': True,
                'message': 'NFS-e emitida com sucesso',
                'numero_nf': resultado['numero_nf'],
                'codigo_verificacao': resultado.get('codigo_verificacao', ''),
            }
        return body, status.HTTP_201_CREATED

    erro_msg = resultado.get('error', 'Erro desconhecido')
    nfse_falha = service.registrar_falha_emissao(
        erro_msg=erro_msg,
        tomador_cpf_cnpj=tomador.cpf_cnpj,
        tomador_nome=tomador.nome,
        tomador_email=tomador.email,
        servico_descricao=validated_data['servico_descricao'],
        valor_servicos=Decimal(str(validated_data['valor_servicos'])),
        numero_rps=int(resultado.get('numero_rps') or 0),
    )
    body: dict[str, Any] = {'success': False, 'error': erro_msg}
    if nfse_falha:
        body['nfse'] = NFSeSerializer(nfse_falha).data
    return body, status.HTTP_400_BAD_REQUEST
