# ✅ CHECKLIST DE IMPLEMENTAÇÃO: Sistema de Acesso às Lojas

**Data:** 31 de Março de 2026  
**Responsável:** Equipe de Desenvolvimento  
**Prazo:** 1 dia

---

## 📋 FASE 1: PREPARAÇÃO (1 dia)

### 1.1 Modificações no Modelo Loja
- [ ] Adicionar campo `atalho` (SlugField, unique=True, max_length=50)
- [ ] Adicionar campo `subdomain` (SlugField, unique=True, null=True, max_length=50)
- [ ] Adicionar índice para campo `atalho`
- [ ] Adicionar índice para campo `subdomain`
- [ ] Criar método `_generate_unique_atalho()`
- [ ] Atualizar método `save()` para gerar atalho automaticamente
- [ ] Adicionar método `get_url_amigavel()`
- [ ] Adicionar método `get_url_segura()`
- [ ] Atualizar docstrings dos métodos

**Arquivo:** `backend/superadmin/models.py`

**Código de Referência:**
```python
# Adicionar após o campo slug
atalho = models.SlugField(
    unique=True, 
    blank=True,
    max_length=50,
    help_text='Atalho curto para acesso fácil (ex: felix)'
)
subdomain = models.SlugField(
    unique=True, 
    blank=True, 
    null=True,
    max_length=50,
    help_text='Subdomínio personalizado (ex: felix.lwksistemas.com.br)'
)
```

---

### 1.2 Criar Migration
- [ ] Executar `python manage.py makemigrations`
- [ ] Revisar migration gerada
- [ ] Testar migration em ambiente de desenvolvimento
- [ ] Verificar se índices foram criados corretamente
- [ ] Documentar migration

**Comando:**
```bash
python manage.py makemigrations superadmin
python manage.py migrate superadmin
```

---

### 1.3 Script de Migração de Lojas Existentes
- [ ] Criar script `gerar_atalhos_lojas_existentes.py`
- [ ] Gerar atalhos para todas as lojas existentes
- [ ] Validar unicidade dos atalhos
- [ ] Testar em ambiente de desenvolvimento
- [ ] Documentar script

**Arquivo:** `backend/management/commands/gerar_atalhos_lojas.py`

**Código de Referência:**
```python
from django.core.management.base import BaseCommand
from superadmin.models import Loja

class Command(BaseCommand):
    help = 'Gera atalhos para lojas existentes'
    
    def handle(self, *args, **options):
        lojas = Loja.objects.filter(atalho='')
        for loja in lojas:
            loja.save()  # Vai gerar atalho automaticamente
            self.stdout.write(f'✅ Atalho gerado para {loja.nome}: {loja.atalho}')
```

---

## 📋 FASE 2: BACKEND (2 horas)

### 2.1 Criar View de Redirecionamento
- [ ] Criar função `atalho_redirect` em `views.py`
- [ ] Implementar busca de loja por atalho
- [ ] Implementar verificação de autenticação
- [ ] Implementar redirecionamento para login se não autenticado
- [ ] Implementar redirecionamento para loja se autenticado
- [ ] Adicionar tratamento de erros (loja não encontrada)
- [ ] Adicionar logs para debug
- [ ] Documentar função

**Arquivo:** `backend/superadmin/views.py`

**Código de Referência:**
```python
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def atalho_redirect(request, atalho):
    """Redireciona atalho curto para URL completa da loja"""
    from django.shortcuts import redirect, get_object_or_404
    
    loja = get_object_or_404(Loja, atalho=atalho, is_active=True)
    
    if not request.user.is_authenticated:
        return redirect(f'/loja/{loja.slug}/login')
    
    return redirect(f'/loja/{loja.slug}/crm-vendas')
```

---

### 2.2 Atualizar View de Login
- [ ] Modificar `login_view` para buscar loja do usuário
- [ ] Implementar redirecionamento automático após login
- [ ] Adicionar suporte para parâmetro `next` (redirecionamento customizado)
- [ ] Adicionar tratamento para usuários sem loja (admin/suporte)
- [ ] Adicionar logs para debug
- [ ] Documentar mudanças

**Arquivo:** `backend/superadmin/views.py`

---

### 2.3 Adicionar Rotas
- [ ] Adicionar rota para `atalho_redirect` em `urls.py`
- [ ] Posicionar rota ANTES de rotas genéricas
- [ ] Testar ordem das rotas
- [ ] Documentar rota

