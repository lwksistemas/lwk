"""
Serviço unificado de emissão de NFS-e
Escolhe o provedor baseado na configuração da loja
"""
import logging
import re
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date

import requests

logger = logging.getLogger(__name__)


def _normalize_cep_digits(cep: Optional[str]) -> str:
    """CEP com 8 dígitos (somente números) para APIs como Asaas."""
    digits = re.sub(r'\D', '', cep or '')
    return digits if len(digits) == 8 else ''


def _tomador_endereco_para_asaas(endereco: Optional[Dict[str, str]]) -> Dict[str, Any]:
    """
    Mapeia o dict de endereço do tomador para campos da API Asaas (customers).
    https://docs.asaas.com/reference/criar-novo-cliente
    """
    if not endereco:
        endereco = {}
    logradouro = (endereco.get('logradouro') or '').strip()
    numero = (endereco.get('numero') or '').strip() or 'S/N'
    complemento = (endereco.get('complemento') or '').strip()
    bairro = (endereco.get('bairro') or '').strip()
    cidade = (endereco.get('cidade') or '').strip()
    uf = (endereco.get('uf') or '').strip().upper()
    cep_ok = _normalize_cep_digits(endereco.get('cep'))

    out: Dict[str, Any] = {}
    if logradouro:
        out['address'] = logradouro[:200]
    out['addressNumber'] = str(numero)[:20]
    if complemento:
        out['complement'] = complemento[:200]
    if bairro:
        out['province'] = bairro[:100]
    if cep_ok:
        out['postalCode'] = cep_ok
    if cidade:
        out['city'] = cidade[:100]
    if len(uf) == 2:
        out['state'] = uf
    return out


