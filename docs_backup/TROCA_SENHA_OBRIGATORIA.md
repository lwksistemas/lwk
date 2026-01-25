# Troca de Senha Obrigatória - Primeiro Acesso

## ✅ Funcionalidade Implementada

Sistema de troca de senha obrigatória para proprietários de loja no primeiro acesso.

---

## 🔐 Como Funciona

### 1. Criação da Loja
Quando uma loja é criada:
- ✅ Senha provisória é gerada automaticamente
- ✅ Email é enviado com as credenciais
- ✅ Campo `senha_foi_alterada` = `False`

### 2. Primeiro Login
Quando o proprietário faz login pela primeira vez:
- ✅ Sistema verifica se `senha_foi_alterada` = `False`
- ✅ Se `False`, redireciona para `/loja/trocar-senha`
- ✅ Usuário não consegue acessar o dashboard sem trocar a senha

### 3. Troca de Senha
Na página de troca de senha:
- ✅ Usuário digita nova senha (mínimo 6 caracteres)
- ✅ Confirma a nova senha
- ✅ Sistema valida e altera a senha
- ✅ Marca `senha_foi_alterada` = `True`
- ✅ Faz logout automático
- ✅ Usuário faz login novamente com a nova senha

### 4. Próximos Acessos
Após trocar a senha:
- ✅ `senha_foi_alterada` = `True`
- ✅ Usuário acessa normalmente o dashboard
- ✅ Não é mais solicitado trocar senha

---

## 📊 Banco de Dados

### Modelo Loja
```python
class Loja(models.Model):
    # ... outros campos ...
    senha_provisoria = models.CharField(max_length=50, blank=True)
    senha_foi_alterada = models.BooleanField(default=False)
```

### Migration
```python
# 0005_add_senha_alterada.py
migrations.AddField(
    model_name='loja',
    name='senha_foi_alterada',
    field=models.BooleanField(default=False),
)
```

---

## 🔌 API Endpoints

### 1. Verificar Senha Provisória
```
GET /api/superadmin/lojas/verificar_senha_provisoria/
```

**Response:**
```json
{
  "precisa_trocar_senha": true,
  "loja_id": 1,
  "loja_nome": "Minha Loja"
}
```

### 2. Alterar Senha Primeiro Acesso
```
POST /api/superadmin/lojas/{id}/alterar_senha_primeiro_acesso/
```

**Request:**
```json
{
  "nova_senha": "minha_nova_senha_123",
  "confirmar_senha": "minha_nova_senha_123"
}
```

**Response:**
```json
{
  "message": "Senha alterada com sucesso!",
  "loja": "Minha Loja"
}
```

---

## 🎨 Interface

### Página: `/loja/trocar-senha`

**Elementos:**
- 🔒 Ícone de cadeado amarelo
- ⚠️ Alerta explicando que é primeiro acesso
- 📝 Formulário com 2 campos:
  - Nova Senha (mínimo 6 caracteres)
  - Confirmar Nova Senha
- 💡 Dicas para senha forte
- ✅ Botão "Alterar Senha e Continuar"

**Validações:**
- Senha mínima de 6 caracteres
- Senhas devem coincidir
- Campos obrigatórios

**Após sucesso:**
- Mensagem de sucesso
- Logout automático
- Redirecionamento para `/loja/login`

---

## 🔄 Fluxo Completo

```
1. Super Admin cria loja
   ↓
2. Sistema gera senha provisória
   ↓
3. Email enviado para proprietário
   ↓
4. Proprietário acessa /loja/login
   ↓
5. Faz login com senha provisória
   ↓
6. Sistema verifica: senha_foi_alterada = False
   ↓
7. Redireciona para /loja/trocar-senha
   ↓
8. Proprietário define nova senha
   ↓
9. Sistema altera senha e marca senha_foi_alterada = True
   ↓
10. Logout automático
   ↓
11. Proprietário faz login com nova senha
   ↓
12. Acessa dashboard normalmente
```

---

## 🧪 Testar Funcionalidade

### Passo 1: Criar uma loja
```bash
# Acesse: http://localhost:3000/superadmin/lojas
# Clique em "Nova Loja"
# Preencha os dados
# Use seu email real para receber as credenciais
```

### Passo 2: Verificar email
```
Você receberá um email com:
- URL de login
- Usuário
- Senha provisória
```

### Passo 3: Fazer primeiro login
```bash
# Acesse a URL do email
# Faça login com a senha provisória
# Será redirecionado automaticamente para /loja/trocar-senha
```

### Passo 4: Trocar senha
```
- Digite nova senha (mínimo 6 caracteres)
- Confirme a senha
- Clique em "Alterar Senha e Continuar"
- Será deslogado automaticamente
```

### Passo 5: Login com nova senha
```bash
# Faça login novamente
# Use a nova senha que você definiu
# Acesse o dashboard normalmente
```

---

## 🔒 Segurança

### Validações Implementadas
✅ Senha mínima de 6 caracteres
✅ Confirmação de senha obrigatória
✅ Apenas proprietário pode alterar
✅ Senha só pode ser alterada uma vez (primeiro acesso)
✅ Logout automático após troca
✅ Senha hasheada no banco de dados

### Recomendações
- Senha forte com letras, números e símbolos
- Não reutilizar senhas de outros sites
- Não compartilhar credenciais
- Alterar senha periodicamente

---

## 📝 Código Importante

### Backend - views.py
```python
@action(detail=False, methods=['get'])
def verificar_senha_provisoria(self, request):
    loja = Loja.objects.get(owner=request.user)
    return Response({
        'precisa_trocar_senha': not loja.senha_foi_alterada
    })

@action(detail=True, methods=['post'])
def alterar_senha_primeiro_acesso(self, request, pk=None):
    loja = self.get_object()
    # Validações...
    user.set_password(nova_senha)
    loja.senha_foi_alterada = True
    loja.save()
```

### Frontend - dashboard/page.tsx
```typescript
const verificarSenhaProvisoria = async () => {
  const response = await apiClient.get('/superadmin/lojas/verificar_senha_provisoria/');
  if (response.data.precisa_trocar_senha) {
    router.push('/loja/trocar-senha');
  }
};
```

---

## ✅ Status

- ✅ Migration criada e aplicada
- ✅ Campo `senha_foi_alterada` adicionado
- ✅ Endpoints da API implementados
- ✅ Página de troca de senha criada
- ✅ Verificação no dashboard implementada
- ✅ Validações de segurança
- ✅ Logout automático após troca
- ✅ Fluxo completo funcionando

**Sistema pronto para uso!** 🔐