**Arquivo:** `backend/urls.py`

**Código de Referência:**
```python
from superadmin.views import atalho_redirect

urlpatterns = [
    # ... rotas existentes ...
    
    # ✅ NOVO: Atalho de acesso rápido
    path('<str:atalho>/', atalho_redirect, name='atalho_redirect'),
]
```

---

### 2.4 Atualizar Serializers
- [ ] Adicionar campos `atalho` e `subdomain` ao `LojaSerializer`
- [ ] Adicionar campos ao `LojaCreateSerializer`
- [ ] Adicionar validação de unicidade
- [ ] Documentar mudanças

**Arquivo:** `backend/superadmin/serializers.py`

---

## 📋 FASE 3: TESTES (2 horas)

### 3.1 Testes de Criação de Loja
- [ ] Criar nova loja via API
- [ ] Verificar se atalho foi gerado automaticamente
- [ ] Verificar se atalho é único
- [ ] Verificar se slug seguro foi gerado
- [ ] Verificar se database_name foi criado corretamente

**Casos de Teste:**
```
1. Criar loja "Felix Representações"
   - Esperado: atalho = "felix-representacoes"
   - Esperado: slug = "felix-representacoes-a8f3k9" (com hash)

2. Criar segunda loja "Felix Representações"
   - Esperado: atalho = "felix-representacoes-1"
   - Esperado: slug = "felix-representacoes-b9e4l2" (hash diferente)
```

---

### 3.2 Testes de Redirecionamento
- [ ] Testar acesso via atalho sem login
- [ ] Verificar redirecionamento para página de login
- [ ] Fazer login
- [ ] Testar acesso via atalho com login
- [ ] Verificar redirecionamento para dashboard da loja
- [ ] Testar atalho inexistente (deve retornar 404)

**Casos de Teste:**
```
1. Acesso sem login:
   GET /felix
   Esperado: Redirect para /loja/felix-representacoes-a8f3k9/login

2. Acesso com login:
   GET /felix (autenticado)
   Esperado: Redirect para /loja/felix-representacoes-a8f3k9/crm-vendas

3. Atalho inexistente:
   GET /naoexiste
   Esperado: 404 Not Found
```

---

### 3.3 Testes de Login Automático
- [ ] Fazer login via API
- [ ] Verificar se resposta contém `redirect_url`
- [ ] Verificar se `redirect_url` usa slug seguro
- [ ] Verificar se redirecionamento funciona no frontend

**Casos de Teste:**
```
POST /api/auth/login
{
  "email": "admin@felix.com",
  "password": "senha123"
}

Esperado:
{
  "success": true,
  "redirect_url": "/loja/felix-representacoes-a8f3k9/crm-vendas",
  "loja_nome": "Felix Representações",
  "loja_slug": "felix-representacoes-a8f3k9"
}
```

---

### 3.4 Testes de Unicidade
- [ ] Tentar criar duas lojas com mesmo nome
- [ ] Verificar se atalhos são diferentes
- [ ] Verificar se slugs são diferentes
- [ ] Verificar se database_names são diferentes

---

### 3.5 Testes de Migração
- [ ] Executar script de migração em lojas existentes
- [ ] Verificar se todos os atalhos foram gerados
- [ ] Verificar se não há atalhos duplicados
- [ ] Testar acesso via atalho em lojas migradas

---

### 3.6 Testes de Performance
- [ ] Medir tempo de resposta do redirecionamento
- [ ] Verificar se índices estão sendo usados
- [ ] Testar com 100+ lojas
- [ ] Verificar uso de cache (se aplicável)

---

### 3.7 Testes de Segurança
- [ ] Tentar acessar loja inativa via atalho (deve falhar)
- [ ] Tentar SQL injection no atalho
- [ ] Verificar se CNPJ não é exposto em nenhuma resposta
- [ ] Verificar logs de acesso

---

## 📋 FASE 4: DOCUMENTAÇÃO (1 hora)

### 4.1 Documentação da API
- [ ] Atualizar documentação Swagger/OpenAPI
- [ ] Documentar novo endpoint de redirecionamento
- [ ] Documentar novos campos do modelo Loja
- [ ] Adicionar exemplos de uso

**Arquivo:** `backend/superadmin/api_docs.py`

---

### 4.2 Documentação para Desenvolvedores
- [ ] Atualizar README.md
- [ ] Documentar novos campos e métodos
- [ ] Adicionar exemplos de código
- [ ] Documentar fluxos de redirecionamento

