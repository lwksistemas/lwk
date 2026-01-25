# ✅ CHECKLIST DE IMPLEMENTAÇÃO

## FASE 1: PREPARAÇÃO (Dia 1)

### Backend
- [ ] Criar branch `refactor/consolidate-models`
- [ ] Criar app `core` com `python manage.py startapp core`
- [ ] Adicionar `core` a `INSTALLED_APPS`
- [ ] Criar arquivo `backend/core/models.py`
- [ ] Criar arquivo `backend/core/views.py`
- [ ] Criar arquivo `backend/core/serializers.py`
- [ ] Documentar estrutura em `backend/core/README.md`

### Frontend
- [ ] Criar branch `refactor/consolidate-components`
- [ ] Criar diretório `frontend/components/auth/`
- [ ] Criar diretório `frontend/components/layouts/`
- [ ] Criar diretório `frontend/components/common/`

---

## FASE 2: MODELOS BASE (Dias 2-3)

### Backend - Criar Modelos Base

- [ ] Implementar `BaseModel` em `core/models.py`
  ```python
  class BaseModel(models.Model):
      is_active = models.BooleanField(default=True)
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)
      
      class Meta:
          abstract = True
  ```

- [ ] Implementar `BaseCategoria`
- [ ] Implementar `BaseCliente`
- [ ] Implementar `BasePedido`
- [ ] Implementar `BaseItemPedido`
- [ ] Implementar `BaseFuncionario`

### Backend - Refatorar Modelos Existentes

#### App: servicos
- [ ] Refatorar `Categoria` para herdar de `BaseCategoria`
- [ ] Refatorar `Cliente` para herdar de `BaseCliente`
- [ ] Refatorar `Funcionario` para herdar de `BaseFuncionario`
- [ ] Executar `makemigrations servicos`
- [ ] Executar `migrate servicos`
- [ ] Testar endpoints

#### App: restaurante
- [ ] Refatorar `Categoria` para herdar de `BaseCategoria`
- [ ] Refatorar `Cliente` para herdar de `BaseCliente`
- [ ] Refatorar `Pedido` para herdar de `BasePedido`
- [ ] Refatorar `ItemPedido` para herdar de `BaseItemPedido`
- [ ] Refatorar `Funcionario` para herdar de `BaseFuncionario`
- [ ] Executar `makemigrations restaurante`
- [ ] Executar `migrate restaurante`
- [ ] Testar endpoints

#### App: ecommerce
- [ ] Refatorar `Categoria` para herdar de `BaseCategoria`
- [ ] Refatorar `Cliente` para herdar de `BaseCliente`
- [ ] Refatorar `Pedido` para herdar de `BasePedido`
- [ ] Refatorar `ItemPedido` para herdar de `BaseItemPedido`
- [ ] Executar `makemigrations ecommerce`
- [ ] Executar `migrate ecommerce`
- [ ] Testar endpoints

#### App: crm_vendas
- [ ] Refatorar `Cliente` para herdar de `BaseCliente`
- [ ] Executar `makemigrations crm_vendas`
- [ ] Executar `migrate crm_vendas`
- [ ] Testar endpoints

---

## FASE 3: VIEWSETS GENÉRICOS (Dias 4-5)

### Backend - Criar ViewSet Base

- [ ] Implementar `BaseModelViewSet` em `core/views.py`
  ```python
  class BaseModelViewSet(viewsets.ModelViewSet):
      permission_classes = [permissions.IsAuthenticated]
      
      def get_queryset(self):
          return self.queryset.filter(is_active=True)
  ```

### Backend - Refatorar ViewSets

#### App: servicos
- [ ] Refatorar `CategoriaViewSet` para herdar de `BaseModelViewSet`
- [ ] Refatorar `ClienteViewSet` para herdar de `BaseModelViewSet`
- [ ] Refatorar `ProfissionalViewSet` para herdar de `BaseModelViewSet`
- [ ] Refatorar `FuncionarioViewSet` para herdar de `BaseModelViewSet`
- [ ] Testar endpoints

#### App: restaurante
- [ ] Refatorar `CategoriaViewSet` para herdar de `BaseModelViewSet`
- [ ] Refatorar `ClienteViewSet` para herdar de `BaseModelViewSet`
- [ ] Refatorar `FuncionarioViewSet` para herdar de `BaseModelViewSet`
- [ ] Testar endpoints

#### App: ecommerce
- [ ] Refatorar `CategoriaViewSet` para herdar de `BaseModelViewSet`
- [ ] Refatorar `ClienteViewSet` para herdar de `BaseModelViewSet`
- [ ] Testar endpoints

#### App: crm_vendas
- [ ] Refatorar `ClienteViewSet` para herdar de `BaseModelViewSet`
- [ ] Testar endpoints

---

## FASE 4: SETTINGS (Dia 6)

### Backend - Consolidar Configurações

