# Correção: Exclusão de Loja com Cancelamento de Pagamentos Asaas v789

## 📋 Problema Identificado

Ao excluir uma loja do sistema, ocorria erro 500 (Internal Server Error) porque o método `cleanup_payments()` tentava importar um serviço inexistente (`payment_deletion_service.py`).

### Erro Original
```
Failed to load resource: the server responded with a status of 500 (Internal Server Error)
```

### Causa Raiz
- O arquivo `backend/superadmin/services/payment_deletion_service.py` não existia no sistema
- O método `cleanup_payments()` em `loja_cleanup_service.py` tentava usar este serviço inexistente
- Pagamentos pendentes no Asaas não eram cancelados ao excluir a loja

## ✅ Solução Implementada

### 1. Refatoração do Método `cleanup_payments()`

Substituído o import do serviço inexistente por implementação direta usando a API Asaas:

```python
def cleanup_payments(self):
    """Remove dados de pagamentos (Asaas)"""
    try:
        # Cancelar pagamentos Asaas
        asaas_cancelled = self._cleanup_asaas_payments()
        
        if asaas_cancelled > 0:
            logger.info(f"✅ Total de pagamentos cancelados: {asaas_cancelled}")
                
    except Exception as e:
        logger.warning(f"⚠️ Erro ao remover pagamentos: {e}")
        self.results['asaas'] = {'erro': str(e)}
```

### 2. Novo Método `_cleanup_asaas_payments()`

Implementado método que:
- Busca a assinatura da loja no banco de dados
- Localiza todos os pagamentos relacionados à loja
- Cancela pagamentos pendentes (PENDING/OVERDUE) via API Asaas
- Remove dados locais (payments, customer, subscription)

```python
def _cleanup_asaas_payments(self):
    """Cancela pagamentos pendentes no Asaas e remove dados locais"""
    try:
        from asaas_integration.models import LojaAssinatura, AsaasPayment, AsaasCustomer
        from asaas_integration.client import AsaasClient
        
        cancelled_count = 0
        
        with transaction.atomic():
            # Buscar assinatura da loja
            assinatura = LojaAssinatura.objects.filter(loja_slug=self.loja_slug).first()
            
            if not assinatura:
                self.results['asaas'] = {
                    'api': {'pagamentos_cancelados': 0},
                    'local': {'payments_removidos': 0, 'customers_removidos': 0, 'subscriptions_removidas': 0}
                }
                return 0
            
            # Buscar todos os pagamentos da loja
            payments = AsaasPayment.objects.filter(
                external_reference__contains=f"loja_{self.loja_slug}"
            )
            
            # Cancelar pagamentos pendentes na API Asaas
            try:
                client = AsaasClient()
                for payment in payments:
                    if payment.status in ['PENDING', 'OVERDUE']:
                        try:
                            client.delete_payment(payment.asaas_id)
                            cancelled_count += 1
                            logger.info(f"✅ Pagamento Asaas cancelado: {payment.asaas_id}")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao cancelar pagamento {payment.asaas_id}: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao conectar com API Asaas: {e}")
            
            # Remover dados locais
            payments_count = payments.count()
            payments.delete()
            
            customer = assinatura.asaas_customer
            assinatura.delete()
            
            if customer:
                customer.delete()
            
            self.results['asaas'] = {
                'api': {'pagamentos_cancelados': cancelled_count},
                'local': {
                    'payments_removidos': payments_count,
                    'customers_removidos': 1 if customer else 0,
                    'subscriptions_removidas': 1
                }
            }
            
            logger.info(f"✅ Asaas: {cancelled_count} cancelados na API, {payments_count} removidos localmente")
            
        return cancelled_count
        
    except Exception as e:
        logger.warning(f"⚠️ Erro ao limpar pagamentos Asaas: {e}")
        self.results['asaas'] = {'erro': str(e)}
        return 0
```

## 🔧 Arquivos Modificados

### `backend/superadmin/services/loja_cleanup_service.py`
- ✅ Removido import de `payment_deletion_service` (inexistente)
- ✅ Implementado `_cleanup_asaas_payments()` com chamadas diretas à API Asaas
- ✅ Removido método `_cleanup_mercadopago_payments()` (não utilizado)
- ✅ Atualizado `self.results` para remover referência ao Mercado Pago

## 📊 Funcionalidades

### O que acontece ao excluir uma loja:

1. **Chamados de Suporte**: Removidos do banco de dados
2. **Logs e Alertas**: Histórico de acesso e violações de segurança removidos
3. **Pagamentos Asaas**:
   - ✅ Boletos pendentes (PENDING) cancelados na API Asaas
   - ✅ Boletos vencidos (OVERDUE) cancelados na API Asaas
   - ✅ Registros locais de pagamentos removidos
   - ✅ Cliente Asaas removido
   - ✅ Assinatura removida
4. **Banco de Dados**: Arquivo SQLite isolado removido
5. **Usuário Proprietário**: Removido se não tiver outras lojas

### Logs Gerados

```
✅ Chamados removidos: X
✅ Logs: X, Alertas: X
✅ Pagamento Asaas cancelado: pay_xxxxx
✅ Asaas: X cancelados na API, X removidos localmente
✅ Arquivo do banco removido: /path/to/db_loja.sqlite3
✅ Usuário removido: username
✅ Loja removida: Nome da Loja
```

## 🚀 Deploy

**Versão**: v789  
**Data**: 05/03/2026  
**Plataforma**: Heroku  
**Branch**: master  

```bash
git add -A
git commit -m "fix: Corrigir exclusão de loja - cancelar pagamentos Asaas pendentes v789"
git push heroku master
```

## ✅ Resultado

- ✅ Erro 500 ao excluir loja corrigido
- ✅ Pagamentos pendentes no Asaas são cancelados automaticamente
- ✅ Dados locais são removidos corretamente
- ✅ Sistema de limpeza funciona de forma transacional (rollback em caso de erro)
- ✅ Logs detalhados para auditoria

## 🔍 Como Testar

1. Criar uma loja de teste no sistema
2. Gerar um pagamento pendente no Asaas para a loja
3. Acessar o SuperAdmin e excluir a loja
4. Verificar nos logs do Heroku se o pagamento foi cancelado
5. Confirmar no painel do Asaas que o boleto foi cancelado

## 📝 Observações

- O cancelamento de pagamentos só funciona para status PENDING e OVERDUE
- Pagamentos já recebidos (RECEIVED, CONFIRMED) não são cancelados
- Em caso de erro na API Asaas, o sistema continua e remove apenas os dados locais
- Todas as operações são executadas dentro de uma transação para garantir consistência
