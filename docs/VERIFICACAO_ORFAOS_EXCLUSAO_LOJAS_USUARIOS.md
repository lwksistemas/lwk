# Verificação: exclusão de lojas e usuários sem cadastros órfãos

Este documento descreve como o sistema garante que **não restem vínculos ou cadastros órfãos** ao excluir lojas e usuários.

---

## 1. Exclusão de loja (superadmin/views.py `destroy`)

Quando uma loja é excluída pelo Super Admin, a ordem é:

### 1.1 Antes de `loja.delete()`

| O que é removido | Onde | Observação |
|------------------|------|------------|
| Chamados de suporte | `Chamado.objects.filter(loja_slug=loja_slug).delete()` | Tabela suporte no default DB |
| Arquivo SQLite (se existir) | `db_{database_name}.sqlite3` | Apenas ambiente com SQLite por loja |
| Config do banco em `settings.DATABASES` | `del settings.DATABASES[database_name]` | Evita uso do alias após exclusão |
| Dados Asaas (API + local) | `AsaasDeletionService`, depois `LojaAssinatura`, `AsaasPayment`, `AsaasCustomer` | Pagamentos, assinatura e cliente no default DB |

### 1.2 Signal `pre_delete` (superadmin/signals.py `delete_all_loja_data`)

Antes do `loja.delete()` ser confirmado, o signal remove por **tipo de loja** no **banco default** (por `loja_id`):

- **Clínica de Estética:** Funcionario, Cliente, Agendamento, Profissional, Procedimento (tabelas `clinica_*`)
- **CRM Vendas:** Vendedor, Cliente, Lead, Venda, Pipeline, Produto (`crm_*`)
- **Restaurante:** Reserva, Pedido, ItemCardapio, Categoria, Mesa, Cliente, Funcionario, Fornecedor, NotaFiscalEntrada, MovimentoEstoque, RegistroPesoBalança, EstoqueItem (`restaurante_*`)
- **Serviços:** Agendamento, OrdemServico, Orcamento, Servico, Profissional, Cliente, Categoria, Funcionario (`servicos_*`)
- **Cabeleireiro:** BloqueioAgenda, Agendamento, Venda, Funcionario, HorarioFuncionamento, Produto, Servico, Profissional, Cliente (`cabeleireiro_*`)

Em seguida o signal:

- Remove **sessões do owner:** `UserSession.objects.filter(user_id=owner_id).delete()`
- **PostgreSQL:** executa `DROP SCHEMA IF EXISTS "{schema_name}" CASCADE` (schema = `database_name` da loja). Isso remove **todas** as tabelas do schema (Clínica da Beleza: Patient, Professional, Procedure, Appointment, BloqueioHorario, HorarioTrabalhoProfissional, Payment, CampanhaPromocao, etc.).

**Clínica da Beleza:** os dados ficam apenas nos schemas por loja. Não há tabelas no default com `loja_id` para clinica_beleza. A limpeza é feita pelo **DROP SCHEMA ... CASCADE**.

### 1.3 Ao chamar `loja.delete()`

O Django remove a loja e, por **CASCADE**:

- `FinanceiroLoja` (OneToOne)
- `PagamentoLoja` (FK para Loja e para FinanceiroLoja)
- `ProfissionalUsuario` (FK loja)

Nenhum desses fica órfão.

### 1.4 Depois da loja

- Se o **owner** não for de nenhuma outra loja e não for superuser: `User` é excluído (groups/permissions limpos antes). Ao excluir o User, CASCADE remove `ProfissionalUsuario`, `PushSubscription`, `UserSession` e, se ainda houver, `Loja` (owner).

---

## 2. Exclusão de usuário (UsuarioSistema)

Em **superadmin/views.py** (ViewSet de usuários do sistema), ao excluir um **UsuarioSistema**:

1. Remove `UsuarioSistema`.
2. Remove o `User` do Django.

**Proteção:** não é permitido excluir usuário que seja **owner de alguma loja**. Nesse caso a API retorna erro e a exclusão é barrada (evita remoção em cascata acidental de lojas ao apagar usuário de sistema). Ver seção 4.

Ao excluir o `User`, o Django remove por CASCADE:

- `ProfissionalUsuario` (vínculos user–loja–professional)
- `PushSubscription`
- `UserSession`
- `Loja` (se o user for owner) — mas isso é bloqueado antes pela regra acima

`HistoricoAcessoGlobal` usa `on_delete=SET_NULL` no `user` e no `loja`: o histórico permanece com referência nula (e `usuario_email` / `usuario_nome` como backup). Não gera órfão que quebre FK.

---

## 3. Comando de verificação de órfãos

Para conferir se restaram registros com `loja_id` de loja inexistente no **banco default**:

```bash
python manage.py verificar_dados_orfaos           # só lista
python manage.py verificar_dados_orfaos --remover # lista e remove órfãos
python manage.py verificar_dados_orfaos --dry-run # simula remoção
```

O comando considera apenas tabelas no **default** que tenham `loja_id` (superadmin, clinica_estetica, crm, restaurante, servicos, cabeleireiro). Dados da **Clínica da Beleza** ficam em schemas; ao excluir a loja, o schema é dropado, então não há órfãos de loja no default para esse tipo.

---

## 4. Ajuste de segurança: não excluir usuário owner de loja

Foi adicionada validação na exclusão de **UsuarioSistema**: se o usuário for **owner** de alguma loja, a exclusão é recusada com mensagem clara. Assim:

- Evita exclusão acidental do dono da loja pelo painel de usuários do sistema.
- A exclusão da loja continua sendo o fluxo correto (pela exclusão da loja, com limpeza e opção de remover o owner se não tiver outras lojas).

---

## 5. Resumo

| Ação | Órfãos evitados? | Como |
|------|------------------|------|
| Excluir loja | Sim | Chamados e Asaas na mão; signal limpa por tipo (default DB) + DROP SCHEMA (Postgres); CASCADE em FinanceiroLoja, PagamentoLoja, ProfissionalUsuario; owner removido só se não tiver outras lojas |
| Excluir usuário (UsuarioSistema) | Sim | Bloqueio se for owner de loja; CASCADE em ProfissionalUsuario, PushSubscription, UserSession |
| HistoricoAcessoGlobal | Mantido de propósito | SET_NULL em user/loja; histórico de auditoria preservado |

**Conclusão:** o sistema está preparado para que, ao excluir lojas e usuários (no fluxo descrito), **não fiquem cadastros ou vínculos órfãos** no banco. O comando `verificar_dados_orfaos` serve para auditoria e correção pontual no default DB.
