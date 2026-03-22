# Correção: Salvar Fotos na Página de Login - v1233

## 📋 PROBLEMA IDENTIFICADO

**Relatado pelo usuário:** As fotos não estavam sendo salvas na página de login da loja.

**URL afetada:** https://lwksistemas.com.br/loja/41449198000172/login

## 🔍 DIAGNÓSTICO

### Causa Raiz
O backend tinha os campos `login_background` e `login_logo` no modelo `Loja`, mas a view `LoginConfigView` não estava processando esses campos ao salvar.

### Fluxo do Problema
1. Frontend envia `login_background` e `login_logo` no PATCH request
2. Backend recebe os dados mas ignora esses campos
3. Apenas `logo`, `cor_primaria` e `cor_secundaria` eram salvos
4. Usuário não conseguia personalizar a imagem de fundo e logo específico do login

## ✅ SOLUÇÃO IMPLEMENTADA

### Arquivos Modificados
- `backend/crm_vendas/views.py` - LoginConfigView

### Mudanças no Código

#### 1. Método GET - Retornar os campos
```python
# ANTES
return Response({
    'logo': (loja.logo or '').strip(),
    'cor_primaria': cor_primaria,
    'cor_secundaria': cor_secundaria,
})

# DEPOIS
return Response({
    'logo': (loja.logo or '').strip(),
    'login_background': (loja.login_background or '').strip(),  # ✅ NOVO
    'login_logo': (loja.login_logo or '').strip(),              # ✅ NOVO
    'cor_primaria': cor_primaria,
    'cor_secundaria': cor_secundaria,
})
```

#### 2. Método PATCH - Salvar os campos
```python
# ANTES
if 'logo' in request.data:
    val = (request.data.get('logo') or '').strip()
    loja.logo = val[:200] if val else ''
    update_fields.append('logo')

# DEPOIS
if 'logo' in request.data:
    val = (request.data.get('logo') or '').strip()
    loja.logo = val[:200] if val else ''
    update_fields.append('logo')

if 'login_background' in request.data:  # ✅ NOVO
    val = (request.data.get('login_background') or '').strip()
    loja.login_background = val[:200] if val else ''
    update_fields.append('login_background')

if 'login_logo' in request.data:  # ✅ NOVO
    val = (request.data.get('login_logo') or '').strip()
    loja.login_logo = val[:200] if val else ''
    update_fields.append('login_logo')
```

## 🎯 FUNCIONALIDADES AGORA DISPONÍVEIS

### 1. Logo Principal
- Logo usado no sistema (dashboard, menus, etc.)
- Campo: `logo`

### 2. Imagem de Fundo do Login
- Imagem de fundo exibida na tela de login
- Se não definida, usa gradiente de cores
- Campo: `login_background`

### 3. Logo Específico do Login
- Logo específico para a tela de login
- Se não definido, usa o logo principal
- Campo: `login_logo`

### 4. Cores Personalizadas
- Cor primária e secundária
- Usadas no gradiente e botões
- Campos: `cor_primaria`, `cor_secundaria`

## 📊 IMPACTO

### Antes
- ❌ Apenas logo e cores eram salvos
- ❌ Não era possível personalizar fundo do login
- ❌ Não era possível ter logo diferente no login

### Depois
- ✅ Todos os campos são salvos corretamente
- ✅ Personalização completa da tela de login
- ✅ Imagem de fundo customizável
- ✅ Logo específico para login

## 🧪 COMO TESTAR

### 1. Acessar Configurações de Login
```
URL: /loja/{slug}/crm-vendas/configuracoes/login
```

### 2. Upload de Imagens
1. Fazer upload da imagem de fundo (login_background)
2. Fazer upload do logo do login (login_logo)
3. Clicar em "Salvar"

### 3. Verificar na Página de Login
```
URL: /loja/{slug}/login
```

Deve exibir:
- Imagem de fundo (se definida)
- Logo específico do login (se definido, senão usa logo principal)
- Cores personalizadas

## 🔧 DETALHES TÉCNICOS

### Endpoint
```
PATCH /crm-vendas/login-config/
```

### Payload
```json
{
  "logo": "https://res.cloudinary.com/.../logo.jpg",
  "login_background": "https://res.cloudinary.com/.../background.jpg",
  "login_logo": "https://res.cloudinary.com/.../login-logo.jpg",
  "cor_primaria": "#10B981",
  "cor_secundaria": "#059669"
}
```

### Response
```json
{
  "logo": "https://res.cloudinary.com/.../logo.jpg",
  "login_background": "https://res.cloudinary.com/.../background.jpg",
  "login_logo": "https://res.cloudinary.com/.../login-logo.jpg",
  "cor_primaria": "#10B981",
  "cor_secundaria": "#059669"
}
```

### Validações
- URLs limitadas a 200 caracteres (URLField max_length)
- Valores vazios são aceitos (campos opcionais)
- Cache é limpo após salvar (`loja_info_publica:{slug}`)

## 📝 MODELO DE DADOS

### Campos no Modelo Loja
```python
class Loja(models.Model):
    # Logo principal
    logo = models.URLField(blank=True)
    
    # Personalização da tela de login
    login_background = models.URLField(blank=True)  # ✅ Agora funciona
    login_logo = models.URLField(blank=True)        # ✅ Agora funciona
    
    # Cores
    cor_primaria = models.CharField(max_length=7, blank=True)
    cor_secundaria = models.CharField(max_length=7, blank=True)
```

## 🚀 DEPLOY

- **Backend:** Heroku v1230
- **Commit:** fe02f076
- **Data:** 22/03/2026

## ✅ CONCLUSÃO

Problema resolvido! Agora os usuários podem:
- Personalizar completamente a tela de login
- Fazer upload de imagem de fundo
- Definir logo específico para o login
- Todas as configurações são salvas corretamente

A correção foi simples mas essencial para a experiência do usuário.
