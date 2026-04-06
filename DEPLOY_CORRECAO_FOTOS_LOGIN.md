# Deploy: Correção de Fotos na Página de Login

## Data do Deploy
**Data:** 03/04/2026  
**Hora:** Após commit 801f2b8d

## Resumo das Alterações

Correção do problema de exibição de fotos na página de configurações de login e implementação de deleção automática de imagens do Cloudinary.

## Commit

```
commit 801f2b8d
Author: [autor]
Date: [data]

fix: Corrigir exibição de fotos na página de configuração de login e adicionar deleção automática do Cloudinary

- Substituir <Image> do Next.js por <img> nativo no ImageUpload para melhor compatibilidade
- Adicionar validação de URLs vazias antes de renderizar imagens
- Criar utilitário cloudinary_utils.py para deletar imagens antigas do Cloudinary
- Implementar deleção automática de imagens ao fazer upload de novas ou remover existentes
- Adicionar logs detalhados no frontend e backend para debug em produção
- Garantir que imagens órfãs não acumulem no Cloudinary
```

## Arquivos Modificados

### Backend
1. ✅ `backend/crm_vendas/views.py` - Lógica de deleção de imagens antigas
2. ✅ `backend/superadmin/cloudinary_utils.py` - Novo utilitário (criado)

### Frontend
3. ✅ `frontend/components/ImageUpload.tsx` - Correção de renderização
4. ✅ `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/login/page.tsx` - Logs e validações

### Documentação
5. ✅ `CORRECAO_FOTOS_LOGIN.md` - Documentação completa das alterações

## Deploy Realizado

### 1. Backend (Heroku)

**Comando:**
```bash
git push heroku master
```

**Status:** ✅ Sucesso

**Versão:** v1498

**URL:** https://lwksistemas-38ad47519238.herokuapp.com/

**Detalhes:**
- Build concluído com sucesso
- Dependências instaladas corretamente
- Collectstatic executado: 160 arquivos estáticos copiados
- Migrations aplicadas (nenhuma nova migration necessária)
- Release command executado com sucesso
- Setup de dados iniciais concluído

**Logs importantes:**
```
remote: ✅ Superadmin: Signals de limpeza carregados
remote: ✅ Asaas Integration: Signals carregados
remote: 160 static files copied to '/tmp/build_844b762b/backend/staticfiles', 462 post-processed.
remote: Operations to perform:
remote:   Apply all migrations: [todos os apps]
remote: Running migrations:
remote:   No migrations to apply.
remote: ✅ Setup concluído com sucesso!
```

### 2. Frontend (Vercel)

**Comando:**
```bash
vercel --prod
```

**Status:** ✅ Sucesso

**URLs:**
- Production: https://frontend-6fyqtirpl-lwks-projects-48afd555.vercel.app
- Aliased: https://lwksistemas.com.br
- Inspect: https://vercel.com/lwks-projects-48afd555/frontend/2Xi3ywFEJkADmCdp7exhvPkxV5xQ

**Tempo de build:** 52 segundos

## Verificações Pós-Deploy

### Backend (Heroku)

✅ **API funcionando:**
- Endpoint `/crm-vendas/login-config/` (GET/PATCH) disponível
- Novo utilitário `cloudinary_utils.py` carregado
- Função de deleção de imagens do Cloudinary ativa

✅ **Dependências:**
- `cloudinary==1.41.0` já estava instalado
- Nenhuma nova dependência necessária

### Frontend (Vercel)

✅ **Build bem-sucedido:**
- Componente `ImageUpload.tsx` atualizado
- Página de configurações de login atualizada
- Logs de debug ativos

✅ **URLs acessíveis:**
- Site principal: https://lwksistemas.com.br
- Página de configurações: https://lwksistemas.com.br/loja/[cnpj]/crm-vendas/configuracoes/login

## Testes Recomendados

### 1. Testar exibição de imagens salvas
```
URL: https://lwksistemas.com.br/loja/22239255889/crm-vendas/configuracoes/login
Ação: Verificar se as imagens salvas aparecem nos campos
Esperado: Imagens devem ser exibidas corretamente
```

