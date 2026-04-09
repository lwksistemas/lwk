"""
Serviço unificado de emissão de NFS-e
Escolhe o provedor baseado na configuração da loja
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)


class NFSeService:
    """
    Serviço unificado para emissão de NFS-e.
    
    Suporta múltiplos provedores:
    - Asaas (intermediário)
    - ISSNet Ribeirão Preto (direto)
    - API Nacional NFS-e (direto)
    - Manual (sem integração)
    """
    
    def __init__(self, loja):
        """
        Inicializa serviço para uma loja específica.
        
        Args:
            loja: Instância do modelo Loja
        """
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
    ) -> Dict[str, Any]:
        """
        Emite NFS-e baseado na configuração da loja.
        
        Args:
            tomador_cpf_cnpj: CPF/CNPJ do tomador (cliente)
            tomador_nome: Nome/Razão social do tomador
            tomador_email: Email do tomador
            tomador_endereco: Endereço do tomador (dict)
            servico_descricao: Descrição do serviço prestado
            valor_servicos: Valor total dos serviços
            numero_rps: Número do RPS (gerado automaticamente se não fornecido)
            enviar_email: Se True, envia email para o tomador
        
        Returns:
            Dict com resultado da emissão:
            {
                'success': bool,
                'numero_nf': str,
                'codigo_verificacao': str,
                'data_emissao': datetime,
                'pdf_url': str,
                'xml_url': str,
                'error': str (se houver erro)
            }
        """
        try:
            provedor = self.config.provedor_nf
            
            logger.info(f"Emitindo NFS-e para loja {self.loja.slug} via {provedor}")
            
            if provedor == 'asaas':
                return self._emitir_via_asaas(
                    tomador_cpf_cnpj=tomador_cpf_cnpj,
                    tomador_nome=tomador_nome,
                    tomador_email=tomador_email,
                    servico_descricao=servico_descricao,
                    valor_servicos=valor_servicos,
                    enviar_email=enviar_email,
                )
            
            elif provedor == 'issnet':
                return self._emitir_via_issnet(
                    tomador_cpf_cnpj=tomador_cpf_cnpj,
                    tomador_nome=tomador_nome,
                    tomador_email=tomador_email,
                    tomador_endereco=tomador_endereco,
                    servico_descricao=servico_descricao,
                    valor_servicos=valor_servicos,
                    numero_rps=numero_rps,
                    enviar_email=enviar_email,
                )
            
            elif provedor == 'nacional':
                return {
                    'success': False,
                    'error': 'API Nacional NFS-e ainda não implementada'
                }
            
            elif provedor == 'manual':
                return {
                    'success': False,
                    'error': 'Emissão manual configurada - emita a nota manualmente no portal da prefeitura'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Provedor desconhecido: {provedor}'
                }
                
        except Exception as e:
            logger.exception(f"Erro ao emitir NFS-e: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _emitir_via_asaas(
        self,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_email: str,
        servico_descricao: str,
        valor_servicos: Decimal,
        enviar_email: bool,
    ) -> Dict[str, Any]:
        """
        Emite NFS-e via Asaas (intermediário).
        
        Nota: Requer que a loja tenha conta no Asaas configurada.
        """
        try:
            # TODO: Implementar emissão via Asaas
            # Requer:
            # 1. Loja ter conta no Asaas
            # 2. Criar customer no Asaas
            # 3. Criar payment no Asaas
            # 4. Emitir NF vinculada ao payment
            
            logger.warning("Emissão via Asaas ainda não implementada para lojas")
            
            return {
                'success': False,
                'error': 'Emissão via Asaas para lojas ainda não implementada. Use ISSNet ou emissão manual.'
            }
            
        except Exception as e:
            logger.exception(f"Erro ao emitir via Asaas: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _emitir_via_issnet(
        self,
        tomador_cpf_cnpj: str,
        tomador_nome: str,
        tomador_email: str,
        tomador_endereco: Dict[str, str],
        servico_descricao: str,
        valor_servicos: Decimal,
        numero_rps: Optional[int],
        enviar_email: bool,
    ) -> Dict[str, Any]:
        """
        Emite NFS-e via ISSNet (direto na prefeitura).
        """
        try:
            from .issnet_client import ISSNetClient
            
            # Validar configuração
            if not self.config.issnet_usuario:
                return {
                    'success': False,
                    'error': 'Usuário ISSNet não configurado'
                }
            
            if not self.config.issnet_senha:
                return {
                    'success': False,
                    'error': 'Senha ISSNet não configurada'
                }
            
            if not self.config.issnet_certificado:
                return {
                    'success': False,
                    'error': 'Certificado digital não configurado'
                }
            
            if not self.config.issnet_senha_certificado:
                return {
                    'success': False,
                    'error': 'Senha do certificado não configurada'
                }
            
            # Gerar número RPS se não fornecido
            if numero_rps is None:
                numero_rps = self._gerar_numero_rps()
            
            # Criar cliente ISSNet
            client = ISSNetClient(
                usuario=self.config.issnet_usuario,
                senha=self.config.issnet_senha,
                certificado_path=self.config.issnet_certificado.path,
                senha_certificado=self.config.issnet_senha_certificado,
                ambiente='producao'
            )
            
            # Emitir NFS-e
            resultado = client.emitir_nfse(
                prestador_cnpj=self.loja.cpf_cnpj,
                prestador_inscricao_municipal=self._get_inscricao_municipal(),
                prestador_razao_social=self.loja.nome,
                tomador_cpf_cnpj=tomador_cpf_cnpj,
                tomador_nome=tomador_nome,
                tomador_endereco=tomador_endereco,
                servico_codigo=self.config.codigo_servico_municipal,
                servico_descricao=servico_descricao or self.config.descricao_servico_padrao,
                valor_servicos=valor_servicos,
                aliquota_iss=self.config.aliquota_iss,
                numero_rps=numero_rps,
            )
            
            # Se sucesso, salvar no banco e enviar email
            if resultado.get('success'):
                # Salvar NFS-e no banco
                self._salvar_nfse(resultado, tomador_email)
                
                # Enviar email se solicitado
                if enviar_email and tomador_email:
                    self._enviar_email_nfse(
                        tomador_email=tomador_email,
                        tomador_nome=tomador_nome,
                        numero_nf=resultado['numero_nf'],
                        valor=valor_servicos,
                        descricao=servico_descricao,
                    )
            
            return resultado
            
        except Exception as e:
            logger.exception(f"Erro ao emitir via ISSNet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_inscricao_municipal(self) -> str:
        """
        Obtém inscrição municipal da loja.
        
        Returns:
            str: Inscrição municipal da loja
        """
        return getattr(self.loja, 'inscricao_municipal', '') or ''
    
    def _gerar_numero_rps(self) -> int:
        """
        Gera número sequencial de RPS para a loja.
        
        Returns:
            int: Próximo número de RPS
        """
        from .models import NFSe
        
        # Buscar último RPS da loja
        ultimo_rps = NFSe.objects.filter(
            loja=self.loja
        ).order_by('-numero_rps').first()
        
        if ultimo_rps:
            return ultimo_rps.numero_rps + 1
        else:
            return 1
    
    def _salvar_nfse(self, resultado: Dict[str, Any], tomador_email: str):
        """
        Salva NFS-e emitida no banco de dados.
        """
        try:
            from .models import NFSe
            
            NFSe.objects.create(
                loja=self.loja,
                numero_nf=resultado['numero_nf'],
                codigo_verificacao=resultado.get('codigo_verificacao', ''),
                data_emissao=resultado.get('data_emissao', datetime.now()),
                valor=resultado.get('valor', 0),
                tomador_email=tomador_email,
                xml_nfse=resultado.get('xml_nfse', ''),
                provedor=self.config.provedor_nf,
                status='emitida',
            )
            
            logger.info(f"NFS-e {resultado['numero_nf']} salva no banco")
            
        except Exception as e:
            logger.error(f"Erro ao salvar NFS-e no banco: {e}")
    
    def _enviar_email_nfse(
        self,
        tomador_email: str,
        tomador_nome: str,
        numero_nf: str,
        valor: Decimal,
        descricao: str,
    ):
        """
        Envia email para o tomador com a NFS-e.
        """
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            assunto = f'Nota Fiscal de Serviço - {self.loja.nome}'
            
            mensagem = f"""
