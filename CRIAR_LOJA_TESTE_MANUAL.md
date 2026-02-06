# 🧪 Como Criar Loja de Teste - Cabeleireiro

## 📋 PASSO A PASSO

### **1. Acessar Superadmin**
URL: https://lwksistemas.com.br/superadmin/lojas

### **2. Clicar em "+ Nova Loja"**

### **3. Preencher Formulário**
- **Nome**: Salão Teste 2026
- **Tipo**: Cabeleireiro
- **Plano**: Qualquer plano ativo
- **CPF/CNPJ**: 12345678901234 (fictício)
- **Email**: teste@cabeleireiro.com
- **Outros campos**: Preencher conforme necessário

### **4. Salvar**

### **5. Verificar Funcionário Admin**
1. Acesse o dashboard da loja criada
2. Clique em "👥 Funcionários" (Ações Rápidas)
3. **Verificar**: Admin deve aparecer automaticamente na lista
4. **Testar proteção**: Tentar editar/excluir (deve estar bloqueado)

---

## ✅ O QUE DEVE ACONTECER

### **Automático (Signal)**
- ✅ Funcionário admin criado automaticamente
- ✅ Nome: Nome do proprietário
- ✅ Email: Email do proprietário
- ✅ Cargo: "Proprietário"
- ✅ Função: "administrador"
- ✅ is_active: True

### **Proteção**
- ✅ Botões Editar/Excluir NÃO aparecem
- ✅ Mensagem: "🔒 Admin da loja (não pode ser editado/excluído)"

---

## 🔍 SE NÃO FUNCIONAR

Verificar logs do Heroku:
```bash
heroku logs --tail --app lwksistemas | grep "Cabeleireiro Signal"
```

Deve aparecer:
```
✅ [Cabeleireiro Signal] Funcionário admin criado: [Nome] para loja [Nome Loja]
```