def _validar_endereco_asaas_nfse(addr_asaas: Dict[str, Any]) -> Optional[str]:
    """Retorna mensagem de erro se faltar dado obrigatório para NFS-e no Asaas."""
    if not addr_asaas.get('address'):
        return 'Informe o logradouro do tomador (endereço completo é obrigatório para NFS-e no Asaas).'
    if not addr_asaas.get('postalCode'):
        return 'Informe um CEP válido (8 dígitos) do tomador.'
    if not addr_asaas.get('province'):
        return 'Informe o bairro do tomador.'
    if not addr_asaas.get('city'):
        return 'Informe a cidade do tomador.'
    if not addr_asaas.get('state'):
        return 'Informe a UF (estado) do tomador com 2 letras.'
    return None


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
                    tomador_endereco=tomador_endereco,
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
        tomador_endereco: Dict[str, str],
        servico_descricao: str,
        valor_servicos: Decimal,
        enviar_email: bool,
    ) -> Dict[str, Any]:
        """
        Emite NFS-e via API Asaas da própria loja (API key em CRMConfig).

        Fluxo: cliente (tomador) → cobrança → recebimento registrado → NF agendada → autorizada.
        Requer chave com escopo de notas fiscais (INVOICE) na conta Asaas da loja.
        """
        from asaas_integration.client import AsaasClient

        try:
            api_key = (getattr(self.config, 'asaas_api_key', None) or '').strip()
            if not api_key:
                return {
                    'success': False,
                    'error': (
                        'Configure a API Key do Asaas da sua loja em '
                        'Configurações → Nota Fiscal (Integrações → API no painel Asaas). '
                        'A chave deve ser da conta da sua empresa (não da LWK).'
                    ),
                }

            sandbox = bool(getattr(self.config, 'asaas_sandbox', False))
            client = AsaasClient(api_key=api_key, sandbox=sandbox)

            cpf_cnpj = re.sub(r'\D', '', tomador_cpf_cnpj or '')
            if len(cpf_cnpj) not in (11, 14):
                return {
                    'success': False,
                    'error': 'CPF/CNPJ do tomador inválido (use 11 ou 14 dígitos).',
                }

            addr_asaas = _tomador_endereco_para_asaas(tomador_endereco)
            addr_err = _validar_endereco_asaas_nfse(addr_asaas)
            if addr_err:
                return {'success': False, 'error': addr_err}

            customer_data = {
                'name': (tomador_nome or 'Cliente')[:200],
                'email': (tomador_email or '')[:200],
                'cpfCnpj': cpf_cnpj,
                'notificationDisabled': True,
                **addr_asaas,
            }
            cust = client.create_customer(customer_data)
            customer_id = cust.get('id')
            if not customer_id:
                return {'success': False, 'error': 'Asaas não retornou ID do cliente.'}

            valor_float = float(valor_servicos)
            if valor_float <= 0:
                return {'success': False, 'error': 'Valor do serviço deve ser maior que zero.'}

            hoje = date.today().isoformat()
            desc = (servico_descricao or self.config.descricao_servico_padrao or 'Serviço prestado')[:500]
            payment_data = {
                'customer': customer_id,
                'billingType': 'BOLETO',
                'value': round(valor_float, 2),
                'dueDate': hoje,
                'description': desc,
            }
            pay = client.create_payment(payment_data)
            payment_id = pay.get('id')
            if not payment_id:
                return {'success': False, 'error': 'Asaas não retornou ID da cobrança.'}

            try:
                client.receive_payment_in_cash(payment_id, round(valor_float, 2), hoje)
            except Exception as recv_err:
                logger.warning('receiveInCash falhou (tentativa segue): %s', recv_err)

            # Mesma configuração municipal das NF de assinatura (env ASAAS_INVOICE_*),
            # com fallback para os campos da loja no CRM se o ambiente não tiver env.
            from asaas_integration.invoice_service import get_municipal_invoice_config

            municipal = get_municipal_invoice_config()
            codigo_raw = municipal.get('municipal_service_code') or (
                self.config.codigo_servico_municipal or '1401'
            )
            codigo = str(codigo_raw).replace('.', '').replace('-', '')[:10]
            nome_serv = (municipal.get('municipal_service_name') or self.config.descricao_servico_padrao or desc)[
                :200
            ]
            service_id = municipal.get('municipal_service_id') or None
            iss_pct = float(self.config.aliquota_iss or 2)

            created = client.create_invoice(
                payment_id=payment_id,
                service_description=desc,
                value=round(valor_float, 2),
                effective_date=hoje,
                municipal_service_code=codigo,
                municipal_service_name=nome_serv,
                municipal_service_id=service_id,
                iss_aliquota=iss_pct,
            )
            invoice_id = created.get('id')
            if not invoice_id:
                return {'success': False, 'error': 'Asaas não retornou ID da nota fiscal agendada.'}

            client.authorize_invoice(invoice_id)
            inv = client.get_invoice(invoice_id)

            numero_nf = str(
                inv.get('number')
                or inv.get('invoiceNumber')
                or inv.get('rpsNumber')
                or invoice_id
            )
            pdf_url = (
                inv.get('pdfUrl')
                or inv.get('invoiceUrl')
                or inv.get('url')
                or ''
            )
            codigo_ver = str(inv.get('validationCode') or inv.get('verificationCode') or '')

            resultado = {
                'success': True,
                'numero_nf': numero_nf[:50],
                'codigo_verificacao': codigo_ver[:50],
                'data_emissao': datetime.now(),
                'valor': valor_float,
                'xml_nfse': '',
                'pdf_url': pdf_url[:500] if pdf_url else '',
                'tomador_nome': tomador_nome,
                'tomador_cpf_cnpj': tomador_cpf_cnpj,
                'servico_descricao': desc,
            }

            self._salvar_nfse(resultado, tomador_email)
            if enviar_email and tomador_email:
                self._enviar_email_nfse(
                    tomador_email=tomador_email,
                    tomador_nome=tomador_nome,
                    numero_nf=numero_nf,
                    valor=valor_servicos,
                    descricao=desc,
                )

            return resultado

        except requests.HTTPError as e:
            msg = str(e)
            resp = getattr(e, 'response', None)
            if resp is not None:
                try:
                    body = resp.json()
                    errs = body.get('errors') or []
                    texts = []
                    for item in errs:
                        if isinstance(item, dict):
                            t = (item.get('description') or item.get('message') or '').strip()
                            if t:
                                texts.append(t)
                    if texts:
                        msg = '; '.join(texts)
                except Exception:
                    pass
            logger.warning('Erro ao emitir via Asaas (API): %s', msg)
            return {'success': False, 'error': msg}

        except Exception as e:
            logger.exception(f"Erro ao emitir via Asaas: {e}")
            return {
                'success': False,
                'error': str(e),
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
                loja_id=self.loja.id,
                numero_nf=resultado['numero_nf'],
                codigo_verificacao=resultado.get('codigo_verificacao', ''),
                data_emissao=resultado.get('data_emissao', datetime.now()),
                valor=resultado.get('valor', 0),
                tomador_email=tomador_email,
                tomador_nome=resultado.get('tomador_nome', ''),
                tomador_cpf_cnpj=resultado.get('tomador_cpf_cnpj', ''),
                servico_descricao=(resultado.get('servico_descricao') or '')[:500],
                xml_nfse=resultado.get('xml_nfse', ''),
                pdf_url=resultado.get('pdf_url', '')[:500],
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
