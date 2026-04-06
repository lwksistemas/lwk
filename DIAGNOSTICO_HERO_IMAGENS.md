# Diagnóstico: Imagens do Hero não aparecem e botão remover ausente

## Problema Relatado
1. As imagens salvas não estão aparecendo na lista
2. A opção de remover a foto não está aparecendo

## Análise do Código

### ✅ Funcionalidades IMPLEMENTADAS corretamente:

1. **Botão de remover imagem (X vermelho)** - `frontend/components/ImageUpload.tsx` linhas 217-227
   - Aparece quando você passa o mouse sobre a imagem (hover)
   - Classe CSS: `opacity-0 group-hover:opacity-100`
   - **POSSÍVEL PROBLEMA**: O botão só aparece no hover, pode não estar visível em mobile

2. **Botão de deletar da lista** - `frontend/components/superadmin/BulkActionList.tsx` linhas 213-220
   - Ícone de lixeira (Trash2) vermelho
   - Está implementado e funcional

3. **API de Hero Imagens** - `backend/homepage/views_admin.py`
   - ViewSet completo com CRUD
   - Endpoint: `/superadmin/homepage/hero-imagens/`

## Possíveis Causas do Problema

### 1. Imagens não aparecem na lista

**Teste 1: Verificar se as imagens estão no banco de dados**
```bash
# No terminal, dentro da pasta backend:
python manage.py shell

# Depois execute:
from homepage.models import HeroImagem
print("Total de imagens:", HeroImagem.objects.count())
print("Imagens ativas:", HeroImagem.objects.filter(ativo=True).count())
for img in HeroImagem.objects.all():
    print(f"ID: {img.id}, Titulo: {img.titulo}, Ativo: {img.ativo}")
    print(f"URL: {img.imagem}")
```

**Teste 2: Verificar resposta da API**
```bash
# Abra o navegador e acesse (logado como superadmin):
https://lwksistemas.com.br/superadmin/homepage/hero-imagens/

# Deve retornar um JSON com a lista de imagens
```

**Teste 3: Verificar console do navegador**
```
1. Abra https://lwksistemas.com.br/superadmin/homepage
2. Abra o DevTools (F12)
3. Vá na aba "Console"
4. Vá na aba "🖼️ Imagens"
5. Procure por erros em vermelho
6. Procure pela requisição GET /superadmin/homepage/hero-imagens/
```

### 2. Botão de remover não aparece

**Problema A: Botão X no ImageUpload (dentro do modal)**
- O botão só aparece quando você passa o mouse sobre a imagem
- Em dispositivos móveis, pode não funcionar (não tem hover)
- **Solução**: Tornar o botão sempre visível

**Problema B: Botão de deletar na lista**
- Deve estar visível sempre
- Se não está aparecendo, pode ser problema de CSS ou de dados

## Soluções Propostas

### Solução 1: Tornar botão X sempre visível (não apenas no hover)

Arquivo: `frontend/components/ImageUpload.tsx`

Mudar a linha 220 de:
```tsx
className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
```

Para:
```tsx
className="absolute -top-2 -right-2 p-1 bg-red-500 text-white rounded-full hover:bg-red-600 shadow-lg"
```

### Solução 2: Adicionar logs de debug

Adicionar no arquivo `frontend/app/(dashboard)/superadmin/homepage/page.tsx` após a linha 90:

```tsx
useEffect(() => {
  console.log('🖼️ Hero Imagens carregadas:', heroImagens);
  console.log('🖼️ Total:', heroImagens.length);
}, [heroImagens]);
```

### Solução 3: Verificar se a API está retornando dados

No arquivo `frontend/app/(dashboard)/superadmin/homepage/page.tsx`, linha 155, adicionar log:

```tsx
const heroImgList = Array.isArray(heroImgRes.data) ? heroImgRes.data : heroImgRes.data?.results ?? [];
console.log('🖼️ API Response:', heroImgRes.data);
console.log('🖼️ Parsed list:', heroImgList);
setHeroImagens(heroImgList);
```

## Checklist de Verificação

- [ ] Verificar se há imagens no banco de dados
- [ ] Verificar se a API `/superadmin/homepage/hero-imagens/` retorna dados
- [ ] Verificar console do navegador por erros
- [ ] Verificar se o botão X aparece ao passar o mouse sobre a imagem
- [ ] Verificar se o botão de lixeira aparece na lista de imagens
- [ ] Testar em diferentes navegadores (Chrome, Firefox, Safari)
- [ ] Testar em dispositivo móvel

## Próximos Passos

1. Execute os testes acima
2. Compartilhe os resultados (screenshots ou logs)
3. Aplicarei as correções necessárias baseado nos resultados
