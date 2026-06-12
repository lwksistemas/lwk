"""
Serviço unificado de emissão de NFS-e para lojas.
Roteamento automático:
  - provedor 'issnet' → WebService ISSNet (municipal)
  - provedor 'nacional' → API ADN Nacional (SEFIN)
  - provedor 'manual' → sem emissão automática
"""
import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from nfse_integration.cancelamento_loja import cancelar_nfse_loja
from nfse_integration.emissao_issnet_loja import emitir_via_issnet_loja
from nfse_integration.emissao_nacional_loja import emitir_via_nacional_loja
from nfse_integration.loja_nfse_api import (
    enviar_email_pos_emissao_loja,
    validar_config_crm_loja,
)
from nfse_integration.persistencia_nfse_loja import registrar_falha_emissao_loja

logger = logging.getLogger(__name__)


class NFSeService:
    """Serviço de emissão de NFS-e para lojas (ISSNet ou Nacional)."""

    def __init__(self, loja):
        self.loja = loja
        self.config = self._get_config()
        validar_config_crm_loja(self.loja, self.config)

    def _get_config(self):
        from crm_vendas.models import CRMConfig

        return CRMConfig.get_or_create_for_loja(self.loja.id)

    def emitir_nfse(
        self,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_email: str,
        tomador_endereco: Dict[str, str],
        servico_descricao: str,
        valor_servicos: Decimal,
        numero_rps: Optional[int] = None,
        enviar_email: bool = True,
        codigo_cnae: Optional[str] = None,
        codigo_servico: Optional[str] = None,
        item_lista_servico: Optional[str] = None,
        empresa_prestadora_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Emite NFS-e com roteamento automático por provedor."""
        try:
            from nfse_integration.prestador_loja import (
                PrestadorNFSeNaoEncontradoError,
                resolver_prestador_emissao_loja,
            )

            try:
                prestador = resolver_prestador_emissao_loja(
                    self.loja,
                    self.config,
                    self.loja.id,
                    empresa_prestadora_id,
                )
            except PrestadorNFSeNaoEncontradoError as exc:
                return {'success': False, 'error': str(exc)}

            provedor = getattr(self.config, 'provedor_nf', 'issnet')

            if provedor == 'manual':
                return {
                    'success': False,
                    'error': 'Emissão manual configurada - emita a nota no portal da prefeitura',
                }

            if provedor == 'desabilitado':
                return {'success': False, 'error': 'Emissão de NFS-e desabilitada'}

            from nfse_integration.nfse_geo import preparar_endereco_tomador_emissao

            tomador_endereco_final, erro_endereco = preparar_endereco_tomador_emissao(
                tomador_endereco,
                email=tomador_email,
            )
            if erro_endereco:
                return {'success': False, 'error': erro_endereco}

            kwargs = dict(
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_email=tomador_email,
                tomador_endereco=tomador_endereco_final,
                servico_descricao=servico_descricao,
                valor_servicos=valor_servicos,
                enviar_email=enviar_email,
                enviar_email_fn=self._enviar_email_nfse,
                codigo_cnae_override=codigo_cnae,
                codigo_servico_override=codigo_servico,
                item_lista_override=item_lista_servico,
                prestador=prestador,
            )

            if provedor == 'issnet':
                return emitir_via_issnet_loja(self.loja, self.config, **kwargs)

            return emitir_via_nacional_loja(self.loja, self.config, **kwargs)

        except Exception as exc:
            logger.exception('Erro ao emitir NFS-e: %s', exc)
            return {'success': False, 'error': str(exc)}

    def cancelar_nfse(
        self,
        numero_nf: str,
        motivo: str,
        codigo_cancelamento: str | int | None = '1',
    ) -> Dict[str, Any]:
        from nfse_integration.models import NFSe

        nfse = NFSe.objects.filter(loja_id=self.loja.id, numero_nf=numero_nf).first()
        if not nfse:
            return {'success': False, 'error': 'NFS-e não encontrada'}

        return cancelar_nfse_loja(
            self.loja,
            self.config,
            nfse,
            numero_nf,
            motivo,
            codigo_cancelamento,
        )

    def registrar_falha_emissao(
        self,
        erro_msg: str,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_email: str,
        servico_descricao: str,
        valor_servicos: Decimal,
        numero_rps: int = 0,
    ):
        return registrar_falha_emissao_loja(
            self.loja.id,
            erro_msg,
            tomador_cpf_cnpj,
            tomador_nome,
            tomador_email,
            servico_descricao,
            valor_servicos,
            numero_rps=numero_rps,
        )

    def _enviar_email_nfse(
        self,
        tomador_email: str,
        tomador_nome: str,
        numero_nf: str,
        valor: Decimal,
        descricao: str,
    ):
        try:
            enviar_email_pos_emissao_loja(
                self.loja,
                self.config,
                numero_nf=numero_nf,
                tomador_email=tomador_email,
                tomador_nome=tomador_nome,
                valor=valor,
                descricao=descricao,
                fail_silently=True,
            )
        except Exception as exc:
            logger.error('Erro ao enviar email NFS-e: %s', exc)
