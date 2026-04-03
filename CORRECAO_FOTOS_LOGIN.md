# Correção: Fotos não aparecem na página de configuração de login

## Problema Identificado

Em produção (https://lwksistemas.com.br/loja/22239255889/crm-vendas/configuracoes/login), as fotos salvas não estavam aparecendo nos campos:
- Logo da loja (principal)
- Imagem de fundo da tela de login
- Logo da tela de login

Além disso, ao remover uma foto, ela não era deletada do Cloudinary, apenas a URL era removida do banco de dados.

## Causas Raiz

### 1. Problema de renderização no componente ImageUpload
- O componente usava `<Image>` do Next.js com propriedade `fill`
- Quando a URL estava vazia ou havia erro de carregamento, o componente não tratava corretamente
- Isso causava problemas de exibição das imagens salvas

### 2. Falta de exclusão de imagens do Cloudinary
- Quando o usuário removia uma foto, apenas a URL era removida do banco
- As imagens ficavam órfãs no Cloudinary, ocupando espaço desnecessário
- Não havia lógica para deletar a imagem antiga ao fazer upload de uma nova

### 3. Validação insuficiente de URLs vazias
- O código não validava adequadamente se a URL estava vazia antes de tentar renderizar
- Faltavam logs detalhados para debug em produção

## Correções Implementadas

### 1. Correção do componente ImageUpload (`frontend/components/ImageUpload.tsx`)

**Antes:**
```tsx
{value ? (
  <div className="relative group w-full sm:w-auto shrink-0">
    <div className={`relative ${previewFrameClass...}`}>
      <Image
        src={value}
        alt="Preview"
        fill
        className={previewImgClass}
        sizes={isWideHero ? '(max-width: 768px) 100vw, 28rem' : '128px'}
        unoptimized
      />
    </div>
    ...
  </div>
) : (
  <div>Placeholder</div>
)}
```

**Depois:**
```tsx
{value && value.trim() !== '' ? (
  <div className="relative group w-full sm:w-auto shrink-0">
    <div className={`relative ${previewFrameClass...}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={value}
        alt="Preview"
        className={previewImgClass}
        onError={(e) => {
          console.error('Erro ao carregar imagem:', value);
          e.currentTarget.style.display = 'none';
        }}
      />
    </div>
    ...
  </div>
) : (
  <div>Placeholder</div>
)}
```

**Mudanças:**
- Substituído `<Image>` do Next.js por `<img>` nativo (mais confiável para URLs externas)
- Adicionada validação `value && value.trim() !== ''` para garantir que a URL não está vazia
- Adicionado handler `onError` para tratar falhas de carregamento
- Removido import desnecessário do `Image` do Next.js

### 2. Criação de utilitário para deletar imagens do Cloudinary (`backend/superadmin/cloudinary_utils.py`)

Novo arquivo com duas funções principais:

#### `extract_public_id_from_url(cloudinary_url: str) -> Optional[str]`
Extrai o public_id de uma URL do Cloudinary para poder deletá-la.

Exemplo:
- URL: `https://res.cloudinary.com/dzrdbw74w/image/upload/v1234567890/lwksistemas/logo.png`
- Public ID: `lwksistemas/logo`

#### `delete_cloudinary_image(cloudinary_url: str) -> bool`
Deleta uma imagem do Cloudinary usando sua URL.

Funcionalidades:
- Valida se a URL é do Cloudinary
- Verifica se o Cloudinary está habilitado nas configurações
- Extrai o public_id da URL
- Deleta a imagem usando a API do Cloudinary
- Retorna `True` se deletado com sucesso ou se já não existir
- Loga todas as operações para debug

### 3. Atualização da view LoginConfigView (`backend/crm_vendas/views.py`)

**Antes:**
```python
if 'login_background' in request.data:
    val = (request.data.get('login_background') or '').strip()
    loja.login_background = val[:200] if val else ''
    update_fields.append('login_background')
```

**Depois:**
```python
if 'login_background' in request.data:
    val = (request.data.get('login_background') or '').strip()
    old_background = (loja.login_background or '').strip()
    
    # Se mudou e tinha uma imagem antiga, deletar do Cloudinary
    if old_background and old_background != val and 'cloudinary.com' in old_background:
        delete_cloudinary_image(old_background)
    
    loja.login_background = val[:200] if val else ''
    update_fields.append('login_background')
```

**Mudanças:**
- Antes de atualizar, verifica se havia uma imagem antiga
- Se a URL mudou (nova imagem ou remoção), deleta a imagem antiga do Cloudinary
- Aplica a mesma lógica para `logo`, `login_background` e `login_logo`
- Mantém o cache sendo limpo após a atualização

### 4. Melhorias na página de configuração (`frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/login/page.tsx`)

