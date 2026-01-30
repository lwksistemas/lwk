"""
Cliente para integração com API do Asaas
Gera boletos e PIX para cobrança de assinaturas das lojas
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AsaasClient:
    """Cliente para API do Asaas"""
    
    def __init__(self, api_key: str = None, sandbox: bool = None):
        self.api_key = api_key or getattr(settings, 'ASAAS_API_KEY', '')
        
        # Auto-detectar sandbox se não especificado
        if sandbox is None:
            # Detectar automaticamente baseado na chave
            self.sandbox = 'hmlg' in self.api_key if self.api_key else True
        else:
            self.sandbox = sandbox
        
        if self.sandbox:
            self.base_url = 'https://sandbox.asaas.com/api/v3'
        else:
            self.base_url = 'https://api.asaas.com/v3'
        
        self.headers = {
            'access_token': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'LWK Sistemas/1.0'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Faz requisição para API do Asaas"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.info(f"Asaas API Request: {method} {url}")
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            logger.info(f"Asaas API Response: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"Erro na API Asaas: {response.status_code} - {response.text}")
                response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para Asaas: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar resposta JSON: {e}")
            raise
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um cliente no Asaas"""
        endpoint = 'customers'
        return self._make_request('POST', endpoint, customer_data)
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Busca um cliente no Asaas"""
        endpoint = f'customers/{customer_id}'
        return self._make_request('GET', endpoint)
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria uma cobrança no Asaas"""
        endpoint = 'payments'
        return self._make_request('POST', endpoint, payment_data)
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """Busca uma cobrança no Asaas"""
        endpoint = f'payments/{payment_id}'
        return self._make_request('GET', endpoint)
    
    def delete_payment(self, payment_id: str) -> Dict[str, Any]:
        """Cancela/exclui uma cobrança no Asaas"""
        endpoint = f'payments/{payment_id}'
        return self._make_request('DELETE', endpoint)
    
    def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        """Exclui um cliente no Asaas"""
        endpoint = f'customers/{customer_id}'
        return self._make_request('DELETE', endpoint)
    
    def list_customer_payments(self, customer_id: str) -> Dict[str, Any]:
        """Lista todos os pagamentos de um cliente"""
        endpoint = f'payments'
        params = {'customer': customer_id}
        return self._make_request('GET', endpoint, params)
    
    def list_payments(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Lista todos os pagamentos"""
        endpoint = 'payments'
        params = {'limit': limit, 'offset': offset}
        return self._make_request('GET', endpoint, params)
    
    def list_customers(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Lista todos os clientes"""
        endpoint = 'customers'
        params = {'limit': limit, 'offset': offset}
        return self._make_request('GET', endpoint, params)
    
    def get_payment_pdf(self, payment_id: str) -> bytes:
        """Baixa o PDF do boleto"""
        # Tentar múltiplas URLs para download do PDF
        urls_to_try = [
            f"{self.base_url}/payments/{payment_id}/identificationField",
            f"{self.base_url}/payments/{payment_id}/bankSlipPdf",
            f"https://sandbox.asaas.com/b/pdf/{payment_id}" if self.sandbox else f"https://asaas.com/b/pdf/{payment_id}"
        ]
        
        for url in urls_to_try:
            try:
                logger.info(f"Tentando baixar PDF de: {url}")
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    # Verificar se o conteúdo é realmente um PDF
                    content_type = response.headers.get('content-type', '')
                    content = response.content
                    
                    # Verificar se é PDF pelo content-type ou pelos primeiros bytes
                    if ('application/pdf' in content_type.lower() or 
                        (content and content[:4] == b'%PDF')):
                        logger.info(f"PDF baixado com sucesso de: {url}")
                        return content
                    else:
                        logger.warning(f"Conteúdo retornado não é PDF: {content_type}")
                        continue
                else:
                    logger.warning(f"Erro HTTP {response.status_code} ao baixar de: {url}")
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro ao baixar PDF de {url}: {e}")
                continue
        
        # Se chegou aqui, nenhuma URL funcionou
        raise Exception("Não foi possível baixar o PDF do boleto de nenhuma URL")
    
    def get_pix_qr_code(self, payment_id: str) -> Dict[str, Any]:
        """Busca dados do QR Code PIX"""
        endpoint = f'payments/{payment_id}/pixQrCode'
        return self._make_request('GET', endpoint)

    # ---------- Notas Fiscais (INVOICE) ----------
    # Requer permissão INVOICE:WRITE na chave da API Asaas

    def create_invoice(
        self,
        payment_id: str,
        service_description: str,
        value: float,
        effective_date: str,
        municipal_service_code: Optional[str] = None,
        municipal_service_name: Optional[str] = None,
        municipal_service_id: Optional[str] = None,
        observations: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Agenda uma nota fiscal vinculada a uma cobrança (payment).
        Campos municipais dependem da prefeitura da conta Asaas (LWK).
        """
        endpoint = 'invoices'
        data = {
            'payment': payment_id,
            'serviceDescription': service_description,
            'value': value,
            'effectiveDate': effective_date,
        }
        if municipal_service_id:
            data['municipalServiceId'] = municipal_service_id
        if municipal_service_code:
            data['municipalServiceCode'] = municipal_service_code
        if municipal_service_name:
            data['municipalServiceName'] = municipal_service_name
        if observations:
            data['observations'] = observations
        return self._make_request('POST', endpoint, data)

    def authorize_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Emitir (autorizar) uma nota fiscal já agendada."""
        endpoint = f'invoices/{invoice_id}/authorize'
        return self._make_request('POST', endpoint, {})

    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Busca uma nota fiscal (para obter link do PDF se disponível)."""
        endpoint = f'invoices/{invoice_id}'
        return self._make_request('GET', endpoint)

class AsaasPaymentService:
    """Serviço para gerenciar pagamentos via Asaas"""
    
    def __init__(self):
        # Obter configuração do banco de dados
        try:
            from .models import AsaasConfig
            config = AsaasConfig.get_config()
            self.client = AsaasClient(api_key=config.api_key, sandbox=config.sandbox)
        except Exception as e:
            logger.error(f"Erro ao obter configuração Asaas: {e}")
            # Fallback para configuração vazia
            self.client = AsaasClient(api_key='', sandbox=True)
    
    def create_loja_subscription_payment(self, loja_data: Dict[str, Any], plano_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria cobrança para assinatura de loja
        
        Args:
            loja_data: Dados da loja (nome, email, cpf_cnpj, etc)
            plano_data: Dados do plano (valor, nome, etc)
        
        Returns:
            Dict com dados da cobrança criada
        """
        try:
            # 1. Criar ou buscar cliente
            customer_data = {
                'name': loja_data['nome'],
                'email': loja_data['email'],
                'cpfCnpj': loja_data['cpf_cnpj'],
                'phone': loja_data.get('telefone', ''),
                'address': loja_data.get('endereco', ''),
                'addressNumber': loja_data.get('numero', ''),
                'complement': loja_data.get('complemento', ''),
                'province': loja_data.get('bairro', ''),
                'city': loja_data.get('cidade', ''),
                'state': loja_data.get('estado', ''),
                'postalCode': loja_data.get('cep', ''),
                'externalReference': f"loja_{loja_data['slug']}"
            }
            
            logger.info(f"Criando cliente Asaas para loja: {loja_data['nome']}")
            customer = self.client.create_customer(customer_data)
            customer_id = customer['id']
            
            # 2. Criar cobrança
            due_date = datetime.now() + timedelta(days=7)  # Vencimento em 7 dias
            
            payment_data = {
                'customer': customer_id,
                'billingType': 'BOLETO',  # Boleto com PIX
                'value': float(plano_data['preco']),
                'dueDate': due_date.strftime('%Y-%m-%d'),
                'description': f"Assinatura {plano_data['nome']} - Loja {loja_data['nome']}",
                'externalReference': f"loja_{loja_data['slug']}_assinatura",
                'postalService': False,
                'split': []
            }
            
            logger.info(f"Criando cobrança Asaas: R$ {plano_data['preco']}")
            payment = self.client.create_payment(payment_data)
            
            # 3. Buscar dados do PIX (se disponível)
            pix_data = None
            try:
                pix_data = self.client.get_pix_qr_code(payment['id'])
            except Exception as e:
                logger.warning(f"PIX não disponível para esta cobrança: {e}")
            
            return {
                'success': True,
                'customer_id': customer_id,
                'payment_id': payment['id'],
                'payment_url': payment.get('invoiceUrl', ''),
                'boleto_url': payment.get('bankSlipUrl', ''),
                'due_date': payment['dueDate'],
                'value': payment['value'],
                'status': payment['status'],
                'pix_qr_code': pix_data.get('qrCode', '') if pix_data else '',
                'pix_copy_paste': pix_data.get('payload', '') if pix_data else '',
                'raw_payment': payment,
                'raw_customer': customer
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar cobrança Asaas: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Consulta status de um pagamento"""
        try:
            payment = self.client.get_payment(payment_id)
            return {
                'success': True,
                'payment_id': payment_id,
                'status': payment['status'],
                'value': payment['value'],
                'due_date': payment['dueDate'],
                'payment_date': payment.get('paymentDate'),
                'raw_payment': payment
            }
        except Exception as e:
            logger.error(f"Erro ao consultar pagamento: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_boleto_pdf(self, payment_id: str) -> bytes:
        """Baixa PDF do boleto"""
        try:
            return self.client.get_payment_pdf(payment_id)
        except Exception as e:
            logger.error(f"Erro ao baixar PDF: {e}")
            raise