**Arquivo:** `README.md`

---

### 4.3 Guia para Clientes
- [ ] Criar guia de uso do atalho
- [ ] Explicar como acessar a loja
- [ ] Adicionar exemplos práticos
- [ ] Criar FAQ

**Arquivo:** `docs/GUIA_ACESSO_LOJAS.md`

---

### 4.4 Documentação Técnica
- [ ] Documentar decisões de design
- [ ] Documentar estrutura de dados
- [ ] Documentar fluxos de segurança
- [ ] Adicionar diagramas (se necessário)

---

## 📋 FASE 5: DEPLOY (30 minutos)

### 5.1 Preparação
- [ ] Revisar todas as mudanças
- [ ] Executar todos os testes
- [ ] Criar backup do banco de dados
- [ ] Revisar migrations

---

### 5.2 Deploy Backend
- [ ] Fazer commit das mudanças
- [ ] Push para repositório
- [ ] Deploy no Heroku
- [ ] Executar migrations em produção
- [ ] Verificar logs

**Comandos:**
```bash
git add .
git commit -m "feat: Sistema híbrido de acesso às lojas (atalho + login automático)"
git push heroku main
heroku run python manage.py migrate
```

---

### 5.3 Migração de Dados em Produção
- [ ] Executar script de geração de atalhos
- [ ] Verificar se todos os atalhos foram gerados
- [ ] Validar unicidade
- [ ] Testar acesso via atalho

**Comando:**
```bash
heroku run python manage.py gerar_atalhos_lojas
```

---

### 5.4 Verificação Pós-Deploy
- [ ] Testar criação de nova loja
- [ ] Testar acesso via atalho
- [ ] Testar login automático
- [ ] Verificar logs de erro
- [ ] Monitorar performance

---

## 📋 FASE 6: MONITORAMENTO (Contínuo)

### 6.1 Métricas
- [ ] Configurar monitoramento de uso de atalhos
- [ ] Monitorar tempo de resposta
- [ ] Monitorar erros 404
- [ ] Monitorar taxa de conversão (login → acesso)

---

### 6.2 Feedback
- [ ] Coletar feedback dos clientes
- [ ] Identificar problemas de UX
- [ ] Ajustar conforme necessário

---

## ✅ CRITÉRIOS DE ACEITAÇÃO

### Funcionalidade
- [x] Novas lojas geram atalho automaticamente
- [x] Atalhos são únicos
- [x] Redirecionamento via atalho funciona
- [x] Login redireciona automaticamente para loja
- [x] Lojas existentes podem ser migradas

### Segurança
- [x] CNPJ não é exposto na URL
- [x] Hash aleatório impede enumeração
- [x] Login obrigatório para acesso
- [x] Lojas inativas não são acessíveis

### Performance
- [x] Redirecionamento < 100ms
- [x] Índices otimizados
- [x] Sem N+1 queries

### UX
- [x] Atalho fácil de lembrar
- [x] Login automático funciona
- [x] URLs amigáveis

---

## 🎯 RESULTADO ESPERADO

### Antes
```
URL: lwksistemas.com.br/loja/41449198000172/crm-vendas
Segurança: 3/10
UX: 3/10
```

### Depois
```
URL Atalho: lwksistemas.com.br/felix
URL Segura: lwksistemas.com.br/loja/felix-representacoes-a8f3k9/crm-vendas
Segurança: 9/10 (+200%)
UX: 10/10 (+233%)
```

---

## 📞 CONTATOS

**Dúvidas Técnicas:** Equipe de Desenvolvimento  
**Aprovação:** Product Owner  
**Testes:** QA Team

---

## 📚 DOCUMENTOS RELACIONADOS

- [x] `RECOMENDACAO_FINAL_ACESSO_LOJAS.md` - Documentação completa
- [x] `RESUMO_EXECUTIVO_ACESSO_LOJAS.md` - Resumo executivo
- [x] `COMPARACAO_VISUAL_ACESSO_LOJAS.md` - Comparação visual
- [x] `SOLUCAO_ACESSO_LOJAS_UX.md` - Análise de UX
- [x] `ANALISE_SEGURANCA_SCHEMA_VS_SLUG.md` - Análise de segurança

---

**Status:** ✅ PRONTO PARA IMPLEMENTAÇÃO  
**Prioridade:** 🔴 ALTA  
**Prazo:** 1 dia  
**Aprovado por:** Product Owner  
**Data de Aprovação:** 31 de Março de 2026
