# Requirements Document

## Introduction

Refatoração do cadastro de vendedor no CRM Vendas para substituir o modal atual (max-w-2xl) por uma página dedicada full-screen com layout em 2 colunas. A coluna esquerda conterá dados pessoais do vendedor e a coluna direita conterá configurações de acesso ao sistema com um sistema de permissões granulares via checkboxes agrupados por perfil/grupo. O deploy inicial será feito no servidor beta para validação antes de ir à produção.

## Glossary

- **CRM_Vendas**: Módulo de CRM (Customer Relationship Management) para lojas do tipo vendas no sistema LWK
- **Vendedor**: Funcionário cadastrado no CRM Vendas que pode ser vendedor, gerente ou outro cargo da equipe comercial
- **Página_Cadastro_Vendedor**: Página dedicada full-screen para criação e edição de vendedores (substitui o modal atual)
- **Coluna_Dados_Pessoais**: Seção esquerda do layout de 2 colunas contendo nome, email, telefone, cargo e comissão
- **Coluna_Acesso_Permissoes**: Seção direita do layout de 2 colunas contendo configurações de acesso ao sistema e permissões granulares
- **Perfil_Grupo**: Grupo de permissões (ex: Gerente de Vendas, Vendedor) que define um conjunto pré-configurado de permissões para o usuário
- **Permissao_Granular**: Permissão individual representada por um checkbox que pode ser habilitada ou desabilitada independentemente do perfil base
- **VendedorUsuario**: Modelo no backend que vincula um User do Django auth a um Vendedor no schema tenant, permitindo login no sistema
- **Servidor_Beta**: Ambiente de staging/homologação onde a funcionalidade será testada antes do deploy em produção

## Requirements

### Requirement 1: Navegação para Página Dedicada de Cadastro

**User Story:** Como administrador do CRM Vendas, eu quero que ao clicar em "Novo vendedor" ou "Editar" seja aberta uma página dedicada full-screen, para que eu tenha mais espaço para preencher dados e configurar permissões.

#### Acceptance Criteria

1. WHEN o administrador clicar no botão "Novo vendedor" na listagem de funcionários, THE Página_Cadastro_Vendedor SHALL navegar para a rota `/loja/{slug}/crm-vendas/configuracoes/funcionarios/novo`
2. WHEN o administrador clicar no botão "Editar" de um vendedor existente, THE Página_Cadastro_Vendedor SHALL navegar para a rota `/loja/{slug}/crm-vendas/configuracoes/funcionarios/{id}/editar`
3. THE Página_Cadastro_Vendedor SHALL exibir um botão "Voltar" no topo que retorna à listagem de funcionários
4. THE Página_Cadastro_Vendedor SHALL ocupar toda a área de conteúdo disponível (full-screen dentro do layout do dashboard)

### Requirement 2: Layout em 2 Colunas

**User Story:** Como administrador do CRM Vendas, eu quero que o formulário de cadastro de vendedor seja organizado em 2 colunas, para que eu possa visualizar dados pessoais separados das configurações de acesso e permissões.

#### Acceptance Criteria

1. THE Página_Cadastro_Vendedor SHALL exibir o formulário em layout de 2 colunas em telas com largura igual ou superior a 1024px
2. WHILE a largura da tela for inferior a 1024px, THE Página_Cadastro_Vendedor SHALL empilhar as colunas verticalmente (Coluna_Dados_Pessoais acima da Coluna_Acesso_Permissoes)
3. THE Coluna_Dados_Pessoais SHALL conter os campos: nome (obrigatório), email, telefone, cargo e comissão padrão (%)
4. THE Coluna_Acesso_Permissoes SHALL conter: toggle de criar acesso ao sistema, seleção de perfil/grupo, e checkboxes de permissões granulares

### Requirement 3: Coluna de Dados Pessoais

**User Story:** Como administrador do CRM Vendas, eu quero preencher os dados pessoais do vendedor na coluna esquerda, para que as informações de contato e cargo fiquem organizadas.

#### Acceptance Criteria

1. THE Coluna_Dados_Pessoais SHALL exibir o campo "Nome" como obrigatório com formatação automática em maiúsculas
2. THE Coluna_Dados_Pessoais SHALL exibir o campo "Email" com validação de formato de e-mail
3. THE Coluna_Dados_Pessoais SHALL exibir o campo "Telefone" com máscara de formatação brasileira (XX) XXXXX-XXXX
4. THE Coluna_Dados_Pessoais SHALL exibir o campo "Cargo" com valor padrão "Vendedor"
5. THE Coluna_Dados_Pessoais SHALL exibir o campo "Comissão Padrão (%)" como numérico com intervalo de 0 a 100 e incremento de 0.01

### Requirement 4: Sistema de Acesso ao Sistema

**User Story:** Como administrador do CRM Vendas, eu quero configurar o acesso ao sistema para o vendedor na coluna direita, para que ele possa fazer login e utilizar o CRM com as permissões corretas.

#### Acceptance Criteria

1. THE Coluna_Acesso_Permissoes SHALL exibir um toggle/checkbox "Criar acesso ao sistema" que controla a visibilidade dos campos de acesso
2. WHEN o toggle "Criar acesso ao sistema" for ativado, THE Coluna_Acesso_Permissoes SHALL exibir os campos "Usuário para login" e "E-mail para envio de senha"
3. WHEN o toggle "Criar acesso ao sistema" for ativado, THE Coluna_Acesso_Permissoes SHALL pré-preencher o campo "Usuário para login" com o primeiro nome do vendedor em minúsculas sem acentos
4. THE Coluna_Acesso_Permissoes SHALL validar que o campo "Usuário para login" aceita apenas letras minúsculas, números, ponto e hífen
5. WHEN o toggle "Criar acesso ao sistema" for ativado sem e-mail preenchido na Coluna_Dados_Pessoais, THE Coluna_Acesso_Permissoes SHALL exibir o campo de e-mail como obrigatório na seção de acesso

