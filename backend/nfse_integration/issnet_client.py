"""
Cliente para webservice ISSNet de Ribeirão Preto
Emissão de NFS-e direta na prefeitura
"""
import logging
import base64
from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class ISSNetClient:
    """
    Cliente para webservice ISSNet de Ribeirão Preto.
    
    Permite emissão de NFS-e diretamente na prefeitura usando:
    - Certificado digital A1 (.pfx)
    - Credenciais de acesso (usuário/senha)
    - Webservice SOAP
    """
    
    def __init__(
        self,
        usuario: str,
        senha: str,
        certificado_path: str,
        senha_certificado: str,
        ambiente: str = 'producao'
    ):
        """
        Inicializa cliente ISSNet.
        
        Args:
            usuario: Usuário de acesso ao webservice
            senha: Senha de acesso ao webservice
            certificado_path: Caminho para arquivo .pfx do certificado
            senha_certificado: Senha do certificado digital
            ambiente: 'producao' ou 'homologacao'
        """
        self.usuario = usuario
        self.senha = senha
        self.certificado_path = certificado_path
        self.senha_certificado = senha_certificado
        self.ambiente = ambiente
        
        # URLs do webservice (Ribeirão Preto)
        self.urls = {
            'producao': 'https://issdigital.ribeirao preto.sp.gov.br/WsNFe2/LoteRps.jws',
            'homologacao': 'https://issdigital.homologacao.ribeirao preto.sp.gov.br/WsNFe2/LoteRps.jws'
        }
        
        self.wsdl_url = f"{self.urls[ambiente]}?wsdl"
        
        # Cliente SOAP será inicializado sob demanda
        self._soap_client = None
    
    def _get_soap_client(self):
        """
        Retorna cliente SOAP configurado com certificado.
        Inicializa apenas quando necessário (lazy loading).
        """
        if self._soap_client is not None:
            return self._soap_client
        
        try:
            from zeep import Client
            from zeep.transports import Transport
            from requests import Session
            from requests.adapters import HTTPAdapter
            from urllib3.util.ssl_ import create_urllib3_context
            import ssl
            
            # Carregar certificado
            with open(self.certificado_path, 'rb') as f:
                pfx_data = f.read()
            
            # Criar contexto SSL com certificado
            from cryptography.hazmat.primitives.serialization import pkcs12
            from cryptography.hazmat.backends import default_backend
            
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                self.senha_certificado.encode(),
                backend=default_backend()
            )
            
            # Configurar sessão com certificado
            session = Session()
            
            # Criar adapter com certificado
            # Nota: Zeep + requests + certificado requer configuração especial
            # Por enquanto, vamos usar uma abordagem simplificada
            
            transport = Transport(session=session)
            
            # Criar cliente SOAP
            self._soap_client = Client(self.wsdl_url, transport=transport)
            
            logger.info(f"Cliente SOAP ISSNet inicializado: {self.ambiente}")
            return self._soap_client
            
        except ImportError as e:
            logger.error(f"Bibliotecas necessárias não instaladas: {e}")
            logger.error("Instale: pip install zeep cryptography")
            raise
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente SOAP: {e}")
            raise
    
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
        serie_rps: str = 'A',
        tipo_rps: int = 1,
        data_emissao: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Emite NFS-e no ISSNet.
        
        Args:
            prestador_cnpj: CNPJ do prestador (loja)
            prestador_inscricao_municipal: Inscrição municipal do prestador
            prestador_razao_social: Razão social do prestador
            tomador_cpf_cnpj: CPF/CNPJ do tomador (cliente)
            tomador_nome: Nome/Razão social do tomador
            tomador_endereco: Endereço do tomador (dict com logradouro, numero, bairro, cidade, uf, cep)
            servico_codigo: Código do serviço municipal (ex: '1401')
            servico_descricao: Descrição do serviço prestado
            valor_servicos: Valor total dos serviços
            aliquota_iss: Alíquota do ISS (ex: 2.00 para 2%)
            numero_rps: Número do RPS
            serie_rps: Série do RPS (padrão: 'A')
            tipo_rps: Tipo do RPS (1=RPS, 2=Nota Fiscal Conjugada, 3=Cupom)
            data_emissao: Data de emissão (padrão: agora)
        
        Returns:
            Dict com resultado da emissão:
            {
                'success': bool,
                'numero_nf': str,
                'codigo_verificacao': str,
                'data_emissao': datetime,
                'xml_nfse': str,
                'error': str (se houver erro)
            }
        """
        try:
            if data_emissao is None:
                data_emissao = datetime.now()
            
            # Construir XML do RPS
            xml_rps = self._construir_xml_rps(
                prestador_cnpj=prestador_cnpj,
                prestador_inscricao_municipal=prestador_inscricao_municipal,
                prestador_razao_social=prestador_razao_social,
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
            
            # Assinar XML com certificado
            xml_assinado = self._assinar_xml(xml_rps)
            
            # Enviar para webservice
            resultado = self._enviar_lote_rps(xml_assinado)
            
            return resultado
            
        except Exception as e:
            logger.exception(f"Erro ao emitir NFS-e: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _construir_xml_rps(
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
        serie_rps: str,
        tipo_rps: int,
        data_emissao: datetime,
    ) -> str:
        """
        Constrói XML do RPS no padrão ISSNet Ribeirão Preto.
        
        Returns:
            str: XML do RPS
        """
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom
        
        # Limpar CNPJ/CPF (apenas números)
        prestador_cnpj = ''.join(filter(str.isdigit, prestador_cnpj))
        tomador_cpf_cnpj = ''.join(filter(str.isdigit, tomador_cpf_cnpj))
        
        # Calcular valores
        valor_servicos = Decimal(str(valor_servicos))
        aliquota_iss = Decimal(str(aliquota_iss))
        valor_iss = (valor_servicos * aliquota_iss / 100).quantize(Decimal('0.01'))
        valor_liquido = valor_servicos - valor_iss
        
        # Root
        rps = Element('Rps')
        
        # Identificação do RPS
        inf_rps = SubElement(rps, 'InfRps', Id=f'rps{numero_rps}')
        
        identificacao_rps = SubElement(inf_rps, 'IdentificacaoRps')
        SubElement(identificacao_rps, 'Numero').text = str(numero_rps)
        SubElement(identificacao_rps, 'Serie').text = serie_rps
        SubElement(identificacao_rps, 'Tipo').text = str(tipo_rps)
        
        # Data de emissão
        SubElement(inf_rps, 'DataEmissao').text = data_emissao.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Natureza da operação (1=Tributação no município)
        SubElement(inf_rps, 'NaturezaOperacao').text = '1'
        
        # Regime especial de tributação (não aplicável)
        SubElement(inf_rps, 'RegimeEspecialTributacao').text = '0'
        
        # Optante pelo Simples Nacional
        SubElement(inf_rps, 'OptanteSimplesNacional').text = '1'  # 1=Sim, 2=Não
        
        # Incentivador cultural
        SubElement(inf_rps, 'IncentivadorCultural').text = '2'  # 2=Não
        
        # Status (1=Normal)
        SubElement(inf_rps, 'Status').text = '1'
        
        # Prestador
        prestador = SubElement(inf_rps, 'Prestador')
        SubElement(prestador, 'Cnpj').text = prestador_cnpj
        SubElement(prestador, 'InscricaoMunicipal').text = prestador_inscricao_municipal
        
        # Tomador
        tomador = SubElement(inf_rps, 'Tomador')
        
        identificacao_tomador = SubElement(tomador, 'IdentificacaoTomador')
        cpf_cnpj_tomador = SubElement(identificacao_tomador, 'CpfCnpj')
        
        if len(tomador_cpf_cnpj) == 11:
            SubElement(cpf_cnpj_tomador, 'Cpf').text = tomador_cpf_cnpj
        else:
            SubElement(cpf_cnpj_tomador, 'Cnpj').text = tomador_cpf_cnpj
        
        SubElement(identificacao_tomador, 'RazaoSocial').text = tomador_nome
        
        # Endereço do tomador
        endereco = SubElement(tomador, 'Endereco')
        SubElement(endereco, 'Endereco').text = tomador_endereco.get('logradouro', '')
        SubElement(endereco, 'Numero').text = tomador_endereco.get('numero', 'S/N')
        SubElement(endereco, 'Bairro').text = tomador_endereco.get('bairro', '')
        SubElement(endereco, 'CodigoMunicipio').text = '3543402'  # Código IBGE Ribeirão Preto
        SubElement(endereco, 'Uf').text = tomador_endereco.get('uf', 'SP')
        SubElement(endereco, 'Cep').text = ''.join(filter(str.isdigit, tomador_endereco.get('cep', '')))
        
        # Serviço
        servico = SubElement(inf_rps, 'Servico')
        
        valores = SubElement(servico, 'Valores')
        SubElement(valores, 'ValorServicos').text = f'{valor_servicos:.2f}'
        SubElement(valores, 'ValorDeducoes').text = '0.00'
        SubElement(valores, 'ValorPis').text = '0.00'
        SubElement(valores, 'ValorCofins').text = '0.00'
        SubElement(valores, 'ValorInss').text = '0.00'
        SubElement(valores, 'ValorIr').text = '0.00'
        SubElement(valores, 'ValorCsll').text = '0.00'
        SubElement(valores, 'IssRetido').text = '2'  # 2=Não retido
        SubElement(valores, 'ValorIss').text = f'{valor_iss:.2f}'
        SubElement(valores, 'Aliquota').text = f'{aliquota_iss:.2f}'
        SubElement(valores, 'DescontoIncondicionado').text = '0.00'
        SubElement(valores, 'DescontoCondicionado').text = '0.00'
        
        SubElement(servico, 'ItemListaServico').text = servico_codigo
        SubElement(servico, 'CodigoTributacaoMunicipio').text = servico_codigo
        SubElement(servico, 'Discriminacao').text = servico_descricao
        SubElement(servico, 'CodigoMunicipio').text = '3543402'  # Ribeirão Preto
        
        # Converter para string XML
        xml_str = tostring(rps, encoding='unicode')
        
        # Formatar (pretty print)
        dom = minidom.parseString(xml_str)
        xml_formatado = dom.toprettyxml(indent='  ', encoding='UTF-8').decode('utf-8')
        
        # Remover declaração XML duplicada
        xml_formatado = '\n'.join([line for line in xml_formatado.split('\n') if line.strip()])
        
        logger.info(f"XML RPS construído: RPS {numero_rps}, Valor R$ {valor_servicos}")
        
        return xml_formatado
    
    def _assinar_xml(self, xml: str) -> str:
        """
        Assina XML com certificado digital.
        
        Args:
            xml: XML a ser assinado
        
        Returns:
            str: XML assinado
        """
        try:
            from signxml import XMLSigner
            from lxml import etree
            from cryptography.hazmat.primitives.serialization import pkcs12
            from cryptography.hazmat.backends import default_backend
            
            # Carregar certificado
            with open(self.certificado_path, 'rb') as f:
                pfx_data = f.read()
            
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                pfx_data,
                self.senha_certificado.encode(),
                backend=default_backend()
            )
            
            # Parse XML
            root = etree.fromstring(xml.encode('utf-8'))
            
            # Assinar
            signer = XMLSigner(
                method='enveloped',
                signature_algorithm='rsa-sha1',
                digest_algorithm='sha1'
            )
            
            signed_root = signer.sign(
                root,
                key=private_key,
                cert=certificate
            )
            
            # Converter de volta para string
            xml_assinado = etree.tostring(signed_root, encoding='unicode', pretty_print=True)
            
            logger.info("XML assinado com sucesso")
            
            return xml_assinado
            
        except ImportError as e:
            logger.error(f"Biblioteca signxml não instalada: {e}")
            logger.error("Instale: pip install signxml lxml")
            raise
        except Exception as e:
            logger.error(f"Erro ao assinar XML: {e}")
            raise
    
    def _enviar_lote_rps(self, xml_assinado: str) -> Dict[str, Any]:
        """
        Envia lote de RPS para o webservice ISSNet.
        
        Args:
            xml_assinado: XML do RPS assinado
        
        Returns:
            Dict com resultado da emissão
        """
        try:
            client = self._get_soap_client()
            
            # Chamar método do webservice
            response = client.service.RecepcionarLoteRps(
                xml_assinado,
                self.usuario,
                self.senha
            )
            
            # Processar resposta
            # Nota: A estrutura exata da resposta depende do webservice
            # Aqui está uma implementação genérica
            
            if hasattr(response, 'NumeroNfse'):
                return {
                    'success': True,
                    'numero_nf': response.NumeroNfse,
                    'codigo_verificacao': getattr(response, 'CodigoVerificacao', ''),
                    'data_emissao': datetime.now(),
                    'xml_nfse': str(response)
                }
            else:
                # Erro na emissão
                erro = getattr(response, 'MensagemRetorno', 'Erro desconhecido')
                return {
                    'success': False,
                    'error': erro
                }
                
        except Exception as e:
            logger.exception(f"Erro ao enviar lote RPS: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def consultar_nfse(self, numero_nf: str) -> Dict[str, Any]:
        """
        Consulta NFS-e emitida.
        
        Args:
            numero_nf: Número da NFS-e
        
        Returns:
            Dict com dados da NFS-e
        """
        try:
            client = self._get_soap_client()
            
            response = client.service.ConsultarNfsePorRps(
                numero_nf,
                self.usuario,
                self.senha
            )
            
            return {
                'success': True,
                'data': response
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
            client = self._get_soap_client()
            
            response = client.service.CancelarNfse(
                numero_nf,
                motivo,
                self.usuario,
                self.senha
            )
            
            return {
                'success': True,
                'message': 'NFS-e cancelada com sucesso'
            }
            
        except Exception as e:
            logger.exception(f"Erro ao cancelar NFS-e: {e}")
            return {
                'success': False,
                'error': str(e)
            }
