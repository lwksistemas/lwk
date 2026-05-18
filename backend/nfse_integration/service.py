"""
Serviço unificado de emissão de NFS-e para lojas.
Roteamento automático:
  - provedor 'issnet' → WebService ISSNet (municipal)
  - provedor 'nacional' → API ADN Nacional (SEFIN)
  - provedor 'manual' → sem emissão automática
"""
import logging
import re
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


def _buscar_codigo_ibge(cep: str) -> str:
    """Busca código IBGE do município pelo CEP (via ViaCEP)."""
    import requests
    cep_digits = re.sub(r'\D', '', cep or '')
    if len(cep_digits) == 8:
        try:
            resp = requests.get(f'https://viacep.com.br/ws/{cep_digits}/json/', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                ibge = data.get('ibge', '')
                if ibge:
                    return str(ibge)
        except Exception as e:
            logger.warning('Erro ao buscar IBGE pelo CEP %s: %s', cep_digits, e)
    return ''


class NFSeService:
    """
    Serviço de emissão de NFS-e para lojas via Nacional (ADN).
    """

    def __init__(self, loja):
        self.loja = loja
        self.config = self._get_config()

    def _get_config(self):
        """Obtém configuração de NFS-e da loja."""
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
    ) -> Dict[str, Any]:
        """
        Emite NFS-e com roteamento automático por provedor.
        """
        try:
            provedor = getattr(self.config, 'provedor_nf', 'issnet')

            if provedor == 'manual':
                return {
                    'success': False,
                    'error': 'Emissão manual configurada - emita a nota no portal da prefeitura'
                }

            if provedor == 'desabilitado':
                return {'success': False, 'error': 'Emissão de NFS-e desabilitada'}

            if provedor == 'issnet':
                return self._emitir_via_issnet(
                    tomador_cpf_cnpj=tomador_cpf_cnpj,
                    tomador_nome=tomador_nome,
                    tomador_email=tomador_email,
                    tomador_endereco=tomador_endereco,
                    servico_descricao=servico_descricao,
                    valor_servicos=valor_servicos,
                    enviar_email=enviar_email,
                    codigo_cnae_override=codigo_cnae,
                    codigo_servico_override=codigo_servico,
                )

            # Nacional (ADN) - para municípios que aderiram ao Emissor Nacional
            return self._emitir_via_nacional(
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_email=tomador_email,
                tomador_endereco=tomador_endereco,
                servico_descricao=servico_descricao,
                valor_servicos=valor_servicos,
                enviar_email=enviar_email,
                codigo_cnae_override=codigo_cnae,
                codigo_servico_override=codigo_servico,
            )

        except Exception as e:
            logger.exception('Erro ao emitir NFS-e: %s', e)
            return {'success': False, 'error': str(e)}

    def _emitir_via_issnet(
        self,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_email: str,
        tomador_endereco: Dict[str, str],
        servico_descricao: str,
        valor_servicos: Decimal,
        enviar_email: bool,
        codigo_cnae_override: Optional[str] = None,
        codigo_servico_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Emite NFS-e via WebService ISSNet (municipal)."""
        try:
            from .issnet_client import ISSNetClient

            cert_data = getattr(self.config, 'issnet_certificado', None) or getattr(self.config, 'nacional_certificado', None)
            senha_cert = getattr(self.config, 'issnet_senha_certificado', '') or getattr(self.config, 'nacional_senha_certificado', '')

            if not cert_data:
                return {'success': False, 'error': 'Certificado digital não configurado para ISSNet'}
            if not senha_cert:
                return {'success': False, 'error': 'Senha do certificado não configurada'}

            cnpj_prestador = re.sub(r'\D', '', self.loja.cpf_cnpj or '')
            im_prestador = getattr(self.config, 'inscricao_municipal', '') or getattr(self.loja, 'inscricao_municipal', '') or ''
            codigo_servico_final = codigo_servico_override or getattr(self.config, 'codigo_servico_municipal', '1401') or '1401'
            codigo_cnae_final = codigo_cnae_override or (getattr(self.config, 'codigo_cnae', '') or '').strip()
            aliquota = float(getattr(self.config, 'aliquota_iss', 2.00))

            usuario_issnet = getattr(self.config, 'issnet_usuario', '') or ''
            senha_issnet = getattr(self.config, 'issnet_senha', '') or ''
            ambiente_issnet = 'homologacao' if getattr(self.config, 'issnet_ambiente_homologacao', False) else 'producao'

            # Salvar certificado em arquivo temporário
            import tempfile, os
            tmp_cert = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
            tmp_cert.write(bytes(cert_data))
            tmp_cert.close()

            try:
                client = ISSNetClient(
                    usuario=usuario_issnet,
                    senha=senha_issnet,
                    certificado_path=tmp_cert.name,
                    senha_certificado=senha_cert,
                    ambiente=ambiente_issnet,
                )

                numero_rps = self._gerar_numero_dps()

                resultado = client.emitir_nfse(
                    prestador_cnpj=cnpj_prestador,
                    prestador_inscricao_municipal=im_prestador,
                    prestador_razao_social=self.loja.nome or '',
                    tomador_cpf_cnpj=tomador_cpf_cnpj,
                    tomador_nome=tomador_nome,
                    tomador_endereco=tomador_endereco,
                    servico_codigo=codigo_servico_final,
                    servico_descricao=servico_descricao or 'Serviço prestado',
                    valor_servicos=Decimal(str(valor_servicos)),
                    aliquota_iss=Decimal(str(aliquota)),
                    numero_rps=numero_rps,
                    serie_rps=getattr(self.config, 'issnet_serie_rps', '1') or '1',
                    codigo_cnae=codigo_cnae_final or None,
                )
            finally:
                os.unlink(tmp_cert.name)

            if resultado.get('success'):
                resultado_final = {
                    'success': True,
                    'numero_nf': resultado.get('numero_nf', ''),
                    'codigo_verificacao': resultado.get('codigo_verificacao', ''),
                    'numero_rps': numero_rps,
                    'data_emissao': datetime.now(),
                    'valor': float(valor_servicos),
                    'xml_nfse': resultado.get('xml_nfse', ''),
                    'pdf_url': resultado.get('link_pdf', ''),
                    'tomador_nome': tomador_nome,
                    'tomador_cpf_cnpj': tomador_cpf_cnpj,
                    'servico_descricao': servico_descricao,
                }
                self._salvar_nfse(resultado_final, tomador_email, provedor='issnet')
                if enviar_email and tomador_email:
                    self._enviar_email_nfse(
                        tomador_email=tomador_email,
                        tomador_nome=tomador_nome,
                        numero_nf=resultado_final['numero_nf'],
                        valor=valor_servicos,
                        descricao=servico_descricao,
                    )
                return resultado_final
            else:
                return {'success': False, 'error': resultado.get('error', 'Erro ISSNet'), 'numero_rps': numero_rps}

        except Exception as e:
            logger.exception('Erro ao emitir via ISSNet: %s', e)
            return {'success': False, 'error': str(e)}

    def _emitir_via_nacional(
        self,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_email: str,
        tomador_endereco: Dict[str, str],
        servico_descricao: str,
        valor_servicos: Decimal,
        enviar_email: bool,
        codigo_cnae_override: Optional[str] = None,
        codigo_servico_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Emite NFS-e via ADN Nacional usando certificado da loja."""
        try:
            from nfse_integration.nacional import NacionalClient

            # Validações
            cert_data = getattr(self.config, 'nacional_certificado', None) or getattr(self.config, 'issnet_certificado', None)
            senha_cert = getattr(self.config, 'nacional_senha_certificado', '') or getattr(self.config, 'issnet_senha_certificado', '')
            codigo_municipio = getattr(self.config, 'nacional_codigo_municipio', '') or ''

            if not cert_data:
                return {'success': False, 'error': 'Certificado digital não configurado'}
            if not senha_cert:
                return {'success': False, 'error': 'Senha do certificado não configurada'}
            if not codigo_municipio:
                # Tentar buscar pelo CEP da loja
                cep_loja = getattr(self.loja, 'cep', '') or ''
                codigo_municipio = _buscar_codigo_ibge(cep_loja)
                if not codigo_municipio:
                    return {'success': False, 'error': 'Código IBGE do município não configurado'}

            # Número DPS
            numero_dps = self._gerar_numero_dps()

            # Cliente Nacional
            ambiente = getattr(self.config, 'nacional_ambiente', 'homologacao') or 'homologacao'
            client = NacionalClient(
                pfx_bytes=bytes(cert_data),
                senha_pfx=senha_cert,
                ambiente=ambiente,
            )

            # Resolver código IBGE do tomador
            cep_tomador = (tomador_endereco.get('cep') or '').strip()
            codigo_municipio_tomador = (tomador_endereco.get('codigo_municipio') or '').strip()
            if not codigo_municipio_tomador and cep_tomador:
                codigo_municipio_tomador = _buscar_codigo_ibge(cep_tomador)
            tomador_endereco_final = {**tomador_endereco, 'codigo_municipio': codigo_municipio_tomador}

            # Dados fiscais
            cnpj_prestador = re.sub(r'\D', '', self.loja.cpf_cnpj or '')
            im_prestador = getattr(self.config, 'inscricao_municipal', '') or getattr(self.loja, 'inscricao_municipal', '') or ''
            codigo_servico_final = codigo_servico_override or getattr(self.config, 'codigo_servico_municipal', '14.01') or '14.01'
            codigo_cnae_final = codigo_cnae_override or (getattr(self.config, 'codigo_cnae', '') or '').strip()
            aliquota = getattr(self.config, 'aliquota_iss', Decimal('2.00'))
            serie_dps = getattr(self.config, 'nacional_serie_dps', '900') or '900'

            resultado = client.emitir_nfse(
                numero_dps=numero_dps,
                serie_dps=serie_dps,
                codigo_municipio_prestador=codigo_municipio,
                prestador_cnpj=cnpj_prestador,
                prestador_inscricao_municipal=im_prestador,
                prestador_razao_social=self.loja.nome or '',
                prestador_email=getattr(self.loja, 'email', '') or '',
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco_final,
                tomador_email=tomador_email,
                codigo_servico=codigo_servico_final,
                descricao_servico=servico_descricao or getattr(self.config, 'descricao_servico_padrao', '') or 'Serviço prestado',
                codigo_cnae=codigo_cnae_final,
                codigo_municipio_incidencia=codigo_municipio,
                valor_servicos=valor_servicos,
                aliquota_iss=aliquota,
                iss_retido=False,
                optante_simples_nacional=getattr(self.config, 'optante_simples_nacional', True),
                incentivador_cultural=getattr(self.config, 'incentivador_cultural', False),
            )

            if resultado.get('success'):
                resultado_final = {
                    'success': True,
                    'numero_nf': resultado.get('chave_acesso', ''),
                    'codigo_verificacao': resultado.get('nsu_recepcao', ''),
                    'numero_rps': numero_dps,
                    'data_emissao': datetime.now(),
                    'valor': float(valor_servicos),
                    'xml_nfse': resultado.get('xml_dps', ''),
                    'pdf_url': '',
                    'tomador_nome': tomador_nome,
                    'tomador_cpf_cnpj': tomador_cpf_cnpj,
                    'servico_descricao': servico_descricao,
                }
                self._salvar_nfse(resultado_final, tomador_email)
                if enviar_email and tomador_email:
                    self._enviar_email_nfse(
                        tomador_email=tomador_email,
                        tomador_nome=tomador_nome,
                        numero_nf=resultado_final['numero_nf'],
                        valor=valor_servicos,
                        descricao=servico_descricao,
                    )
                return resultado_final
            else:
                error_msg = resultado.get('error', 'Erro desconhecido')
                erros = resultado.get('erros', [])
                if erros:
                    error_msg += ' | ' + '; '.join(
                        f"[{e.get('Codigo', '')}] {e.get('Descricao', '')}" if isinstance(e, dict) else str(e)
                        for e in erros
                    )
                return {'success': False, 'error': error_msg, 'numero_rps': numero_dps}

        except Exception as e:
            logger.exception('Erro ao emitir via Nacional: %s', e)
            return {'success': False, 'error': str(e)}

    def _gerar_numero_dps(self) -> int:
        """Próximo número DPS baseado no maior já gravado."""
        from django.db.models import Max
        from .models import NFSe

        mx = NFSe.objects.filter(loja_id=self.loja.id).aggregate(m=Max('numero_rps'))['m']
        mx = int(mx or 0)

        portal_ult = int(getattr(self.config, 'nacional_ultimo_dps', 0) or getattr(self.config, 'issnet_ultimo_rps_conhecido', 0) or 0)
        nxt = max(mx + 1, portal_ult + 1)
        logger.info('Nacional próximo DPS: max_BD=%s, portal=%s -> usando %s', mx, portal_ult, nxt)
        return nxt

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
        """Grava tentativa de emissão que falhou."""
        from django.utils import timezone
        from .models import NFSe

        numero_nf = f"FALHA-{uuid4().hex[:12]}"
        try:
            return NFSe.objects.create(
                loja_id=self.loja.id,
                numero_nf=numero_nf[:50],
                numero_rps=int(numero_rps or 0),
                codigo_verificacao='',
                data_emissao=timezone.now(),
                valor=valor_servicos,
                tomador_cpf_cnpj=(tomador_cpf_cnpj or '')[:18],
                tomador_nome=(tomador_nome or '')[:200],
                tomador_email=tomador_email or '',
                servico_descricao=(servico_descricao or '')[:500],
                provedor='nacional',
                status='erro',
                erro=(erro_msg or 'Erro desconhecido')[:2000],
            )
        except Exception as e:
            logger.error('Erro ao registrar falha de NFS-e: %s', e, exc_info=True)
            return None

    def _salvar_nfse(self, resultado: Dict[str, Any], tomador_email: str, provedor: str = 'nacional'):
        """Salva NFS-e emitida no banco."""
        try:
            from .models import NFSe

            NFSe.objects.create(
                loja_id=self.loja.id,
                numero_nf=resultado['numero_nf'],
                numero_rps=int(resultado.get('numero_rps') or 0),
                codigo_verificacao=resultado.get('codigo_verificacao', ''),
                data_emissao=resultado.get('data_emissao', datetime.now()),
                valor=resultado.get('valor', 0),
                tomador_email=tomador_email,
                tomador_nome=resultado.get('tomador_nome', ''),
                tomador_cpf_cnpj=resultado.get('tomador_cpf_cnpj', ''),
                servico_descricao=(resultado.get('servico_descricao') or '')[:500],
                xml_nfse=resultado.get('xml_nfse', ''),
                pdf_url=resultado.get('pdf_url', '')[:500],
                provedor=provedor,
                status='emitida',
            )
            logger.info('NFS-e %s salva no banco (provedor=%s)', resultado['numero_nf'], provedor)
        except Exception as e:
            logger.error('Erro ao salvar NFS-e no banco: %s', e)

    def _enviar_email_nfse(
        self,
        tomador_email: str,
        tomador_nome: str,
        numero_nf: str,
        valor: Decimal,
        descricao: str,
    ):
        """Envia email para o tomador com a NFS-e."""
        try:
            from django.core.mail import EmailMessage
            from django.conf import settings

            assunto = f'Nota Fiscal de Serviço - {self.loja.nome}'
            mensagem = (
                f'Olá {tomador_nome}!\n\n'
                f'A nota fiscal de serviço foi emitida.\n\n'
                f'📋 DADOS DA NOTA FISCAL:\n'
                f'• Chave de Acesso: {numero_nf}\n'
                f'• Prestador: {self.loja.nome}\n'
                f'• CNPJ: {self.loja.cpf_cnpj}\n'
                f'• Valor: R$ {valor:.2f}\n'
                f'• Descrição: {descricao}\n\n'
                f'---\n'
                f'Atenciosamente,\n'
                f'{self.loja.nome}'
            )

            email = EmailMessage(
                subject=assunto,
                body=mensagem,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[tomador_email],
            )

            # Anexar XML
            try:
                from .models import NFSe
                nfse = NFSe.objects.filter(
                    loja_id=self.loja.id, numero_nf=numero_nf
                ).order_by('-data_emissao').first()
                if nfse and nfse.xml_nfse:
                    email.attach(f'nfse_{numero_nf[:20]}.xml', nfse.xml_nfse.encode('utf-8'), 'application/xml')
            except Exception:
                pass

            email.send(fail_silently=True)
            logger.info('Email NFS-e enviado para %s', tomador_email)
        except Exception as e:
            logger.error('Erro ao enviar email NFS-e: %s', e)