- [ ] Criar `backend/config/settings_base.py`
- [ ] Mover configurações comuns para `settings_base.py`
- [ ] Atualizar `backend/config/settings.py` para importar de `settings_base.py`
- [ ] Atualizar `backend/config/settings_production.py`
- [ ] Atualizar `backend/config/settings_single_db.py`
- [ ] Atualizar `backend/config/settings_postgres.py`
- [ ] Testar com `python manage.py check`
- [ ] Testar desenvolvimento: `python manage.py runserver`
- [ ] Testar produção: `DEBUG=False python manage.py check`

---

## FASE 5: COMPONENTES REACT (Dias 7-8)

### Frontend - Criar Componentes Base

- [ ] Criar `frontend/components/auth/LoginForm.tsx`
  - [ ] Implementar formulário reutilizável
  - [ ] Suportar múltiplos tipos de usuário
  - [ ] Testar com diferentes userTypes

- [ ] Criar `frontend/components/layouts/DashboardLayout.tsx`
  - [ ] Implementar layout base
  - [ ] Incluir Header, Sidebar, Footer
  - [ ] Testar responsividade

- [ ] Criar `frontend/components/common/Header.tsx`
- [ ] Criar `frontend/components/common/Sidebar.tsx`
- [ ] Criar `frontend/components/common/Footer.tsx`

### Frontend - Refatorar Páginas

#### Auth Pages
- [ ] Refatorar `app/(auth)/login/page.tsx`
  - [ ] Usar `LoginForm` component
  - [ ] Testar login
  - [ ] Testar redirecionamento

- [ ] Refatorar `app/(auth)/loja/page.tsx`
  - [ ] Usar `LoginForm` component
  - [ ] Testar login
  - [ ] Testar redirecionamento

- [ ] Refatorar `app/(auth)/superadmin/page.tsx`
  - [ ] Usar `LoginForm` component
  - [ ] Testar login
  - [ ] Testar redirecionamento

- [ ] Refatorar `app/(auth)/suporte/page.tsx`
  - [ ] Usar `LoginForm` component
  - [ ] Testar login
  - [ ] Testar redirecionamento

#### Dashboard Pages
- [ ] Refatorar `app/(dashboard)/dashboard/page.tsx`
  - [ ] Usar `DashboardLayout` component
  - [ ] Testar layout
  - [ ] Testar responsividade

- [ ] Refatorar `app/(dashboard)/loja/page.tsx`
  - [ ] Usar `DashboardLayout` component
  - [ ] Testar layout
  - [ ] Testar responsividade

- [ ] Refatorar `app/(dashboard)/superadmin/page.tsx`
  - [ ] Usar `DashboardLayout` component
  - [ ] Testar layout
  - [ ] Testar responsividade

- [ ] Refatorar `app/(dashboard)/suporte/page.tsx`
  - [ ] Usar `DashboardLayout` component
  - [ ] Testar layout
  - [ ] Testar responsividade

---

## FASE 6: HOOKS CUSTOMIZADOS (Dia 9)

### Frontend - Criar Hooks

- [ ] Criar `frontend/hooks/use-auth.ts`
  - [ ] Implementar lógica de autenticação
  - [ ] Testar login/logout
  - [ ] Testar token refresh

- [ ] Criar `frontend/hooks/use-user.ts`
  - [ ] Implementar lógica de usuário
  - [ ] Testar carregamento de dados
  - [ ] Testar atualização de dados

- [ ] Criar `frontend/hooks/use-api.ts`
  - [ ] Implementar wrapper para chamadas API
  - [ ] Testar tratamento de erros
  - [ ] Testar loading states

### Frontend - Refatorar Componentes

- [ ] Atualizar componentes para usar novos hooks
- [ ] Remover lógica duplicada
- [ ] Testar todos os componentes

---

## FASE 7: CONSOLIDAÇÃO DE .ENV (Dia 10)

### Frontend - Consolidar Variáveis de Ambiente