**Logs detalhados adicionados:**

```typescript
const loadConfig = async () => {
  // ...
  console.log('📥 Dados recebidos do backend:', data);
  console.log('  - logo:', data.logo || '(vazio)');
  console.log('  - login_background:', data.login_background || '(vazio)');
  console.log('  - login_logo:', data.login_logo || '(vazio)');
  
  // Garantir que valores vazios sejam strings vazias
  const logoValue = (data.logo ?? '').toString().trim();
  const backgroundValue = (data.login_background ?? '').toString().trim();
  const loginLogoValue = (data.login_logo ?? '').toString().trim();
  
  console.log('✅ Estados atualizados:');
  console.log('  - logo state:', logoValue || '(vazio)');
  console.log('  - loginBackground state:', backgroundValue || '(vazio)');
  console.log('  - loginLogo state:', loginLogoValue || '(vazio)');
};

const saveConfig = async () => {
  // ...
  console.log('📤 Enviando dados para o backend:', payload);
  const response = await apiClient.patch('/crm-vendas/login-config/', payload);
  console.log('✅ Resposta do backend:', response.data);
  
  // Recarregar configurações para garantir sincronização
  await loadConfig();
};
```

**Benefícios:**
- Logs detalhados para debug em produção
- Garantia de que valores vazios são tratados como strings vazias
- Recarga automática após salvar para sincronizar estado

## Como Testar

### 1. Testar exibição de imagens salvas
1. Acesse: https://lwksistemas.com.br/loja/22239255889/crm-vendas/configuracoes/login
2. Abra o Console do navegador (F12)
3. Verifique os logs:
   - `📥 Dados recebidos do backend:` - deve mostrar as URLs das imagens
   - `✅ Estados atualizados:` - deve mostrar os valores nos estados React
4. As imagens devem aparecer nos campos de upload

### 2. Testar upload de nova imagem
1. Clique em "Escolher Imagem" em qualquer campo
2. Faça upload de uma nova imagem
3. Clique em "Salvar"
4. Verifique no console:
   - `📤 Enviando dados para o backend:` - deve mostrar a nova URL
   - `✅ Resposta do backend:` - deve confirmar o salvamento
5. A imagem antiga deve ser deletada do Cloudinary (verificar logs do backend)

### 3. Testar remoção de imagem
1. Passe o mouse sobre uma imagem existente
2. Clique no botão "X" vermelho que aparece
3. Clique em "Salvar"
4. Verifique no console:
   - `📤 Enviando dados para o backend:` - campo deve estar vazio
5. A imagem deve ser deletada do Cloudinary (verificar logs do backend)
6. O placeholder deve aparecer no lugar da imagem

### 4. Verificar logs do backend
No servidor, verificar logs do Django:
```
✅ Imagem deletada do Cloudinary: lwksistemas/logo
⚠️ Imagem não encontrada no Cloudinary: lwksistemas/old-image
❌ Erro ao deletar imagem do Cloudinary: ...
```

## Requisitos

### Backend
- Biblioteca `cloudinary` instalada: `pip install cloudinary`
- Configuração do Cloudinary preenchida em `/superadmin/cloudinary-config/`
- Cloudinary habilitado nas configurações

### Frontend
- Nenhuma dependência adicional necessária

## Notas Importantes

1. **Cache Redis**: As informações públicas da loja são cacheadas por 5 minutos. Após salvar, o cache é limpo automaticamente.

2. **Cloudinary não configurado**: Se o Cloudinary não estiver configurado ou habilitado, as imagens antigas não serão deletadas, mas o sistema continuará funcionando normalmente (apenas removendo a URL do banco).

3. **Imagens já órfãs**: Imagens que já estavam órfãs no Cloudinary antes desta correção não serão deletadas automaticamente. Para limpeza, será necessário um script separado.

4. **Segurança**: A função de deleção só funciona para URLs do Cloudinary configurado. URLs externas são ignoradas.

5. **Logs em produção**: Os logs do console podem ser removidos após confirmar que tudo está funcionando corretamente em produção.

## Arquivos Modificados

1. ✅ `frontend/components/ImageUpload.tsx` - Correção de renderização
2. ✅ `backend/superadmin/cloudinary_utils.py` - Novo arquivo com utilitários
3. ✅ `backend/crm_vendas/views.py` - Adição de lógica de deleção
4. ✅ `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/login/page.tsx` - Logs e validações

## Próximos Passos (Opcional)

1. **Script de limpeza**: Criar script para identificar e deletar imagens órfãs no Cloudinary
2. **Monitoramento**: Adicionar métricas de uso de storage do Cloudinary
3. **Otimização**: Implementar compressão automática de imagens no upload
4. **Backup**: Considerar backup de imagens antes de deletar (se necessário)
