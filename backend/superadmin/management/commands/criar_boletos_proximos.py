"""
Comando para criar e enviar boletos 10 dias antes do vencimento

Cria boletos no Asaas e envia por email para lojas que têm vencimento em 10 dias.

Uso:
    python manage.py criar_boletos_proximos
    python manage.py criar_boletos_proximos --dry-run
    python manage.py criar_boletos_proximos --dias 10
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import timedelta, datetime
from superadmin.models import FinanceiroLoja
from asaas_integration.models import LojaAssinatura, AsaasPayment
from asaas_integration.client import AsaasPaymentService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cria e envia boletos por email X dias antes do vencimento'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula a execução sem criar boletos ou enviar emails'
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=10,
            help='Dias antes do vencimento para criar boleto (padrão: 10)'
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        dias_antes = options.get('dias', 10)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Modo DRY-RUN ativado - nenhum boleto será criado\n'))
        
        self.stdout.write(self.style.SUCCESS(f'💳 Criando boletos {dias_antes} dias antes do vencimento...'))
        
        hoje = timezone.now().date()
        data_alvo = hoje + timedelta(days=dias_antes)
        
        self.stdout.write(f'   Data de hoje: {hoje}')
        self.stdout.write(f'   Data alvo (vencimentos): {data_alvo}\n')
        
        # Buscar lojas com vencimento na data alvo e status ativo
        financeiros = FinanceiroLoja.objects.filter(
            data_proxima_cobranca=data_alvo,
            status_pagamento='ativo'
        ).select_related('loja', 'loja__owner', 'loja__plano')
        
        total = financeiros.count()
        criados = 0
        erros = 0
        
        self.stdout.write(f'📊 {total} loja(s) com vencimento em {data_alvo}\n')
        
        for financeiro in financeiros:
            loja = financeiro.loja
            owner = loja.owner
            
            if not owner or not owner.email:
                self.stdout.write(self.style.WARNING(f'   ⚠️ Loja {loja.nome}: sem email do proprietário'))
                erros += 1
                continue
            
            self.stdout.write(f'   💳 Loja: {loja.nome}')
            self.stdout.write(f'      Email: {owner.email}')
            self.stdout.write(f'      Vencimento: {financeiro.data_proxima_cobranca}')
            
            valor = loja.plano.preco_mensal if loja.tipo_assinatura == 'mensal' else loja.plano.preco_anual
            self.stdout.write(f'      Valor: R$ {valor}')
            
            if not dry_run:
                try:
                    # Criar boleto
                    resultado = self._criar_boleto(loja, financeiro, data_alvo)
                    
                    if resultado['success']:
                        criados += 1
                        self.stdout.write(self.style.SUCCESS(f'      ✅ Boleto criado: {resultado["payment_id"]}'))
                        
                        # Enviar email
                        email_enviado = self._enviar_email_boleto(
                            loja, 
                            financeiro, 
                            owner.email,
                            resultado['boleto_url'],
                            resultado['pix_copy_paste']
                        )
                        
                        if email_enviado:
                            self.stdout.write(self.style.SUCCESS(f'      📧 Email enviado'))
                        else:
                            self.stdout.write(self.style.WARNING(f'      ⚠️ Erro ao enviar email'))
                    else:
                        erros += 1
                        self.stdout.write(self.style.ERROR(f'      ❌ Erro: {resultado["error"]}'))
                        
                except Exception as e:
                    erros += 1
                    self.stdout.write(self.style.ERROR(f'      ❌ Erro: {e}'))
                    logger.error(f"Erro ao criar boleto para {loja.nome}: {e}")
            else:
                self.stdout.write(self.style.WARNING(f'      🔍 Boleto não criado (dry-run)'))
            
            self.stdout.write('')  # Linha em branco
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('✅ Processamento concluído!'))
        self.stdout.write(self.style.SUCCESS(f'   Total de lojas: {total}'))
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'   Boletos criados: {criados}'))
            if erros > 0:
                self.stdout.write(self.style.ERROR(f'   Erros: {erros}'))
        else:
            self.stdout.write(self.style.WARNING(f'   💡 Execute sem --dry-run para criar os boletos'))
        self.stdout.write(self.style.SUCCESS('='*60))
    
    def _criar_boleto(self, loja, financeiro, data_vencimento):
        """Cria boleto no Asaas"""
        try:
            # Buscar assinatura
            loja_assinatura = LojaAssinatura.objects.get(loja_slug=loja.slug)
            
            # Verificar se já existe cobrança para essa data
            cobranca_existente = AsaasPayment.objects.filter(
                customer=loja_assinatura.asaas_customer,
                due_date=data_vencimento,
                status__in=['PENDING', 'RECEIVED', 'CONFIRMED']
            ).exists()
            
            if cobranca_existente:
                return {
                    'success': False,
                    'error': 'Já existe cobrança para esta data'
                }
            
            # Criar boleto no Asaas
            asaas_service = AsaasPaymentService()
            
            loja_data = {
                'nome': loja.nome,
                'slug': loja.slug,
                'email': loja.owner.email,
                'cpf_cnpj': loja.cpf_cnpj or '000.000.000-00',
                'telefone': getattr(loja.owner, 'telefone', ''),
                'endereco': loja.logradouro or '',
                'numero': loja.numero or '',
                'complemento': loja.complemento or '',
                'bairro': loja.bairro or '',
                'cidade': loja.cidade or '',
                'estado': loja.uf or '',
                'cep': loja.cep or '',
            }
            
            valor_plano = loja.plano.preco_anual if loja.tipo_assinatura == 'anual' else loja.plano.preco_mensal
            plano_data = {
                'nome': f"{loja.plano.nome} ({loja.get_tipo_assinatura_display()})",
                'preco': valor_plano
            }
            
            due_date_str = data_vencimento.strftime('%Y-%m-%d')
            result = asaas_service.create_loja_subscription_payment(
                loja_data, 
                plano_data, 
                due_date=due_date_str,
                customer_id=loja_assinatura.asaas_customer.asaas_id
            )
            
            if result['success']:
                # Criar pagamento no banco local
                new_payment = AsaasPayment.objects.create(
                    asaas_id=result['payment_id'],
                    customer=loja_assinatura.asaas_customer,
                    external_reference=f"loja_{loja.slug}_assinatura_{data_vencimento.strftime('%Y%m')}",
                    billing_type='BOLETO',
                    status=result['status'],
                    value=result['value'],
                    due_date=datetime.strptime(result['due_date'], '%Y-%m-%d').date(),
                    invoice_url=result['payment_url'],
                    bank_slip_url=result['boleto_url'],
                    pix_qr_code=result['pix_qr_code'],
                    pix_copy_paste=result['pix_copy_paste'],
                    description=f"Assinatura {plano_data['nome']} - Loja {loja.nome} - {data_vencimento.strftime('%m/%Y')}",
                    raw_data=result['raw_payment']
                )
                
                # Atualizar assinatura
                loja_assinatura.current_payment = new_payment
                loja_assinatura.save()
                
                # Atualizar financeiro
                financeiro.asaas_customer_id = loja_assinatura.asaas_customer.asaas_id
                financeiro.asaas_payment_id = result['payment_id']
                financeiro.boleto_url = result['boleto_url']
                financeiro.boleto_pdf_url = result['boleto_url']
                financeiro.pix_qr_code = result['pix_qr_code']
                financeiro.pix_copy_paste = result['pix_copy_paste']
                financeiro.save()
                
                # Criar registro em PagamentoLoja
                from superadmin.models import PagamentoLoja
                referencia_mes = data_vencimento.replace(day=1)
                
                PagamentoLoja.objects.create(
                    loja=loja,
                    financeiro=financeiro,
                    provedor_boleto='asaas',
                    asaas_payment_id=result['payment_id'],
                    valor=result['value'],
                    status='pendente',
                    data_vencimento=data_vencimento,
                    referencia_mes=referencia_mes,
                    forma_pagamento='boleto',
                    boleto_url=result['boleto_url'],
                    boleto_pdf_url=result['boleto_url'],
                    pix_copy_paste=result['pix_copy_paste']
                )
                
                logger.info(f"Boleto criado para {loja.nome}: {result['payment_id']}")
                
                return {
                    'success': True,
                    'payment_id': result['payment_id'],
                    'boleto_url': result['boleto_url'],
                    'pix_copy_paste': result['pix_copy_paste']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Erro desconhecido')
                }
                
        except Exception as e:
            logger.error(f"Erro ao criar boleto: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _enviar_email_boleto(self, loja, financeiro, email_destino, boleto_url, pix_copy_paste):
        """Envia email com o boleto"""
        try:
            valor = loja.plano.preco_mensal if loja.tipo_assinatura == 'mensal' else loja.plano.preco_anual
            tipo_assinatura = loja.get_tipo_assinatura_display()
            
            assunto = f'Boleto de Assinatura - {loja.nome}'
            
            corpo = f"""
Olá,

Seu boleto de assinatura está disponível para pagamento.

Dados da assinatura:
- Loja: {loja.nome}
- Plano: {loja.plano.nome} ({tipo_assinatura})
- Valor: R$ {valor:.2f}
- Vencimento: {financeiro.data_proxima_cobranca.strftime('%d/%m/%Y')}

Acesse o boleto: {boleto_url}

"""
            
            if pix_copy_paste:
                corpo += f"""
Você também pode pagar via PIX:
{pix_copy_paste}

"""
            
            corpo += """
Em caso de dúvidas, entre em contato com o suporte.

Atenciosamente,
Equipe LWK Sistemas
"""
            
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
            
            msg = EmailMessage(
                subject=assunto,
                body=corpo,
                from_email=from_email,
                to=[email_destino]
            )
            msg.send(fail_silently=False)
            
            logger.info(f"Email de boleto enviado para {loja.nome} ({email_destino})")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
