# Análise: Problema de Permissões do Administrador - v1185

## Problema Reportado
Usuário Luiz Henrique Felix está logado como administrador (owner) da loja, mas o sistema está limitando seu acesso como se fosse apenas um vendedor.

URL: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/configuracoes

## Contexto
- Loja: FELIX REPRESENTACOES E COMERCIO LTDA (ID: 132)
- CNPJ: 41449198000172
- Usuário: Luiz Henrique Felix (Administrador)
- Email: danielsouzafelix30@gmail.com

## Arquitetura de Permissões

### Tipos de Usuário
1. **Owner (Proprietário)**: Dono da loja, tem acesso total
2. **Vendedor**: Funcionário com acesso limitado
3. **Owner + Vendedor**: Owner que também atua como vendedor (pode fazer vendas)

### Lógica Atual (backend/crm_vendas/utils.py)

```python
def is_vendedor_usuario(request):
    """
    Verifica se o usuário logado é um vendedor (VendedorUsuario), não o owner.
    Retorna True apenas se for um vendedor real, False para owner ou outros.
    """
    # 1. Verificar se é proprietário
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if loja and loja.owner_id == request.user.id:
        return False  # Owner não é vendedor
    
    # 2. Verificar se é vendedor (VendedorUsuario)
    vu = VendedorUsuario.objects.using('default').filter(
        user=request.user,
        loja_id=loja_id,
    ).first()
    return vu is not None
```

### Decorator de Permissão (backend/crm_vendas/decorators.py)

```python
def require_admin_access(message='...'):
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            # 1. Verificar se é proprietário da loja
            loja = Loja.objects.using('default').filter(id=loja_id).first()
            if loja and loja.owner_id == request.user.id:
                # Owner SEMPRE tem acesso total
                return func(self, request, *args, **kwargs)
            
            # 2. Verificar se é vendedor comum (não-owner)
            if is_vendedor_usuario(request):
                return Response({'detail': message}, status=403)
            
            return func(self, request, *args, **kwargs)
```

## Possíveis Causas do Problema

### 1. Problema no Contexto da Loja
- `get_current_loja_id()` pode estar retornando None ou ID errado
- Middleware `TenantMiddleware` pode não estar setando o contexto corretamente

### 2. Problema na Verificação do Owner
- `loja.owner_id` pode não corresponder a `request.user.id`
- Pode haver múltiplos usuários com mesmo email
- Cache do middleware pode estar desatualizado

### 3. Problema com VendedorUsuario
- Owner pode ter registro de VendedorUsuario vinculado
- Função `is_vendedor_usuario()` pode estar retornando True incorretamente

## Diagnóstico

### Endpoint de Debug Criado
```
GET /api/crm-vendas/debug-permissions/
```

Retorna:
- user_id, username, email
- loja_id, loja_nome, loja_owner_id
- is_owner (comparação direta)
- vendedor_id
- is_vendedor_usuario
- vendedor_usuario (registro VendedorUsuario se existir)
- todos_vendedor_usuarios (lista completa)

### Como Testar
1. Fazer login como Luiz Henrique Felix
2. Acessar: https://lwksistemas-38ad47519238.herokuapp.com/api/crm-vendas/debug-permissions/
3. Verificar os valores retornados

## Soluções Possíveis

### Solução 1: Corrigir Lógica de is_vendedor_usuario
Se o owner tem VendedorUsuario vinculado, a função deve retornar False mesmo assim.

```python
def is_vendedor_usuario(request):
    # SEMPRE verificar owner PRIMEIRO
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if loja and loja.owner_id == request.user.id:
        return False  # Owner NUNCA é vendedor
    
    # Depois verificar VendedorUsuario
    vu = VendedorUsuario.objects.using('default').filter(
        user=request.user,
        loja_id=loja_id,
    ).first()
    return vu is not None
```

### Solução 2: Adicionar Verificação Extra no Decorator
Adicionar log de debug para identificar onde está falhando:

```python
def require_admin_access(message='...'):
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            loja_id = get_current_loja_id()
            logger.debug(f'require_admin_access: loja_id={loja_id}, user_id={request.user.id}')
            
            if loja_id:
                loja = Loja.objects.using('default').filter(id=loja_id).first()
                logger.debug(f'require_admin_access: loja.owner_id={loja.owner_id if loja else None}')
                
                if loja and loja.owner_id == request.user.id:
                    logger.debug('require_admin_access: OWNER - acesso permitido')
                    return func(self, request, *args, **kwargs)
            
            is_vend = is_vendedor_usuario(request)
            logger.debug(f'require_admin_access: is_vendedor_usuario={is_vend}')
            
            if is_vend:
                logger.debug('require_admin_access: VENDEDOR - acesso negado')
                return Response({'detail': message}, status=403)
            
            return func(self, request, *args, **kwargs)
```

### Solução 3: Limpar Cache do Middleware
Se o problema for cache:

```python
# Limpar cache do navegador
# Fazer logout e login novamente
# Verificar se loja_id está correto no contexto
```

## Próximos Passos

1. ✅ Deploy do endpoint de debug (v1185)
2. ⏳ Testar endpoint e verificar valores retornados
3. ⏳ Identificar causa raiz do problema
4. ⏳ Implementar correção apropriada
5. ⏳ Testar acesso às configurações novamente

## Observações
- Código de permissões parece correto na teoria
- Problema pode estar na execução ou no contexto
- Endpoint de debug vai revelar a causa exata
