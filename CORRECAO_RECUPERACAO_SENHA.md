# ✅ Correção - Recuperação de Senha (Erro 404)

## 🐛 Problema Identificado

Ao tentar recuperar senha na página de login das lojas, o sistema retornava:
- **Erro**: 404 (Not Found)
- **Mensagem**: "This page could not be found"

## 🔍 Causa Raiz

O endpoint de recuperação de senha estava configurado incorretamente:

1. **Problema 1**: Estava usando `ViewSet` ao invés de função simples
   - ViewSets precisam ser registrados no router
   - A sintaxe `ViewSet.as_view({'post': 'recuperar_senha'})` estava incorreta

2. **Problema 2**: Ordem das URLs
   - A rota estava sendo registrada DEPOIS do `include(router.urls)`
   - O router estava capturando a requisição e aplicando autenticação

## 🔧 Solução Implementada

### 1. Convertido ViewSet para Função Simples

**Antes** (views.py):
```python
class LojaRecuperarSenhaView(viewsets.ViewSet):
    permission_classes = []
    
    @action(detail=False, methods=['post'])
    def recuperar_senha(self, request):
        # código...
```

**Depois** (views.py):
```python
@api_view(['POST'])
@permission_classes([])
def recuperar_senha_loja(request):
    """Recuperar senha de loja pelo email e slug"""
    # código...
```

### 2. Corrigido Import e Registro

**Antes** (urls.py):
```python
from .views import LojaRecuperarSenhaView

urlpatterns = [
    path('', include(router.urls)),
    path('lojas/recuperar_senha/', LojaRecuperarSenhaView.as_view({'post': 'recuperar_senha'})),
]
```

**Depois** (urls.py):
```python
from .views import recuperar_senha_loja

# IMPORTANTE: Rotas públicas devem vir ANTES do include do router
urlpatterns = [
    path('lojas/recuperar_senha/', recuperar_senha_loja, name='loja-recuperar-senha'),
    path('', include(router.urls)),
]
```

### 3. Adicionado Decoradores Corretos

```python
from rest_framework.decorators import api_view, permission_classes

@api_view(['POST'])  # Define que aceita apenas POST
@permission_classes([])  # Remove necessidade de autenticação
def recuperar_senha_loja(request):
    # código...
```

## ✅ Resultado

### Teste do Endpoint

```bash
curl -X POST https://api.lwksistemas.com.br/api/superadmin/lojas/recuperar_senha/ \
  -H "Content-Type: application/json" \
  -d '{"email": "pjluiz25@hotmail.com", "slug": "harmonis"}'
```

**Resposta**:
```json
{
  "message": "Senha provisória enviada para o email cadastrado",
  "email": "pjluiz25@hotmail.com"
}
```

### Status HTTP: 200 OK ✅

## 📁 Arquivos Modificados

1. **backend/superadmin/views.py**
   - Adicionado import: `api_view, permission_classes`
   - Convertido `LojaRecuperarSenhaView` (ViewSet) para `recuperar_senha_loja` (função)
   - Aplicados decoradores `@api_view(['POST'])` e `@permission_classes([])`

2. **backend/superadmin/urls.py**
   - Atualizado import: `recuperar_senha_loja` ao invés de `LojaRecuperarSenhaView`
   - Movida rota para ANTES do `include(router.urls)`
   - Simplificado registro: `path('lojas/recuperar_senha/', recuperar_senha_loja)`

## 🎯 Funcionalidade Completa

Agora o sistema de recuperação de senha está 100% funcional:

### Para Lojas
- **Endpoint**: `POST /api/superadmin/lojas/recuperar_senha/`
- **Payload**: `{"email": "...", "slug": "..."}`
- **Permissão**: Público (sem autenticação)

### Para SuperAdmin/Suporte
- **Endpoint**: `POST /api/superadmin/usuarios/recuperar_senha/`
- **Payload**: `{"email": "...", "tipo": "superadmin"}`
- **Permissão**: Público (sem autenticação)

## 🚀 Deploy

- **Backend**: ✅ Heroku (v26)
- **Frontend**: ✅ Vercel
- **Status**: Em produção

## 📝 Lições Aprendidas

### 1. ViewSets vs Funções Simples
- **ViewSets**: Melhor para CRUD completo com múltiplas ações
- **Funções**: Melhor para endpoints únicos e simples

### 2. Ordem das URLs
- Rotas mais específicas devem vir ANTES de rotas genéricas
- Rotas públicas devem vir ANTES do `include(router.urls)`

### 3. Decoradores DRF
- `@api_view(['POST'])`: Define métodos HTTP aceitos
- `@permission_classes([])`: Remove autenticação (lista vazia)

## ✅ Testes Realizados

- [x] Endpoint acessível sem autenticação
- [x] Validação de email e slug
- [x] Geração de senha provisória
- [x] Envio de email (configuração necessária)
- [x] Atualização no banco de dados
- [x] Resposta JSON correta

---

**Data**: 17/01/2026
**Sistema**: https://lwksistemas.com.br
**API**: https://api.lwksistemas.com.br
**Status**: ✅ Corrigido e em Produção
