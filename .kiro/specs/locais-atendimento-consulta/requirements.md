# Requirements Document

## Introduction

Esta funcionalidade adiciona o conceito de "Local de Atendimento" ao módulo de consultas da Clínica da Beleza. Cada local possui um nome e um valor de consulta associado. Ao criar uma nova consulta, o profissional seleciona o local de atendimento e o valor da consulta é preenchido automaticamente com base no preço configurado para aquele local. O gerenciamento dos locais (CRUD) é acessível via botão de configuração na página de consultas.

## Glossary

- **Sistema**: O módulo Clínica da Beleza do LWK Sistemas
- **Local_de_Atendimento**: Entidade que representa um lugar onde consultas são realizadas (ex: Consultório, Home Care, Hospital, Telemedicina), contendo nome e valor de consulta associado
- **Página_de_Consultas**: Página frontend localizada em `/clinica-beleza/consultas` que lista e gerencia consultas
- **NovaConsultaModal**: Modal de criação de nova consulta avulsa
- **Profissional**: Usuário com papel de profissional de saúde que realiza consultas
- **CRUD_Locais**: Interface de gerenciamento (criar, listar, editar, excluir) dos locais de atendimento
- **Valor_Consulta**: Campo monetário (decimal, 2 casas) que armazena o preço da consulta

## Requirements

### Requirement 1: Modelo de Local de Atendimento

**User Story:** Como administrador da clínica, eu quero cadastrar locais de atendimento com nome e valor, para que o preço da consulta seja padronizado por local.

#### Acceptance Criteria

1. THE Sistema SHALL armazenar cada Local_de_Atendimento com os campos: nome (texto, máximo 200 caracteres) e valor_consulta (decimal, 10 dígitos, 2 casas decimais)
2. THE Sistema SHALL isolar os dados de Local_de_Atendimento por loja utilizando LojaIsolationMixin
3. THE Sistema SHALL garantir que o campo nome do Local_de_Atendimento seja obrigatório e não vazio
4. THE Sistema SHALL garantir que o campo valor_consulta do Local_de_Atendimento seja obrigatório e maior ou igual a zero
5. THE Sistema SHALL manter campos de auditoria created_at e updated_at em cada Local_de_Atendimento
6. THE Sistema SHALL permitir desativar um Local_de_Atendimento sem excluí-lo permanentemente através de um campo is_active

### Requirement 2: API CRUD de Locais de Atendimento

**User Story:** Como administrador da clínica, eu quero criar, listar, editar e excluir locais de atendimento via API, para gerenciar os locais disponíveis.

#### Acceptance Criteria

1. WHEN uma requisição GET é enviada ao endpoint de locais, THE Sistema SHALL retornar a lista de locais de atendimento ativos da loja corrente
2. WHEN uma requisição POST com nome e valor_consulta válidos é enviada, THE Sistema SHALL criar um novo Local_de_Atendimento e retornar os dados criados com status 201
3. WHEN uma requisição PUT com dados válidos é enviada para um local existente, THE Sistema SHALL atualizar o Local_de_Atendimento e retornar os dados atualizados
4. WHEN uma requisição DELETE é enviada para um local existente, THE Sistema SHALL desativar o Local_de_Atendimento (soft delete via is_active=False)
5. IF uma requisição POST ou PUT com nome vazio é enviada, THEN THE Sistema SHALL retornar erro de validação com status 400
6. IF uma requisição POST ou PUT com valor_consulta negativo é enviada, THEN THE Sistema SHALL retornar erro de validação com status 400
7. IF uma requisição é enviada para um Local_de_Atendimento inexistente ou de outra loja, THEN THE Sistema SHALL retornar status 404

### Requirement 3: Botão de Configuração na Página de Consultas

**User Story:** Como administrador da clínica, eu quero acessar o gerenciamento de locais de atendimento a partir da página de consultas, para configurar os locais de forma rápida e contextual.

#### Acceptance Criteria

1. THE Página_de_Consultas SHALL exibir um botão de configuração (ícone engrenagem) posicionado ao lado do botão "Nova consulta" no cabeçalho
2. WHEN o botão de configuração é clicado, THE Sistema SHALL abrir o CRUD_Locais em modal com a lista de locais cadastrados
3. THE CRUD_Locais SHALL exibir cada local com seu nome e valor formatado em reais (R$ X,XX)
4. THE CRUD_Locais SHALL permitir adicionar um novo local através de formulário com campos nome e valor
5. THE CRUD_Locais SHALL permitir editar o nome e o valor de um local existente
6. THE CRUD_Locais SHALL permitir excluir um local com confirmação prévia do usuário
7. WHEN um local é adicionado, editado ou excluído com sucesso, THE CRUD_Locais SHALL atualizar a lista exibida sem recarregar a página

### Requirement 4: Seleção de Local ao Criar Consulta

**User Story:** Como profissional, eu quero selecionar o local de atendimento ao criar uma nova consulta, para que o valor da consulta seja preenchido automaticamente.

#### Acceptance Criteria

1. THE NovaConsultaModal SHALL exibir um campo de seleção (dropdown) com os locais de atendimento ativos da loja
2. WHEN o Profissional seleciona um Local_de_Atendimento no dropdown, THE NovaConsultaModal SHALL preencher automaticamente o valor da consulta com o valor_consulta configurado no local selecionado
3. WHEN o valor é preenchido automaticamente, THE NovaConsultaModal SHALL permitir que o Profissional altere manualmente o valor antes de confirmar
4. THE NovaConsultaModal SHALL enviar o local_atendimento selecionado e o valor_consulta ao criar a consulta
5. THE Sistema SHALL armazenar a referência ao Local_de_Atendimento na Consulta criada
6. IF nenhum Local_de_Atendimento estiver cadastrado, THEN THE NovaConsultaModal SHALL ocultar o campo de seleção de local e manter o comportamento atual (valor calculado pelos procedimentos)

### Requirement 5: Persistência do Local na Consulta

**User Story:** Como administrador da clínica, eu quero que o local de atendimento fique registrado na consulta, para consultar onde cada atendimento foi realizado.

#### Acceptance Criteria

1. THE Sistema SHALL armazenar uma referência opcional (ForeignKey nullable) ao Local_de_Atendimento no modelo Consulta
2. WHEN uma consulta é criada com local_atendimento informado, THE Sistema SHALL registrar o valor_consulta do local selecionado no campo valor_consulta da Consulta
3. WHEN o valor_consulta é alterado manualmente pelo Profissional no momento da criação, THE Sistema SHALL armazenar o valor informado pelo Profissional ao invés do valor padrão do local
4. THE Página_de_Consultas SHALL exibir o nome do Local_de_Atendimento nos detalhes da consulta quando disponível
