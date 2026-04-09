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
    
    def update_customer(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza um cliente no Asaas"""
        endpoint = f'customers/{customer_id}'
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
    
    # ✅ NOVO: Métodos para cartão de crédito
    
    def create_payment_link(self, payment_id: str, name: str = None, callback_url: str = None) -> Dict[str, Any]:
        """
        Cria link de checkout para cobrança existente
        Permite que cliente cadastre cartão e pague online
        
        Args:
            payment_id: ID da cobrança no Asaas
            name: Nome do link (não usado neste endpoint)
            callback_url: URL de retorno após pagamento (opcional)
        
        Returns:
            dict com url do link de pagamento
        """
        # Para cobranças específicas, usamos o endpoint de checkout
        endpoint = f'payments/{payment_id}/identificationField'
        
        # Primeiro, obter os dados da cobrança
        payment_data = self._make_request('GET', f'payments/{payment_id}')
        
        # O link de checkout já vem na resposta da cobrança
        if payment_data.get('invoiceUrl'):
            return {
                'url': payment_data.get('invoiceUrl'),
                'id': payment_id
            }
        
        # Se não tiver, retornar erro
        return {
            'error': 'Link de pagamento não disponível para esta cobrança'
        }
    
    def tokenize_credit_card(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tokeniza cartão de crédito para cobranças recorrentes
        
        Args:
            card_data: {
                'customer': customer_id,
                'creditCard': {
                    'holderName': 'Nome no cartão',
                    'number': '5162306219378829',
                    'expiryMonth': '05',
                    'expiryYear': '2024',
                    'ccv': '318'
                },
                'creditCardHolderInfo': {
                    'name': 'Nome completo',
                    'email': 'email@example.com',
                    'cpfCnpj': '00000000000',
                    'postalCode': '00000000',
                    'addressNumber': '123',
                    'phone': '11999999999'
                }
            }
        
        Returns:
            dict com creditCardToken
        """
        endpoint = 'creditCard/tokenize'
        return self._make_request('POST', endpoint, card_data)
    
    def charge_credit_card(
        self, 
        customer_id: str, 
        value: float, 
        credit_card_token: str,
        description: str = None,
        due_date: str = None
    ) -> Dict[str, Any]:
        """
        Cria cobrança no cartão de crédito tokenizado
        
        Args:
            customer_id: ID do cliente no Asaas
            value: Valor da cobrança
            credit_card_token: Token do cartão tokenizado
            description: Descrição da cobrança
            due_date: Data de vencimento (YYYY-MM-DD)
        
        Returns:
            dict com dados da cobrança
        """
        endpoint = 'payments'
        data = {
            'customer': customer_id,
            'billingType': 'CREDIT_CARD',
            'value': value,
            'dueDate': due_date or (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'creditCard': {
                'creditCardToken': credit_card_token
            }
        }
        
        if description:
            data['description'] = description
        
        return self._make_request('POST', endpoint, data)
    
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
        """Baixa o PDF do boleto via bankSlipUrl da API ou URLs alternativas."""
        urls_to_try = []

        # 1. Obter bankSlipUrl da API (formato correto segundo documentação Asaas)
        try:
            payment = self.get_payment(payment_id)
            bank_slip_url = payment.get('bankSlipUrl')
            if bank_slip_url:
                urls_to_try.append(bank_slip_url)  # URL pública do boleto
        except Exception as e:
            logger.warning(f"Erro ao obter payment para bankSlipUrl: {e}")

        # 2. URLs alternativas b/pdf (sandbox usa ID sem prefixo pay_ em alguns casos)
        id_sem_prefixo = payment_id.replace('pay_', '', 1) if payment_id.startswith('pay_') else payment_id
        base_b_pdf = 'https://sandbox.asaas.com' if self.sandbox else 'https://www.asaas.com'
        urls_to_try.append(f"{base_b_pdf}/b/pdf/{id_sem_prefixo}")
        urls_to_try.append(f"{base_b_pdf}/b/pdf/{payment_id}")

        for url in urls_to_try:
            try:
                logger.info(f"Tentando baixar PDF de: {url}")
                # URLs públicas (bankSlipUrl, b/pdf) — User-Agent browser-like para evitar bloqueio
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/pdf,*/*',
                }
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    content = response.content
                    if ('application/pdf' in content_type.lower() or
                            (content and len(content) >= 4 and content[:4] == b'%PDF')):
                        logger.info(f"PDF baixado com sucesso de: {url}")
                        return content
                    logger.warning(f"Conteúdo retornado não é PDF: {content_type}")
                else:
                    logger.warning(f"Erro HTTP {response.status_code} ao baixar de: {url}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro ao baixar PDF de {url}: {e}")

        raise Exception("Não foi possível baixar o PDF do boleto de nenhuma URL")
    
    def get_pix_qr_code(self, payment_id: str) -> Dict[str, Any]:
        """Busca dados do QR Code PIX"""
        endpoint = f'payments/{payment_id}/pixQrCode'
        return self._make_request('GET', endpoint)

    def receive_payment_in_cash(
        self,
        payment_id: str,
        value: float,
        payment_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Registra recebimento em dinheiro da cobrança (permite seguir com NFS-e sem liquidação bancária).
        POST /v3/payments/{id}/receiveInCash
        """
        from datetime import date
        if payment_date is None:
            payment_date = date.today().isoformat()
        endpoint = f'payments/{payment_id}/receiveInCash'
        payload = {
            'paymentDate': payment_date,
            'value': float(value),
            'notifyCustomer': False,
        }
        return self._make_request('POST', endpoint, payload)

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
        iss_aliquota: Optional[float] = None,
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
        
        # Alíquota ISS (prefeitura / configuração da loja)
        iss_pct = float(iss_aliquota) if iss_aliquota is not None else 2.0
        data['taxes'] = {
            'retainIss': False,
            'iss': iss_pct,
            'cofins': 0.0,
            'csll': 0.0,
            'inss': 0.0,
            'ir': 0.0,
            'pis': 0.0,
        }
        
        return self._make_request('POST', endpoint, data)

    def authorize_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Emitir (autorizar) uma nota fiscal já agendada."""
        endpoint = f'invoices/{invoice_id}/authorize'
        return self._make_request('POST', endpoint, {})

    def cancel_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Cancela uma nota fiscal agendada ou emitida."""
        endpoint = f'invoices/{invoice_id}'
        return self._make_request('DELETE', endpoint)

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
    
    def create_loja_subscription_payment(self, loja_data: Dict[str, Any], plano_data: Dict[str, Any], due_date: str = None, customer_id: str = None) -> Dict[str, Any]:
        """
        Cria cobrança para assinatura de loja
        
        Args:
            loja_data: Dados da loja (nome, email, cpf_cnpj, etc)
            plano_data: Dados do plano (valor, nome, etc)
            due_date: Data de vencimento no formato YYYY-MM-DD (opcional, padrão: +7 dias)
            customer_id: ID do customer existente no Asaas (opcional, se não fornecido cria novo)
        
        Returns:
            Dict com dados da cobrança criada
        """
        try:
            # 1. Usar customer existente ou criar novo
            if customer_id:
                logger.info(f"Usando customer existente: {customer_id}")
                # Buscar dados do customer para retornar
                try:
                    customer = self.client.get_customer(customer_id)
                except:
                    # Se não conseguir buscar, usar o ID fornecido mesmo assim
                    customer = {'id': customer_id}
            else:
                # Criar novo customer
                # ✅ CORREÇÃO v1328: Remover formatação do CEP (apenas dígitos)
                cep_raw = loja_data.get('cep', '')
                cep_limpo = ''.join(c for c in cep_raw if c.isdigit())
                
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
                    'postalCode': cep_limpo,  # CEP sem formatação (apenas dígitos)
                    'externalReference': f"loja_{loja_data['slug']}"
                }
                
                logger.info(f"Criando cliente Asaas para loja: {loja_data['nome']}")
                customer = self.client.create_customer(customer_data)
            
            customer_id = customer['id']
            
            # 2. Criar cobrança
            # Usar data fornecida ou calcular +7 dias
            if due_date:
                payment_due_date = due_date
            else:
                payment_due_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            payment_data = {
                'customer': customer_id,
                'billingType': 'BOLETO',  # Boleto com PIX
                'value': float(plano_data['preco']),
                'dueDate': payment_due_date,
                'description': f"Assinatura {plano_data['nome']} - Loja {loja_data['nome']}",
                'externalReference': f"loja_{loja_data['slug']}_assinatura",
                'postalService': False,
                'split': []
            }
            
            logger.info(f"Criando cobrança Asaas: R$ {plano_data['preco']} - Vencimento: {payment_due_date}")
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