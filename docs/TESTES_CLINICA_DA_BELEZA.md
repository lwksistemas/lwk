# Testes pós-deploy – Clínica da Beleza

Checklist para validar o sistema usando uma loja do tipo **Clínica da Beleza**, após deploy (Vercel + Heroku).

---

## URLs de produção

| Ambiente | URL |
|----------|-----|
| **Frontend** | https://lwksistemas.com.br |
| **Backend API** | https://lwksistemas-38ad47519238.herokuapp.com |

---

## Pré-requisito: loja tipo Clínica da Beleza

- Ter uma loja cadastrada no Super Admin com **tipo = "Clínica da Beleza"** (ou nome que contenha "clínica" e "beleza").
- Exemplo de slug: `minha-clinica-beleza` → login: `https://lwksistemas.com.br/loja/minha-clinica-beleza/login`

Se não existir, crie no Super Admin (Lojas → Nova Loja) e escolha o tipo **Clínica da Beleza**.

---

## Checklist de testes (Clínica da Beleza)

Use uma conta **proprietária** dessa loja (owner). Marque cada item após testar.

### 1. Login e dashboard

- [ ] Acessar `https://lwksistemas.com.br/loja/{SLUG}/login` (substituir `{SLUG}` pelo slug da loja).
- [ ] Fazer login com usuário/senha do proprietário.
- [ ] Redirecionamento para o dashboard da Clínica da Beleza (layout específico, sidebar com ícones).
- [ ] Exibição de estatísticas (agendamentos hoje, receita, etc.) sem erro.
- [ ] Logo da loja (se houver) carregando corretamente (next/image).

### 2. Agenda

- [ ] Menu/atalho para **Agenda** → abrir `/loja/{slug}/agenda`.
- [ ] Calendário carregando (FullCalendar).
- [ ] Seleção de profissional (se houver) e carregamento de agendamentos.
- [ ] Criar novo agendamento (paciente, procedimento, data/hora) e salvar.
- [ ] Bloqueio de horário (se disponível): criar e ver bloqueio no calendário.
- [ ] Indicador offline (canto da tela) visível; comportamento opcional com rede desligada.

### 3. Pacientes

- [ ] Menu **Pacientes** → `/loja/{slug}/clinica-beleza/pacientes`.
- [ ] Listagem de pacientes carregando.
- [ ] Cadastrar novo paciente e editar um existente.

### 4. Profissionais

- [ ] Menu **Profissionais** → `/loja/{slug}/clinica-beleza/profissionais`.
- [ ] Listagem de profissionais.
- [ ] Abrir horários de trabalho (se houver modal) e salvar.

### 5. Procedimentos

- [ ] Menu **Procedimentos** → `/loja/{slug}/clinica-beleza/procedimentos`.
- [ ] Listagem de procedimentos.
- [ ] Valores exibidos em R$ (formatCurrency).
- [ ] Criar/editar procedimento com preço.

### 6. Financeiro

- [ ] Menu **Financeiro** → `/loja/{slug}/clinica-beleza/financeiro`.
- [ ] Resumo (caixa diário, total mês, etc.) em R$ (formatCurrency).
- [ ] Lista de pagamentos/comissões carregando.
- [ ] Valores e datas formatados corretamente.

### 7. Campanhas

- [ ] Menu **Campanhas** → `/loja/{slug}/clinica-beleza/campanhas`.
- [ ] Página carregando sem erro (lista ou empty state).

### 8. Segurança e compatibilidade

- [ ] Em outra aba, tentar acessar outra loja (slug diferente) com o mesmo usuário: deve dar 403 ou redirecionar (isolamento entre lojas).
- [ ] Fazer logout e tentar acessar de novo uma URL interna da loja: deve ir para a tela de login.
- [ ] Após login, nenhum erro 401 nas chamadas de API (ver Network no DevTools).

### 9. Mobile / responsivo

- [ ] Redimensionar janela ou testar em celular: dashboard e agenda usáveis.
- [ ] Botões e links clicáveis; formulários preenchíveis.

---

## Onde reportar falhas

- **Frontend (Vercel):** build e runtime – ver [Vercel Dashboard](https://vercel.com) do projeto.
- **Backend (Heroku):** `heroku logs --tail -a lwksistemas` para erros da API.
- Anotar: URL, ação feita, mensagem de erro (tela ou console/Network).

---

## Deploy usado neste checklist

- **Commit:** Deploy: correções Vercel/Heroku + compatibilidade frontend-backend  
- **Backend:** Heroku v670  
- **Frontend:** Vercel (produção em lwksistemas.com.br)

Referências: `docs/DEPLOY_VERCEL_HEROKU_CLI.md`, `docs/SEGURANCA_ENTRE_LOJAS.md`.