### Requirement 5: Seleção de Perfil/Grupo de Permissões

**User Story:** Como administrador do CRM Vendas, eu quero selecionar um perfil/grupo para o vendedor, para que as permissões base sejam configuradas automaticamente de acordo com a função dele.

#### Acceptance Criteria

1. THE Coluna_Acesso_Permissoes SHALL exibir um seletor de Perfil_Grupo com as opções carregadas do endpoint `/crm-vendas/vendedores/grupos_disponiveis/`
2. WHEN um Perfil_Grupo for selecionado, THE Coluna_Acesso_Permissoes SHALL carregar e marcar automaticamente os checkboxes de permissões associados ao grupo selecionado
3. WHEN nenhum Perfil_Grupo for selecionado, THE Coluna_Acesso_Permissoes SHALL exibir todos os checkboxes de permissões desmarcados
4. THE Coluna_Acesso_Permissoes SHALL permitir a seleção de Perfil_Grupo independentemente do toggle de acesso ao sistema estar ativo

### Requirement 6: Permissões Granulares com Checkboxes

**User Story:** Como administrador do CRM Vendas, eu quero ajustar individualmente as permissões de cada vendedor através de checkboxes, para ter controle fino sobre o que cada membro da equipe pode fazer no sistema.

#### Acceptance Criteria

1. THE Coluna_Acesso_Permissoes SHALL exibir as permissões disponíveis como checkboxes agrupados por categoria (ex: Oportunidades, Contatos, Relatórios, Configurações)
2. WHEN um Perfil_Grupo for selecionado, THE Coluna_Acesso_Permissoes SHALL permitir que o administrador marque ou desmarque permissões individuais para personalizar o perfil
3. THE Coluna_Acesso_Permissoes SHALL carregar a lista de permissões disponíveis a partir de um endpoint do backend
4. WHEN o formulário for aberto para edição de um vendedor com acesso existente, THE Coluna_Acesso_Permissoes SHALL carregar e exibir as permissões atuais do vendedor

### Requirement 7: Salvamento do Formulário

**User Story:** Como administrador do CRM Vendas, eu quero salvar os dados do vendedor com suas permissões em uma única ação, para que o processo seja eficiente.

#### Acceptance Criteria

1. THE Página_Cadastro_Vendedor SHALL exibir um botão "Salvar" fixo na parte superior da página
2. WHEN o botão "Salvar" for clicado com dados válidos, THE Página_Cadastro_Vendedor SHALL enviar os dados pessoais, configuração de acesso e permissões em uma única requisição ao backend
3. WHEN o salvamento for concluído com sucesso, THE Página_Cadastro_Vendedor SHALL redirecionar para a listagem de funcionários com mensagem de confirmação
4. IF o salvamento falhar por erro de validação, THEN THE Página_Cadastro_Vendedor SHALL exibir as mensagens de erro nos campos correspondentes sem perder os dados preenchidos
5. IF o salvamento falhar por erro de rede ou servidor, THEN THE Página_Cadastro_Vendedor SHALL exibir uma mensagem de erro genérica no topo da página

### Requirement 8: Backend - Endpoint de Permissões Disponíveis

**User Story:** Como frontend do CRM Vendas, eu quero consultar as permissões disponíveis organizadas por categoria, para exibir os checkboxes corretos na interface.

#### Acceptance Criteria

1. THE CRM_Vendas SHALL expor um endpoint GET `/crm-vendas/vendedores/permissoes_disponiveis/` que retorna a lista de permissões disponíveis agrupadas por categoria
2. WHEN o endpoint for consultado, THE CRM_Vendas SHALL retornar as permissões no formato `{categoria: string, permissoes: [{id: number, codename: string, nome: string}]}`
3. THE CRM_Vendas SHALL filtrar as permissões retornadas para incluir apenas as relevantes ao módulo CRM Vendas

### Requirement 9: Backend - Persistência de Permissões Granulares

**User Story:** Como sistema CRM Vendas, eu quero persistir as permissões individuais do vendedor, para que o controle de acesso granular funcione corretamente.

#### Acceptance Criteria

1. WHEN um vendedor for criado ou atualizado com permissões granulares, THE CRM_Vendas SHALL atribuir as permissões selecionadas ao User vinculado via VendedorUsuario
2. WHEN um vendedor for atualizado com um novo Perfil_Grupo e permissões customizadas, THE CRM_Vendas SHALL aplicar primeiro as permissões do grupo e depois sobrescrever com as permissões individuais selecionadas
3. IF o vendedor não possuir acesso ao sistema (sem VendedorUsuario), THEN THE CRM_Vendas SHALL armazenar o Perfil_Grupo e as permissões selecionadas para aplicação quando o acesso for criado

### Requirement 10: Deploy no Servidor Beta

**User Story:** Como equipe de desenvolvimento, eu quero que a funcionalidade seja disponibilizada primeiro no servidor beta, para que seja validada antes de ir para produção.

#### Acceptance Criteria

1. THE Página_Cadastro_Vendedor SHALL ser deployada e testada no Servidor_Beta antes de ser liberada em produção
2. WHILE a funcionalidade estiver em validação no Servidor_Beta, THE CRM_Vendas SHALL manter o fluxo atual (modal) em produção sem alterações
