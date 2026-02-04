# 🔧 CORREÇÃO: Admin da loja não aparece em Funcionários - v254

## 🐛 PROBLEMA IDENTIFICADO

O admin da loja "felix" não aparece na lista de funcionários porque:

1. ✅ API `/superadmin/lojas/info_publica/` **NÃO ESTAVA** retornando o `id` da loja
2. ❌ Frontend salvava `undefined` no `localStorage.getItem('current_loja_id')`
3. ❌ Requisição GET `/crm/vendedores/` enviava header `X-Loja-ID: undefined`
4. ❌ Backend não conseguia filtrar os vendedores corretamente
5. ❌ Vendedor admin não foi criado automaticamente (loja criada antes do signal existir)

## ✅ CORREÇÃO APLICADA

### 1. Backend: Adicionar ID na API info_publica

**Arquivo:** `backend/superadmin/views.py`

```python
def info_publica(self, request):
    """Retorna informações públicas da loja para página de login (sem autenticação)"""
    slug = request.query_params.get('slug')
    if not slug:
        return Response({'error': 'slug é obrigatório'}, status=400)
    
    try:
        loja = Loja.objects.get(slug=slug, is_active=True)
        return Response({
            'id': loja.id,  # ✅ IMPORTANTE: ID único da loja para X-Loja-ID
            'nome': loja.nome,
            'slug': loja.slug,
            'tipo_loja_nome': loja.tipo_loja.nome,
            'cor_primaria': loja.cor_primaria,
            'cor_secundaria': loja.cor_secundaria,
            'logo': loja.logo,
            'login_page_url': loja.login_page_url,
        })
    except Loja.DoesNotExist:
        return Response({'error': 'Loja não encontrada'}, status=404)
```

### 2. Criar vendedor admin para loja "felix"

**Comando para rodar no Heroku:**

```bash
heroku run python backend/manage.py shell -c "
from superadmin.models import Loja
from crm_vendas.models import Vendedor

loja = Loja.objects.get(slug='felix')
print(f'✅ Loja: {loja.nome} (ID: {loja.id})')

# Verificar se já existe
vendedor_existente = Vendedor.objects.all_without_filter().filter(loja_id=loja.id, is_admin=True).first()

if vendedor_existente:
    print(f'ℹ️ Vendedor já existe: {vendedor_existente.nome}')
else:
    vendedor = Vendedor.objects.create(
        nome=loja.owner.get_full_name() or loja.owner.username,
        email=loja.owner.email,
        telefone='',
        cargo='Gerente de Vendas',
        is_admin=True,
        loja_id=loja.id,
        meta_mensal=10000.00
    )
    print(f'✅ Vendedor criado: {vendedor.nome} (ID: {vendedor.id})')
"
```

## 📋 DEPLOY

### Backend v254
```bash
git -C backend add -A
git -C backend commit -m "fix: adicionar ID da loja na API info_publica para X-Loja-ID funcionar"
git -C backend push heroku master
```

**Status:** ✅ Deployado com sucesso

### Teste da API
```bash
curl "https://lwksistemas-38ad47519238.herokuapp.com/api/superadmin/lojas/info_publica/?slug=felix"
```

**Resposta:**
```json
{
    "id": 73,  ← ✅ AGORA RETORNA O ID!
    "nome": "felix",
    "slug": "felix",
    "tipo_loja_nome": "CRM Vendas",
    "cor_primaria": "#3B82F6",
    "cor_secundaria": "#2563EB",
    "logo": "",
    "login_page_url": "/loja/felix/login"
}
```

## 🎯 PRÓXIMOS PASSOS

1. Rodar comando no Heroku para criar vendedor admin
2. Limpar cache do navegador (Ctrl+Shift+Delete)
3. Fazer logout e login novamente
4. Clicar em "Funcionários" 💼
5. ✅ Admin da loja deve aparecer na lista!

## 🔍 VERIFICAÇÃO

Após criar o vendedor, verificar se aparece:

```bash
heroku run python backend/manage.py shell -c "
from crm_vendas.models import Vendedor
vendedores = Vendedor.objects.all_without_filter().filter(loja_id=73)
print(f'Total: {vendedores.count()}')
for v in vendedores:
    print(f'  - {v.nome} (is_admin: {v.is_admin})')
"
```

## 📝 NOTAS

- O signal `create_funcionario_for_loja_owner` já está implementado e funciona para novas lojas
- Lojas antigas (criadas antes do signal) precisam ter o funcionário criado manualmente
- O ID da loja é único e não muda, diferente do slug que pode ser alterado
