# 🔐 CREDENCIAIS DE PRODUÇÃO - LWK SISTEMAS

## ✅ SISTEMA ONLINE E FUNCIONANDO

### 🌐 URLs de Acesso

| Serviço | URL |
|---------|-----|
| **Sistema Principal** | https://lwksistemas.com.br |
| **API Backend** | https://lwksistemas-38ad47519238.herokuapp.com |
| **Admin Django** | https://lwksistemas-38ad47519238.herokuapp.com/admin |

### 🔑 Credenciais de Login

#### Super Administrador
```
URL: https://lwksistemas.com.br/superadmin/login
Usuário: superadmin
Senha: super123
```

#### Suporte
```
URL: https://lwksistemas.com.br/suporte/login
Usuário: suporte
Senha: suporte123
```

### 🧪 Teste de API

**Login via API:**
```bash
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"super123"}'
```

**Resposta esperada:**
```json
{
  "refresh": "eyJ...",
  "access": "eyJ..."
}
```

### 📊 Status do Banco de Dados

- ✅ **Usuários**: 8 cadastrados
- ✅ **Tipos de Loja**: 5 configurados
- ✅ **Planos**: 21 disponíveis
- ✅ **Migrações**: Todas aplicadas

### 🔧 Resolução de Problemas

**Se o login não funcionar:**

1. **Limpar cache do navegador**
2. **Tentar em aba anônima**
3. **Verificar se está usando HTTPS**
4. **Testar API diretamente**

**Comandos de diagnóstico:**
```bash
# Testar API
curl https://lwksistemas-38ad47519238.herokuapp.com/api/

# Testar login
curl -X POST https://lwksistemas-38ad47519238.herokuapp.com/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"super123"}'
```

### 🎯 Funcionalidades Disponíveis

**Super Admin:**
- ✅ Dashboard com estatísticas
- ✅ Gerenciamento de lojas
- ✅ Gerenciamento de planos
- ✅ Gerenciamento de tipos de loja
- ✅ Relatórios financeiros
- ✅ Gerenciamento de usuários

**Suporte:**
- ✅ Dashboard de chamados
- ✅ Atendimento de tickets
- ✅ Histórico de suporte

### 🚀 Sistema Totalmente Funcional

- ✅ **Frontend**: Deployado no Vercel
- ✅ **Backend**: Deployado no Heroku
- ✅ **Banco**: PostgreSQL configurado
- ✅ **HTTPS**: Ativo em ambos
- ✅ **CORS**: Configurado corretamente
- ✅ **Autenticação**: JWT funcionando
- ✅ **Login**: Credenciais validadas

---

## 🎊 SISTEMA PRONTO PARA USO!

**Acesse agora: https://lwksistemas.com.br**

**Login: superadmin / super123**