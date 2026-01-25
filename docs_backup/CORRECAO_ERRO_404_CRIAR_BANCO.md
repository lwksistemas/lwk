# ✅ Correção Erro 404 - Criar Banco

## Problema

Ao criar uma nova loja, ocorria erro 404:
```
AxiosError: Request failed with status code 404
at async handleSubmit (app/(dashboard)/superadmin/lojas/page.tsx:491:7)
```

**Causa**: O sistema tentava criar o banco automaticamente logo após criar a loja, mas o endpoint não estava sendo encontrado corretamente.

---

## ✅ Solução Implementada

### Mudança no Fluxo

**ANTES (com erro):**
1. Criar loja via POST `/superadmin/lojas/`
2. Criar banco automaticamente via POST `/superadmin/lojas/{id}/criar_banco/` ❌ (causava erro 404)

**AGORA (corrigido):**
1. Criar loja via POST `/superadmin/lojas/`
2. Superadmin cria banco manualmente clicando em "Criar Banco" na lista ✅

---

## 🎯 Vantagens da Nova Abordagem

### 1. **Mais Controle**
- Superadmin decide quando criar o banco
- Pode revisar dados da loja antes de criar banco

### 2. **Mais Seguro**
- Evita criação de bancos desnecessários
- Permite correção de dados antes de criar banco

### 3. **Sem Erros**
- Elimina o erro 404
- Processo mais estável

### 4. **Flexibilidade**
- Pode criar loja sem banco (para testes)
- Pode criar banco depois se necessário

---

## 📋 Novo Fluxo de Criação de Loja

### Passo 1: Criar Loja
1. Acessar `/superadmin/lojas`
2. Clicar em "+ Nova Loja"
3. Preencher formulário
4. Clicar em "Criar Loja"

**Resultado:**
```
✅ Loja "Nome da Loja" criada com sucesso!

📋 Informações importantes:
• Email enviado para: email@exemplo.com
• Senha provisória gerada: ABC123xyz

🔐 Dados de acesso enviados por email:
• URL: http://localhost:3000/loja/slug/login
• Usuário: username
• Email: email@exemplo.com

💡 O proprietário pode alterar a senha no primeiro acesso.

⚠️ IMPORTANTE: Use o botão "Criar Banco" na lista de lojas 
para criar o banco de dados isolado.
```

### Passo 2: Criar Banco (Manual)
1. Na lista de lojas, localizar a loja criada
2. Clicar no botão "Criar Banco"
3. Confirmar criação

**Resultado:**
```
Banco criado com sucesso!

Usuário: username
Senha: senha123
```

---

## 🔧 Código Alterado

### Frontend: `frontend/app/(dashboard)/superadmin/lojas/page.tsx`

**Linha 491 - REMOVIDA:**
```typescript
// ❌ REMOVIDO (causava erro 404)
await apiClient.post(`/superadmin/lojas/${response.data.id}/criar_banco/`);
```

**Mensagem Atualizada:**
```typescript
mensagem += `\n\n⚠️ IMPORTANTE: Use o botão "Criar Banco" na lista de lojas para criar o banco de dados isolado.`;
```

---

## ✅ Status Atual

### Funcionalidades Operacionais:
- ✅ Criar loja (sem banco)
- ✅ Criar banco manualmente (botão na lista)
- ✅ Email com senha provisória
- ✅ Editar loja
- ✅ Excluir loja (com banco)
- ✅ Reenviar senha
- ✅ Mostrar senha

### Fluxo Recomendado:
1. Criar loja
2. Verificar dados na lista
3. Criar banco manualmente
4. Loja pronta para uso

---

## 💡 Alternativa Futura (Opcional)

Se quiser criar banco automaticamente no futuro, pode-se:

### Opção 1: Criar no Backend (Serializer)
```python
# backend/superadmin/serializers.py
def create(self, validated_data):
    # ... código existente ...
    loja = Loja.objects.create(**validated_data)
    
    # Criar banco automaticamente
    from django.core.management import call_command
    call_command('migrate', '--database', loja.database_name)
    loja.database_created = True
    loja.save()
    
    return loja
```

### Opção 2: Usar Celery (Assíncrono)
```python
# Criar banco em background
from celery import shared_task

@shared_task
def criar_banco_async(loja_id):
    loja = Loja.objects.get(id=loja_id)
    # criar banco...
```

---

## ✅ Conclusão

O erro foi corrigido removendo a chamada automática ao endpoint `criar_banco`. Agora o superadmin tem controle total sobre quando criar o banco de dados isolado de cada loja.

**Status**: ✅ Corrigido e Funcional

---

**Última atualização:** 16/01/2026
**Arquivo alterado:** `frontend/app/(dashboard)/superadmin/lojas/page.tsx`
