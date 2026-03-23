# Alterações: Seleção de Grupo no Cadastro de Funcionários

**Data**: 23/03/2026  
**Deploy**: Heroku v1290 (Backend) | Vercel (Frontend - automático)  
**Loja de Teste**: 41449198000172 (FELIX REPRESENTACOES E COMERCIO LTDA)

---

## Problema Resolvido

Ao cadastrar funcionários no CRM, não havia opção para selecionar o grupo/perfil (Gerente de Vendas, Vendedor, etc). O usuário precisava atribuir manualmente os grupos após criar o funcionário.

---

## Solução Implementada

### Backend (Django)

1. **Endpoint para Listar Grupos Disponíveis**
   - Adicionado action `grupos_disponiveis` no `VendedorViewSet`
   - Retorna grupos relacionados ao CRM: "Gerente de Vendas" e "Vendedor"
   - Endpoint: `GET /crm-vendas/vendedores/grupos_disponiveis/`
   - Requer permissão de administrador

2. **Modificações no VendedorSerializer**
   - Adicionado campo `grupo_id` (write-only) para receber o ID do grupo
   - Adicionado campo `grupo_nome` (read-only) para exibir o nome do grupo atual
   - Método `get_grupo_nome()` busca o grupo do vendedor via VendedorUsuario

3. **Atribuição de Grupo ao Criar/Editar Vendedor**
   - Método `_criar_acesso_e_enviar_email()` modificado para aceitar `grupo_id`
   - Novo método `_atualizar_grupo()` para atualizar grupo de vendedor existente
   - Novo método `_atualizar_grupo_usuario()` que:
     - Remove grupos CRM anteriores (Gerente de Vendas, Vendedor)
     - Adiciona o novo grupo selecionado
   - Grupo é atribuído automaticamente ao criar acesso ou pode ser atualizado posteriormente

### Frontend (Next.js/React)

1. **Carregamento de Grupos**
   - Estado `grupos` adicionado ao componente
   - Carrega grupos disponíveis na montagem do componente
   - Usa `Promise.all` para carregar vendedores e grupos simultaneamente

2. **Campo de Seleção no Formulário**
   - Adicionado campo select "Perfil/Grupo" entre "Cargo" e "Comissão"
   - Opções carregadas dinamicamente do backend
   - Campo opcional (pode criar vendedor sem grupo)
   - Texto de ajuda: "Define as permissões do funcionário no sistema. Gerente de Vendas tem acesso completo."

3. **Exibição do Grupo na Lista**
   - Badge roxo exibindo o grupo do vendedor (se houver)
   - Aparece ao lado do badge "Administrador"
   - Cores: `bg-purple-100 text-purple-700` (light) / `bg-purple-900/30 text-purple-400` (dark)

4. **Envio do Grupo ao Salvar**
   - Campo `grupo_id` incluído no payload apenas se foi selecionado
   - Conversão para inteiro antes do envio
   - Funciona tanto para criar quanto para editar vendedor

---

## Arquivos Modificados

### Backend
- `backend/crm_vendas/views.py`
  - Import de `Group` do Django
  - Action `grupos_disponiveis` no VendedorViewSet

- `backend/crm_vendas/serializers.py`
  - Campos `grupo_id` e `grupo_nome` no VendedorSerializer
  - Método `get_grupo_nome()`
  - Métodos `create()` e `update()` modificados
  - Método `_criar_acesso_e_enviar_email()` modificado
  - Novos métodos `_atualizar_grupo()` e `_atualizar_grupo_usuario()`

### Frontend
- `frontend/app/(dashboard)/loja/[slug]/crm-vendas/configuracoes/funcionarios/page.tsx`
  - Interface `Vendedor` atualizada (`grupo_nome`)
  - Estado `grupos` adicionado
  - Função `carregar()` modificada para buscar grupos
  - Funções `abrirNovo()` e `abrirEditar()` com campo `grupo_id`
  - Função `handleSubmit()` envia `grupo_id` se selecionado
  - Campo select adicionado no formulário
  - Badge de grupo adicionado na lista