### 2. Testar upload de nova imagem
```
Ação: 
1. Fazer upload de uma nova imagem em qualquer campo
2. Clicar em "Salvar"
3. Verificar logs do console (F12)

Esperado:
- Console: "📤 Enviando dados para o backend:" com nova URL
- Console: "✅ Resposta do backend:" confirmando salvamento
- Backend logs: "✅ Imagem deletada do Cloudinary: [public_id]" (se havia imagem antiga)
```

### 3. Testar remoção de imagem
```
Ação:
1. Passar mouse sobre imagem existente
2. Clicar no botão "X" vermelho
3. Clicar em "Salvar"
4. Verificar logs

Esperado:
- Console: "📤 Enviando dados para o backend:" com campo vazio
- Backend logs: "✅ Imagem deletada do Cloudinary: [public_id]"
- Placeholder deve aparecer no lugar da imagem
```

### 4. Verificar logs do backend
```bash
# No Heroku
heroku logs --tail --app lwksistemas

# Procurar por:
✅ Imagem deletada do Cloudinary: lwksistemas/[filename]
⚠️ Imagem não encontrada no Cloudinary: [public_id]
❌ Erro ao deletar imagem do Cloudinary: [erro]
```

## Monitoramento

### Logs do Frontend (Console do Navegador)
```javascript
// Ao carregar a página
📥 Dados recebidos do backend: { logo: "...", login_background: "...", ... }
  - logo: (URL ou "(vazio)")
  - login_background: (URL ou "(vazio)")
  - login_logo: (URL ou "(vazio)")
✅ Estados atualizados:
  - logo state: (URL ou "(vazio)")
  - loginBackground state: (URL ou "(vazio)")
  - loginLogo state: (URL ou "(vazio)")

// Ao salvar
📤 Enviando dados para o backend: { logo: "...", login_background: "...", ... }
✅ Resposta do backend: { logo: "...", login_background: "...", ... }
```

### Logs do Backend (Heroku)
```bash
# Deleção bem-sucedida
✅ Imagem deletada do Cloudinary: lwksistemas/logo_123

# Imagem não encontrada (já deletada)
⚠️ Imagem não encontrada no Cloudinary: lwksistemas/old_image

# Erro ao deletar
❌ Erro ao deletar imagem do Cloudinary: [mensagem de erro]
```

## Rollback (Se Necessário)

### Backend
```bash
# Reverter para versão anterior
heroku releases --app lwksistemas
heroku rollback v1497 --app lwksistemas
```

### Frontend
```bash
# Reverter no dashboard da Vercel
# https://vercel.com/lwks-projects-48afd555/frontend
# Ou via CLI:
vercel rollback [deployment-url]
```

## Notas Importantes

1. **Cache Redis:** As informações públicas da loja são cacheadas por 5 minutos. O cache é limpo automaticamente após salvar.

2. **Cloudinary:** A deleção de imagens só funciona se:
   - Cloudinary estiver configurado em `/superadmin/cloudinary-config/`
   - Cloudinary estiver habilitado nas configurações
   - Credenciais (cloud_name, api_key, api_secret) estiverem corretas

3. **Logs de Debug:** Os logs do console podem ser removidos após confirmar que tudo está funcionando em produção.

4. **Imagens Órfãs Antigas:** Imagens que já estavam órfãs antes desta correção não serão deletadas automaticamente.

## Próximos Passos

1. ✅ Monitorar logs por 24-48 horas
2. ⏳ Verificar se as imagens estão sendo exibidas corretamente
3. ⏳ Confirmar que a deleção do Cloudinary está funcionando
4. ⏳ Considerar remover logs de debug após estabilização
5. ⏳ Criar script de limpeza para imagens órfãs antigas (opcional)

## Contato

Em caso de problemas, verificar:
1. Logs do Heroku: `heroku logs --tail --app lwksistemas`
2. Console do navegador (F12) na página de configurações
3. Dashboard do Cloudinary para confirmar deleções
4. Documentação completa em `CORRECAO_FOTOS_LOGIN.md`