- [ ] Criar `frontend/.env.example`
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_APP_NAME=LWK Sistemas
  ```

- [ ] Atualizar `frontend/.env.local`
  - [ ] Remover variáveis não utilizadas
  - [ ] Adicionar variáveis faltantes

- [ ] Atualizar `frontend/.env.production`
  - [ ] Remover variáveis não utilizadas
  - [ ] Adicionar variáveis faltantes

- [ ] Remover `frontend/.env.vercel`
- [ ] Remover `frontend/.env.local.example`
- [ ] Atualizar `.gitignore`

---

## FASE 8: LIMPEZA (Dia 11)

### Backend - Remover Código Morto

- [ ] Remover arquivos de banco de dados
  ```bash
  rm backend/db_*.sqlite3
  ```

- [ ] Remover scripts de migração duplicados
  ```bash
  rm backend/criar_banco_*.py
  rm backend/migrar_*.py
  ```

- [ ] Remover scripts de teste
  ```bash
  rm backend/testar_*.py
  rm backend/limpar_*.py
  ```

- [ ] Remover modelos antigos
  ```bash
  rm backend/*/models_single_db.py
  ```

- [ ] Atualizar `.gitignore`
  ```
  *.sqlite3
  *.pyc
  __pycache__/
  .env
  .venv/
  venv/
  ```

### Frontend - Remover Código Morto

- [ ] Remover `.env.vercel`
- [ ] Remover `.env.local.example`
- [ ] Atualizar `.gitignore`
  ```
  .env.local
  .env.production
  .next/
  .vercel/
  node_modules/
  dist/
  build/
  ```

---

## FASE 9: TESTES (Dia 12)

### Backend - Testes

- [ ] Executar testes unitários
  ```bash
  python manage.py test
  ```

- [ ] Testar endpoints com Postman/Insomnia
  - [ ] GET /api/servicos/categorias/
  - [ ] POST /api/servicos/categorias/
  - [ ] PUT /api/servicos/categorias/{id}/
  - [ ] DELETE /api/servicos/categorias/{id}/

- [ ] Testar com múltiplos bancos de dados
  - [ ] Banco default
  - [ ] Banco suporte
  - [ ] Banco loja_template

- [ ] Testar migrações
  ```bash
  python manage.py migrate
  python manage.py migrate --database=suporte
  ```

### Frontend - Testes

- [ ] Testar build
  ```bash
  npm run build
  ```

- [ ] Testar desenvolvimento
  ```bash
  npm run dev
  ```

- [ ] Testar login em todos os tipos
  - [ ] Superadmin
  - [ ] Loja
  - [ ] Suporte

- [ ] Testar dashboards
  - [ ] Carregamento de dados
  - [ ] Responsividade
  - [ ] Navegação

- [ ] Testar em diferentes navegadores
  - [ ] Chrome
  - [ ] Firefox
  - [ ] Safari
  - [ ] Edge

---

## FASE 10: DOCUMENTAÇÃO (Dia 13)

### Backend - Documentar

- [ ] Atualizar `backend/README.md`
  - [ ] Explicar estrutura de modelos base
  - [ ] Explicar como criar novo app
  - [ ] Explicar como usar ViewSet genérico

- [ ] Criar `backend/core/README.md`
  - [ ] Documentar modelos base
  - [ ] Documentar ViewSets genéricos
  - [ ] Documentar serializers base

- [ ] Atualizar `backend/ARCHITECTURE.md`
  - [ ] Explicar nova estrutura
  - [ ] Mostrar diagrama de herança

### Frontend - Documentar

- [ ] Atualizar `frontend/README.md`
  - [ ] Explicar estrutura de componentes
  - [ ] Explicar como criar novo componente
  - [ ] Explicar como usar hooks

- [ ] Criar `frontend/COMPONENTS.md`
  - [ ] Documentar componentes reutilizáveis
  - [ ] Mostrar exemplos de uso

- [ ] Criar `frontend/HOOKS.md`
  - [ ] Documentar hooks customizados
  - [ ] Mostrar exemplos de uso

---

## FASE 11: DEPLOY (Dia 14)

### Backend - Deploy

- [ ] Fazer merge de `refactor/consolidate-models` para `main`
- [ ] Executar testes em CI/CD
- [ ] Deploy para staging
- [ ] Testar em staging
- [ ] Deploy para produção

### Frontend - Deploy

- [ ] Fazer merge de `refactor/consolidate-components` para `main`
- [ ] Executar testes em CI/CD
- [ ] Deploy para staging (Vercel)
- [ ] Testar em staging
- [ ] Deploy para produção (Vercel)

---

## FASE 12: MONITORAMENTO (Dia 15+)

- [ ] Monitorar logs de erro
- [ ] Monitorar performance
- [ ] Coletar feedback do time
- [ ] Documentar lições aprendidas
- [ ] Planejar próximas melhorias

---

## 📊 MÉTRICAS DE SUCESSO

### Antes
- Linhas de código duplicado: ~2.000
- Modelos duplicados: 15+
- ViewSets duplicados: 8+
- Arquivos de configuração: 4
- Arquivos mortos: 20+

### Depois (Meta)
- Linhas de código duplicado: <200
- Modelos duplicados: 0
- ViewSets duplicados: 0
- Arquivos de configuração: 2
- Arquivos mortos: 0

### Verificar
- [ ] Redução de código duplicado: 90%
- [ ] Redução de tamanho do repositório: 15%
- [ ] Redução de tempo de manutenção: 40%
- [ ] Redução de bugs: 80%

---

## 🚨 ROLLBACK PLAN

Se algo der errado:

1. **Revert Branch**
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **Restore Database**
   ```bash
   python manage.py migrate <app> <migration-number>
   ```

3. **Notify Team**
   - Comunicar problema
   - Explicar causa
   - Planejar próxima tentativa

---

## 📝 NOTAS

- Fazer commits pequenos e frequentes
- Testar após cada mudança
- Documentar decisões
- Comunicar progresso ao time
- Pedir review antes de merge

---

**Tempo Total Estimado:** 15 dias
**Equipe Recomendada:** 2-3 desenvolvedores
**Risco:** Baixo (mudanças incrementais)
**Benefício:** Alto (reduz 40% do tempo de manutenção)
