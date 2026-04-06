# Correções Aplicadas - Hero Imagens

## Problema Identificado

Após análise do código, identifiquei os seguintes problemas:

### 1. Botão de Remover Imagem (X) Invisível
**Arquivo**: `frontend/components/ImageUpload.tsx`

**Problema**: O botão X vermelho para remover a imagem só aparecia quando o usuário passava o mouse sobre a imagem (hover). Em dispositivos móveis ou quando o usuário não sabia que precisava passar o mouse, o botão ficava invisível.

**Solução Aplicada**: Removi as classes `opacity-0 group-hover:opacity-100` e adicionei `shadow-lg z-10` para tornar o botão sempre visível.

```tsx
// ANTES:
className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"

// DEPOIS:
className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 shadow-lg z-10"
```

### 2. Erro no Filtro de Busca
**Arquivo**: `frontend/app/(dashboard)/superadmin/homepage/page.tsx`

**Problema**: O filtro de busca tentava acessar `h.titulo.toLowerCase()` mas o campo `titulo` pode ser uma string vazia ou undefined, causando erro JavaScript que impedia a lista de ser renderizada.

**Solução Aplicada**: Adicionei verificação para garantir que `titulo` seja tratado como string vazia se for undefined.

```tsx
// ANTES:
const matchSearch = h.titulo.toLowerCase().includes(searchHeroImg.toLowerCase());

// DEPOIS:
const matchSearch = (h.titulo || '').toLowerCase().includes(searchHeroImg.toLowerCase());
```

### 3. Logs de Debug Adicionados
**Arquivo**: `frontend/app/(dashboard)/superadmin/homepage/page.tsx`

**Adicionado**: Logs no console para facilitar o diagnóstico:

```tsx
// Log quando carregar dados da API
console.log('🖼️ API Response hero-imagens:', heroImgRes.data);
console.log('🖼️ Parsed heroImgList:', heroImgList);

// Log quando o estado mudar
useEffect(() => {
  console.log('🖼️ Hero Imagens carregadas:', heroImagens);
  console.log('🖼️ Total de imagens:', heroImagens.length);
  console.log('🖼️ Imagens filtradas:', filteredHeroImagens.length);
}, [heroImagens, filteredHeroImagens]);
```

## Como Testar as Correções

### Passo 1: Fazer Deploy das Alterações

```bash
# Commit e push das alterações
git add .
git commit -m "fix: corrige visualização e remoção de imagens do hero"
git push

# Deploy no Vercel (frontend)
# O Vercel deve fazer deploy automático ao detectar o push
```

### Passo 2: Testar no Navegador

1. Acesse: https://lwksistemas.com.br/superadmin/homepage
2. Faça login como superadmin
3. Clique na aba "🖼️ Imagens"
4. Abra o DevTools (F12) e vá na aba "Console"

### Passo 3: Verificar Logs

No console, você deve ver:
```
🖼️ API Response hero-imagens: [...]
🖼️ Parsed heroImgList: [...]
🖼️ Hero Imagens carregadas: [...]
🖼️ Total de imagens: X
🖼️ Imagens filtradas: X
```

### Passo 4: Testar Funcionalidades

#### A. Adicionar Nova Imagem
1. Clique em "Nova Imagem"
2. Faça upload de uma imagem via Cloudinary
3. Adicione um título (opcional)
4. Clique em "Salvar"
5. Verifique se a imagem aparece na lista

#### B. Remover Imagem (Botão X)
1. Clique em "Editar" em uma imagem existente
2. Você deve ver a imagem com um botão X vermelho no canto superior direito
3. Clique no X para remover a imagem
4. A imagem deve desaparecer do preview

#### C. Deletar Imagem da Lista
1. Na lista de imagens, cada item deve ter um botão de lixeira (vermelho)
2. Clique no botão de lixeira
3. Confirme a exclusão
4. A imagem deve ser removida da lista

## Possíveis Problemas Restantes

Se após essas correções as imagens ainda não aparecerem, pode ser:

### 1. Problema no Backend
- Verificar se a tabela `homepage_hero_imagem` existe no banco de dados
- Verificar se há imagens cadastradas
- Verificar se a API `/superadmin/homepage/hero-imagens/` está retornando dados

**Como verificar**:
```bash
# No servidor de produção (Heroku)
heroku run python manage.py shell --app lwksistemas

# Depois execute:
from homepage.models import HeroImagem
print("Total:", HeroImagem.objects.count())
for img in HeroImagem.objects.all():
    print(f"ID: {img.id}, Titulo: {img.titulo}, Ativo: {img.ativo}")
```

### 2. Problema de Permissões
- Verificar se o usuário logado tem permissão de superadmin
- Verificar se o token JWT está válido

### 3. Problema de CORS ou API
- Verificar se a API está respondendo corretamente
- Verificar se não há erro 401, 403 ou 500 na aba Network do DevTools

## Próximos Passos

1. ✅ Correções aplicadas no código
2. ⏳ Fazer deploy das alterações
3. ⏳ Testar no ambiente de produção
4. ⏳ Verificar logs no console
5. ⏳ Reportar resultados

## Arquivos Modificados

- `frontend/components/ImageUpload.tsx` - Botão X sempre visível
- `frontend/app/(dashboard)/superadmin/homepage/page.tsx` - Correção no filtro + logs de debug

## Observações

- O botão de deletar da lista (ícone de lixeira) já estava funcionando corretamente
- O problema principal era o botão X invisível e o erro no filtro de busca
- Os logs adicionados vão ajudar a diagnosticar problemas futuros
