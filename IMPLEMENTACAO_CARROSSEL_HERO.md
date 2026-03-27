# Implementação do Carrossel de Imagens do Hero

## Resumo
Sistema de carrossel automático de imagens de fundo na seção Hero da homepage implementado com sucesso.

## Deploy
- **Backend**: v1388 (Heroku)
- **Frontend**: Deploy concluído (Vercel)

## O que foi implementado

### Backend

1. **Modelo HeroImagem** (`backend/homepage/models.py`)
   - Campos: imagem (URL), titulo, ordem, ativo
   - Tabela: `homepage_hero_imagem`

2. **Migration** (`backend/homepage/migrations/0039_heroimagem.py`)
   - Criada e aplicada com sucesso no Heroku

3. **ViewSet** (`backend/homepage/views_admin.py`)
   - `HeroImagemViewSet` para CRUD completo
   - Endpoint: `/api/superadmin/homepage/hero-imagens/`
   - Permissões: IsAuthenticated + IsSuperAdmin

4. **Endpoint Público** (`backend/homepage/views.py`)
   - Retorna `hero_imagens` no endpoint `/api/homepage/`
   - Apenas imagens ativas, ordenadas por ordem/id

### Frontend

1. **Componente Hero** (`frontend/app/components/Hero.tsx`)
   - Carrossel automático (muda a cada 5 segundos)
   - Imagens cobrem toda a seção como fundo
   - Overlay azul semi-transparente sobre as imagens
   - Indicadores de navegação (dots) na parte inferior
   - Transição suave entre imagens

2. **Página de Configuração** (`frontend/app/(dashboard)/superadmin/homepage/page.tsx`)
   - Nova aba "Imagens Hero" adicionada
   - Interface completa para gerenciar imagens:
     - Adicionar novas imagens
     - Editar imagens existentes
     - Reordenar imagens (setas para cima/baixo)
     - Ativar/desativar imagens
     - Excluir imagens
     - Busca por título
     - Filtro por status (ativo/inativo)
     - Seleção em lote com ações múltiplas
   - Preview das imagens na lista
   - Upload via Cloudinary integrado

## Como usar

### Para o Superadmin

1. Acesse: https://lwksistemas.com.br/superadmin/homepage
2. Clique na aba "Imagens Hero"
3. Clique em "Nova Imagem"
4. Faça upload da imagem (recomendado: 1920x1080px, proporção 16:9)
5. Adicione um título opcional
6. Salve

### Funcionalidades

- **Carrossel Automático**: As imagens mudam automaticamente a cada 5 segundos
- **Indicadores**: Dots na parte inferior mostram qual imagem está ativa
- **Navegação Manual**: Clique nos dots para ir para uma imagem específica
- **Ordem Personalizável**: Use as setas para reordenar as imagens
- **Ativar/Desativar**: Controle quais imagens aparecem no carrossel
- **Ações em Lote**: Selecione múltiplas imagens para ativar/desativar/excluir

## Comportamento

- Se não houver imagens cadastradas, o Hero exibe apenas o gradiente azul padrão
- Se houver apenas 1 imagem, ela fica estática (sem carrossel)
- Se houver 2 ou mais imagens ativas, o carrossel inicia automaticamente
- As imagens cobrem toda a seção Hero com um overlay azul semi-transparente
- O texto do Hero (título, subtítulo, botões) fica sempre visível sobre as imagens

## Endpoints da API

### Público (sem autenticação)
- `GET /api/homepage/` - Retorna hero_imagens junto com outros dados da homepage

### Admin (requer autenticação de superadmin)
- `GET /api/superadmin/homepage/hero-imagens/` - Lista todas as imagens
- `POST /api/superadmin/homepage/hero-imagens/` - Cria nova imagem
- `GET /api/superadmin/homepage/hero-imagens/{id}/` - Detalhes de uma imagem
- `PATCH /api/superadmin/homepage/hero-imagens/{id}/` - Atualiza imagem
- `DELETE /api/superadmin/homepage/hero-imagens/{id}/` - Exclui imagem

## Estrutura de Dados

```json
{
  "id": 1,
  "imagem": "https://res.cloudinary.com/.../imagem.jpg",
  "titulo": "Banner Principal",
  "ordem": 0,
  "ativo": true,
  "created_at": "2025-03-27T10:00:00Z",
  "updated_at": "2025-03-27T10:00:00Z"
}
```

## Próximos Passos (Opcional)

- Adicionar velocidade de transição configurável
- Adicionar efeitos de transição diferentes (fade, slide, etc.)
- Adicionar suporte para vídeos de fundo
- Adicionar textos personalizados por imagem (título/subtítulo diferentes para cada slide)

## Status
✅ Implementação completa e funcional
✅ Deploy realizado (backend v1388 + frontend)
✅ Pronto para uso em produção
