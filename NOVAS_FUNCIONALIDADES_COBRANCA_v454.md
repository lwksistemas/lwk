# Novas Funcionalidades de Cobrança - v454

## 🎯 Objetivo
Adicionar funcionalidades de **cobrança manual** e **exclusão de cobrança** no sistema financeiro.

## ✅ Funcionalidades Implementadas

### 1. **📅 Cobrança Manual**
Permite criar uma cobrança com data de vencimento personalizada.

#### Backend
**Endpoint**: `POST /api/asaas/subscriptions/{id}/create_manual_payment/`

**Parâmetros**:
```json
{
  "due_date": "2026-03-15"  // Formato: YYYY-MM-DD
}
```

**Resposta de Sucesso**:
```json
{
  "success": true,
  "message": "Cobrança manual criada com sucesso",
  "payment_id": "pay_xxxxx",
  "due_date": "2026-03-15"
}
```

**Validações**:
- ✅ Data de vencimento é obrigatória
- ✅ Formato de data deve ser YYYY-MM-DD
- ✅ Serviço Asaas deve estar disponível
- ✅ Loja deve existir

#### Código (Boas Práticas)
```python
@action(detail=True, methods=['post'])
def create_manual_payment(self, request, pk=None):
    """Criar cobrança manual com data personalizada"""
    # Validações
    # Buscar loja
    # Preparar dados (reutilizando funções existentes)
    # Criar cobrança
    # Retornar resultado
```

### 2. **🗑️ Exclusão de Cobrança**
Permite excluir uma cobrança pendente no Asaas e no sistema.

#### Backend
**Endpoint**: `DELETE /api/asaas/payments/{id}/delete_payment/`

**Resposta de Sucesso**:
```json
{
  "success": true,
  "message": "Cobrança excluída com sucesso"
}
```

**Validações**:
- ✅ Não permite excluir cobranças já pagas
- ✅ Exclui no Asaas primeiro
- ✅ Depois exclui localmente
- ✅ Logs detalhados

#### Código (Boas Práticas)
```python
@action(detail=True, methods=['delete'])
def delete_payment(self, request, pk=None):
    """Excluir cobrança no Asaas e no sistema"""
    # Validar se pode excluir (não pode se já pago)
    # Excluir no Asaas
    # Excluir localmente
    # Retornar resultado
```

### 3. **🔧 Correção: Módulo dateutil**
Adicionado `python-dateutil==2.8.2` ao `requirements.txt` para corrigir o erro:
```
No module named 'dateutil'
```

## 📊 Fluxos de Uso

### Fluxo 1: Criar Cobrança Manual
```
1. SuperAdmin acessa: https://lwksistemas.com.br/superadmin/financeiro
2. Clica em "Nova Cobrança" na loja desejada
3. Escolhe "Cobrança Manual"
4. Seleciona data de vencimento personalizada
5. Sistema cria cobrança no Asaas com a data escolhida
6. Cobrança aparece na lista
```

### Fluxo 2: Excluir Cobrança
```
1. SuperAdmin acessa: https://lwksistemas.com.br/superadmin/financeiro
2. Localiza cobrança pendente
3. Clica em "Excluir"
4. Confirma exclusão
5. Sistema exclui no Asaas
6. Sistema exclui localmente
7. Cobrança desaparece da lista
```

### Fluxo 3: Excluir e Criar Nova (Combo)
```
1. Excluir cobrança errada
2. Criar nova cobrança manual com data correta
3. Sistema atualizado
```

## 🎨 Interface (A Implementar no Frontend)

### Modal de Nova Cobrança
```
┌─────────────────────────────────────┐
│ Nova Cobrança - Luiz Salao          │
├─────────────────────────────────────┤
│                                     │
│ Escolha o tipo de cobrança:         │
│                                     │
│ ○ Automática (próximo mês, dia 10) │
│ ● Manual (escolher data)            │
│                                     │
│ Data de Vencimento:                 │
│ [15/03/2026] 📅                     │
│                                     │
│ Valor: R$ 199,90                    │
│                                     │
├─────────────────────────────────────┤
│         [Cancelar]  [Criar]         │
└─────────────────────────────────────┘
```

### Botão de Exclusão
```
┌─────────────────────────────────────┐
│ Luiz Salao                          │
│ Profissional (Mensal) - R$ 199,90  │
│ Vencimento: 10/07/2026              │
│ Status: Aguardando pagamento        │
│                                     │
│ [📄 Boleto] [🔄 Status] [🗑️ Excluir]│
└─────────────────────────────────────┘
```

## 🔒 Segurança

### Validações Implementadas
- ✅ Apenas SuperAdmin pode criar/excluir cobranças
- ✅ Não permite excluir cobranças pagas
- ✅ Validação de formato de data
- ✅ Validação de existência da loja
- ✅ Logs detalhados de todas as operações

### Logs
```python
# Cobrança Manual
logger.info(f"📅 Criando cobrança manual para {loja.nome}")
logger.info(f"   - Data de vencimento: {due_date_str}")

# Exclusão
logger.info(f"🗑️ Excluindo cobrança {payment.asaas_id}")
logger.info(f"   - Status: {payment.status}")
logger.info(f"   - Valor: R$ {payment.value}")
logger.info(f"✅ Cobrança excluída no Asaas")
logger.info(f"✅ Cobrança excluída localmente (ID: {payment_id})")
```

## 🚀 Deploy

### Backend v454
```bash
git add -A
git commit -m "v454: Adicionar python-dateutil + Cobrança manual + Exclusão de cobrança"
git push heroku master
```

✅ **Status**: Deploy em andamento  
🌐 **URL**: https://lwksistemas-38ad47519238.herokuapp.com

## 📝 Próximos Passos

### Frontend (A Implementar)
1. ✅ Modal de nova cobrança com opção manual
2. ✅ Seletor de data (date picker)
3. ✅ Botão de exclusão em cada cobrança
4. ✅ Confirmação antes de excluir
5. ✅ Feedback visual (loading, sucesso, erro)

### Melhorias Futuras
- [ ] Editar data de vencimento de cobrança existente
- [ ] Cancelar cobrança (sem excluir)
- [ ] Histórico de cobranças excluídas
- [ ] Notificação por email ao criar cobrança manual
- [ ] Validação de data mínima (não permitir datas passadas)

## 🎯 Benefícios

**Para o SuperAdmin:**
- ✅ Flexibilidade para criar cobranças em datas específicas
- ✅ Corrigir erros excluindo e recriando cobranças
- ✅ Controle total sobre o financeiro das lojas

**Para o Sistema:**
- ✅ Código limpo e organizado
- ✅ Reutilização de funções existentes
- ✅ Logs detalhados para debug
- ✅ Validações robustas

**Novas funcionalidades implementadas com boas práticas!** 🎉