---

## Como Usar

1. **Acessar Configurações de Funcionários**
   - Menu: CRM Vendas > Configurações > Cadastrar funcionários
   - URL: `/loja/{slug}/crm-vendas/configuracoes/funcionarios`

2. **Criar Novo Vendedor com Grupo**
   - Clicar em "Novo vendedor"
   - Preencher dados (Nome, Email, Telefone, Cargo)
   - Selecionar "Perfil/Grupo" (Gerente de Vendas ou Vendedor)
   - Definir comissão padrão
   - Marcar "Criar acesso ao sistema" se desejar
   - Salvar

3. **Editar Vendedor Existente**
   - Clicar em "Editar" no vendedor desejado
   - Alterar dados conforme necessário
   - Selecionar novo grupo (se desejar alterar)
   - Marcar "Criar ou reenviar acesso" para aplicar o grupo
   - Salvar

4. **Visualizar Grupo do Vendedor**
   - Na lista de funcionários, o grupo aparece como badge roxo
   - Exemplo: "Gerente de Vendas" ou "Vendedor"

---

## Grupos Disponíveis

### Gerente de Vendas
- Acesso completo ao CRM
- Todas as permissões de vendas
- Pode gerenciar leads, contas, contatos, oportunidades, propostas, contratos
- Pode gerenciar produtos/serviços, atividades, templates
- Pode visualizar e editar funcionários (exceto excluir administrador)
- NÃO é tratado como vendedor comum (não aparece filtrado como vendedor)

### Vendedor
- Acesso básico ao CRM
- Permissões limitadas de vendas
- Pode gerenciar suas próprias oportunidades
- Acesso restrito a configurações

---

## Observações Importantes

1. **Administrador (Owner)**
   - NÃO deve ser vendedor, mas sim Gerente de Vendas
   - Owner nunca é marcado como `is_vendedor=true`
   - Mesmo com grupo Gerente de Vendas, mantém privilégios de owner

2. **Atribuição de Grupo**
   - Grupo só é atribuído quando "Criar acesso" está marcado
   - Para atualizar grupo de vendedor existente, marcar "Criar ou reenviar acesso"
   - Grupos CRM anteriores são removidos automaticamente ao atribuir novo grupo

3. **Permissões**
   - Apenas administradores podem acessar configurações de funcionários
   - Vendedores comuns não veem esta página

4. **Cache**
   - Lista de vendedores não usa cache (problema de cache recorrente)
   - Dados sempre atualizados após salvar

---

## Testes Realizados

✅ Listar grupos disponíveis via API  
✅ Criar vendedor com grupo selecionado  
✅ Criar vendedor sem grupo (opcional)  
✅ Editar vendedor e alterar grupo  
✅ Exibir grupo na lista de vendedores  
✅ Verificar permissões (apenas admin acessa)  
✅ Deploy backend (Heroku v1290)  
✅ Deploy frontend (Vercel automático)

---

## Próximos Passos

- Testar na loja 41449198000172 após deploy
- Verificar se grupos são atribuídos corretamente
- Confirmar que permissões funcionam conforme esperado
- Validar que Gerente de Vendas vê todas as oportunidades
- Confirmar que Vendedor vê apenas suas oportunidades

---

## Comandos Úteis

```bash
# Listar grupos disponíveis
heroku run "python backend/manage.py shell -c \"from django.contrib.auth.models import Group; print(list(Group.objects.values('id', 'name')))\""

# Verificar grupos de um usuário
heroku run "python backend/manage.py shell -c \"from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.get(email='email@exemplo.com'); print(list(u.groups.values('name')))\""

# Adicionar usuário a um grupo manualmente
heroku run "python backend/manage.py shell -c \"from django.contrib.auth import get_user_model; from django.contrib.auth.models import Group; User = get_user_model(); u = User.objects.get(email='email@exemplo.com'); g = Group.objects.get(name='Gerente de Vendas'); u.groups.add(g)\""
```
# Deploy v1.2 - Seleção de Grupo