Olá {tomador_nome}!

A nota fiscal de serviço foi emitida com sucesso.

📋 DADOS DA NOTA FISCAL:
• Número: {numero_nf}
• Prestador: {self.loja.nome}
• CNPJ: {self.loja.cpf_cnpj}
• Valor: R$ {valor:.2f}
• Descrição: {descricao}

Para consultar a nota fiscal, acesse o portal da Prefeitura de Ribeirão Preto.

---

Atenciosamente,
{self.loja.nome}
"""
            
            send_mail(
                assunto,
                mensagem,
                settings.DEFAULT_FROM_EMAIL,
                [tomador_email],
                fail_silently=False,
            )
            
            logger.info(f"Email de NFS-e enviado para {tomador_email}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email de NFS-e: {e}")
    
    def consultar_nfse(self, numero_nf: str) -> Dict[str, Any]:
        """
        Consulta NFS-e emitida.
        
        Args:
            numero_nf: Número da NFS-e
        
        Returns:
            Dict com dados da NFS-e
        """
        try:
            provedor = self.config.provedor_nf
            
            if provedor == 'issnet':
                from .issnet_client import ISSNetClient
                
                client = ISSNetClient(
                    usuario=self.config.issnet_usuario,
                    senha=self.config.issnet_senha,
                    certificado_path=self.config.issnet_certificado.path,
                    senha_certificado=self.config.issnet_senha_certificado,
                )
                
                return client.consultar_nfse(numero_nf)
            
            else:
                return {
                    'success': False,
                    'error': f'Consulta não suportada para provedor {provedor}'
                }
                
        except Exception as e:
            logger.exception(f"Erro ao consultar NFS-e: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancelar_nfse(self, numero_nf: str, motivo: str) -> Dict[str, Any]:
        """
        Cancela NFS-e emitida.
        
        Args:
            numero_nf: Número da NFS-e
            motivo: Motivo do cancelamento
        
        Returns:
            Dict com resultado do cancelamento
        """
        try:
            provedor = self.config.provedor_nf
            
            if provedor == 'issnet':
                from .issnet_client import ISSNetClient
                
                client = ISSNetClient(
                    usuario=self.config.issnet_usuario,
                    senha=self.config.issnet_senha,
                    certificado_path=self.config.issnet_certificado.path,
                    senha_certificado=self.config.issnet_senha_certificado,
                )
                
                resultado = client.cancelar_nfse(numero_nf, motivo)
                
                # Atualizar status no banco
                if resultado.get('success'):
                    from .models import NFSe
                    NFSe.objects.filter(
                        loja=self.loja,
                        numero_nf=numero_nf
                    ).update(status='cancelada')
                
                return resultado
            
            else:
                return {
                    'success': False,
                    'error': f'Cancelamento não suportado para provedor {provedor}'
                }
                
        except Exception as e:
            logger.exception(f"Erro ao cancelar NFS-e: {e}")
            return {
                'success': False,
                'error': str(e)
            }
