# Requirements Document

## Introduction

Esta feature abrange duas melhorias na experiência do administrador no sistema Clínica da Beleza:

1. **Menu lateral oculto por padrão** — Ao acessar o dashboard (`/loja/{slug}/dashboard`), o menu lateral (sidebar) deve iniciar recolhido, maximizando a área útil da tela. O usuário pode expandir manualmente quando necessário.

2. **Administrador como Profissional** — Na página de profissionais (`/clinica-beleza/profissionais`), permitir que o administrador da loja se habilite como profissional, criando um registro `Professional` vinculado ao seu usuário. Atualmente o admin não aparece na lista de profissionais.

## Glossary

- **Sistema**: O sistema LWK Sistemas (frontend Next.js + backend Django)
- **Menu_Lateral**: Componente sidebar (`ClinicaBelezaShell`) que exibe a navegação principal da clínica
- **Dashboard**: Página inicial da loja em `/loja/{slug}/dashboard`
- **Administrador**: Usuário proprietário/admin da loja (owner)
- **Profissional**: Registro do model `Professional` (herda de `ProfissionalBase`) no app `clinica_beleza`
- **Página_Profissionais**: Tela em `/loja/{slug}/clinica-beleza/profissionais` que lista os profissionais cadastrados
- **Toggle_Menu**: Botão que alterna o estado do Menu_Lateral entre recolhido e expandido
- **Toggle_Admin_Profissional**: Controle (botão/switch) que habilita ou desabilita o Administrador como Profissional

## Requirements

### Requirement 1: Menu lateral inicia recolhido

**User Story:** Como administrador da loja, eu quero que o menu lateral inicie recolhido ao acessar o dashboard, para que eu tenha mais espaço útil de tela ao entrar no sistema.

#### Acceptance Criteria

1. WHEN o Sistema carrega a página do Dashboard, THE Menu_Lateral SHALL iniciar no estado recolhido (collapsed)
2. WHEN o usuário clica no Toggle_Menu com o Menu_Lateral recolhido, THE Menu_Lateral SHALL expandir exibindo os rótulos de todos os itens de navegação
3. WHEN o usuário clica no Toggle_Menu com o Menu_Lateral expandido, THE Menu_Lateral SHALL recolher exibindo apenas os ícones dos itens de navegação
4. WHEN o usuário navega entre páginas dentro da loja após expandir o Menu_Lateral manualmente, THE Menu_Lateral SHALL manter o estado expandido escolhido pelo usuário durante a sessão
5. WHEN o usuário acessa o Dashboard em dispositivo móvel, THE Menu_Lateral SHALL permanecer completamente oculto até ser aberto pelo botão de menu mobile

### Requirement 2: Habilitar administrador como profissional

**User Story:** Como administrador da loja, eu quero me habilitar como profissional na página de profissionais, para que eu possa atender clientes e aparecer na agenda como os demais profissionais.

#### Acceptance Criteria

1. WHEN o Administrador acessa a Página_Profissionais, THE Sistema SHALL exibir o Toggle_Admin_Profissional com o estado atual (habilitado ou desabilitado)
2. WHEN o Administrador ativa o Toggle_Admin_Profissional e não existe um registro Profissional vinculado ao Administrador, THE Sistema SHALL criar um registro Professional com o nome e email do Administrador, vinculado à loja atual
3. WHEN o Administrador ativa o Toggle_Admin_Profissional com sucesso, THE Sistema SHALL exibir o Administrador na lista de profissionais da Página_Profissionais
4. WHEN o Administrador desativa o Toggle_Admin_Profissional, THE Sistema SHALL desativar o registro Professional do Administrador (marcando is_active como false) sem removê-lo do banco de dados
5. WHILE o registro Professional do Administrador está com is_active igual a false, THE Sistema SHALL ocultar o Administrador da lista de profissionais visíveis na Página_Profissionais
6. WHILE o registro Professional do Administrador está com is_active igual a true, THE Sistema SHALL incluir o Administrador como opção disponível na agenda de atendimentos
7. IF a criação do registro Professional falhar por erro de rede ou servidor, THEN THE Sistema SHALL exibir uma mensagem de erro descritiva e reverter o Toggle_Admin_Profissional ao estado anterior
8. THE Toggle_Admin_Profissional SHALL ser visível apenas para usuários com permissão de administrador da loja

### Requirement 3: Persistência do vínculo admin-profissional

**User Story:** Como administrador da loja, eu quero que meu registro de profissional persista entre sessões, para que eu não precise me habilitar novamente cada vez que acesso o sistema.

#### Acceptance Criteria

1. WHEN o Administrador faz login novamente após ter se habilitado como Profissional, THE Sistema SHALL exibir o Toggle_Admin_Profissional como ativado refletindo o estado persistido
2. WHEN o registro Professional do Administrador já existe e está ativo, THE Sistema SHALL permitir que o Administrador edite seus dados profissionais (especialidade, registro profissional, telefone) como qualquer outro Profissional
3. THE Sistema SHALL vincular o registro Professional do Administrador à mesma loja (schema) do Administrador respeitando o isolamento multi-tenant
