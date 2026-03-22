# Solução: Endpoints Públicos para Cadastro de Lojas

## Problema Identificado

O formulário de cadastro público em `/cadastro` estava falhando com erro 401 (Unauthorized) porque tentava acessar endpoints protegidos que requerem autenticação de superadmin:

- `/api/superadmin/tipos-loja/` → 401
- `/api/superadmin/planos/` → 401
- `/api/superadmin/mercadopago-config/` → 401

## Solução Implementada

### 1. Backend: Criação de ViewSets Públicos

**Arquivo**: `backend/superadmin/views.py`

Criados dois novos ViewSets públicos (somente leitura):

```python
class TipoLojaPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet público para listar tipos de loja"""
    serializer_class = TipoLojaSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        return TipoLoja.objects.filter(is_active=True).order_by('nome')

class PlanoAssinaturaPublicoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet público para listar planos de assinatura"""
    serializer_class = PlanoAssinaturaSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def get_queryset(self):
        return PlanoAssinatura.objects.filter(is_active=True).order_by('preco_mensal')
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Buscar planos por tipo de app (público)"""
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            planos = self.get_queryset().filter(tipos_loja__id=tipo_id)
            serializer = self.get_serializer(planos, many=True)
            return Response(serializer.data)
        return Response({'error': 'tipo_id é obrigatório'}, status=400)
```

**Características**:
- `permission_classes = [permissions.AllowAny]` → Sem autenticação
- `authentication_classes = []` → Sem verificação de token
- `ReadOnlyModelViewSet` → Apenas GET (segurança)
- Retorna apenas registros ativos (`is_active=True`)

### 2. Backend: Rotas Públicas

**Arquivo**: `backend/superadmin/urls.py`

Criado router público separado:

```python
# Router público para cadastro de lojas (sem autenticação)
public_router = DefaultRouter()
public_router.register(r'tipos-loja', TipoLojaPublicoViewSet, basename='public-tipo-loja')
public_router.register(r'planos', PlanoAssinaturaPublicoViewSet, basename='public-plano')

urlpatterns = [
    # ...
    path('public/', include(public_router.urls)),
    # ...
]
```

**Endpoints criados**:
- `GET /api/superadmin/public/tipos-loja/` → Lista tipos de loja
- `GET /api/superadmin/public/planos/` → Lista planos
- `GET /api/superadmin/public/planos/por_tipo/?tipo_id=X` → Planos por tipo

### 3. Frontend: Hook Atualizado

**Arquivo**: `frontend/hooks/useLojaForm.ts`

Atualizado para usar endpoints públicos quando `incluirSenha=false`:

```typescript
const loadTiposEPlanos = async () => {
  try {
    // Usar endpoints públicos quando não incluir senha (cadastro público)
    const baseUrl = incluirSenha ? '/superadmin' : '/superadmin/public';
    
    const [tiposRes, planosRes] = await Promise.all([
      apiClient.get(`${baseUrl}/tipos-loja/`),
      apiClient.get(`${baseUrl}/planos/`)
    ]);
    
    setTipos(tiposRes.data.results || tiposRes.data);
    setPlanos(planosRes.data.results || planosRes.data);
  } catch (error) {
    console.error('Erro ao carregar tipos e planos:', error);
  }
};

const loadPlanosPorTipo = async (tipoId: string) => {
  if (!tipoId) {
    setPlanos([]);
    return;
  }
  
  try {
    const baseUrl = incluirSenha ? '/superadmin' : '/superadmin/public';
    const response = await apiClient.get(`${baseUrl}/planos/por_tipo/?tipo_id=${tipoId}`);
    setPlanos(response.data);
  } catch (error) {
    console.error('Erro ao carregar planos por tipo:', error);
    setPlanos([]);
  }
};
```

**Mudanças**:
- Detecta modo público via parâmetro `incluirSenha`
- Usa `/superadmin/public/` para cadastro público
- Usa `/superadmin/` para painel admin
- Não chama MercadoPago config no modo público

### 4. Limpeza de Código

**Arquivo**: `frontend/app/cadastro/page.tsx`

Removidos imports e variáveis não utilizadas:
- Removido `useRouter` (não usado)
- Warnings TypeScript corrigidos

## Fluxo de Funcionamento

### Cadastro Público (`/cadastro`)
1. Usuário acessa `/cadastro` (sem autenticação)
2. Hook `useLojaForm(false)` carrega dados via endpoints públicos
3. Formulário exibe tipos e planos disponíveis
4. Usuário preenche e submete
5. POST para `/api/superadmin/lojas/` cria a loja
6. Senha gerada automaticamente no backend
7. Boleto gerado e senha enviada por email após pagamento

### Painel Admin (`/superadmin/lojas`)
1. Superadmin autenticado acessa painel
2. Hook `useLojaForm(true)` carrega dados via endpoints protegidos
3. Formulário exibe campo de senha provisória
4. Admin pode criar loja com senha customizada

## Segurança

✅ Endpoints públicos são **somente leitura** (ReadOnlyModelViewSet)
✅ Retornam apenas registros ativos
✅ Não expõem dados sensíveis
✅ Criação de loja continua protegida (POST requer validação)
✅ Separação clara entre rotas públicas e protegidas

## Testes Necessários

1. Acessar `/cadastro` sem autenticação
2. Verificar se tipos e planos carregam
3. Selecionar tipo e verificar se planos filtram
4. Preencher formulário e submeter
5. Verificar criação da loja no banco
6. Confirmar que painel admin continua funcionando

## Arquivos Modificados

- `backend/superadmin/views.py` → ViewSets públicos
- `backend/superadmin/urls.py` → Rotas públicas
- `frontend/hooks/useLojaForm.ts` → Lógica de endpoints
- `frontend/app/cadastro/page.tsx` → Limpeza de código
