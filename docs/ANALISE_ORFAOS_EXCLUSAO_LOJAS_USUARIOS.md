# Análise: Órfãos na exclusão de lojas e usuários

## Objetivo

Garantir que, ao excluir **lojas** ou **usuários**, não permaneçam no sistema cadastros ou vínculos órfãos (registros que referenciam loja ou usuário inexistentes).

---

## 1. Fluxo de exclusão de LOJA

### 1.1 Onde ocorre

- **superadmin/views.py**: `LojaViewSet.destroy()` (DELETE da API de lojas).

### 1.2 Ordem das operações

1. **Chamados de suporte**  
   Remove todos os `Chamado` com `loja_slug` da loja.

2. **Banco SQLite (dev)**  
   Se `database_created` e existir arquivo `db_<database_name>.sqlite3`, remove o arquivo e a entrada em `settings.DATABASES`.

3. **Asaas (API + dados locais)**  
   - Chama `AsaasDeletionService.delete_loja_from_asaas(loja_slug)`.  
   - Remove localmente: `AsaasPayment`, `LojaAssinatura`, `AsaasCustomer` (por `loja_slug`).

4. **Exclusão da loja**  
   `loja.delete()` dispara o signal `pre_delete` e, em seguida, o Django aplica CASCADE nos FKs.

5. **Signal `pre_delete` (superadmin/signals.py – `delete_all_loja_data`)**  
   - Remove dados no banco **default** por `loja_id`, conforme o **tipo da loja**:
     - **Clínica de Estética**: Funcionario, Cliente, Agendamento, Profissional, Procedimento  
     - **CRM Vendas**: Vendedor, Cliente, Lead, Venda, Pipeline, Produto  
     - **Restaurante**: Reserva, Pedido, ItemCardapio, Categoria, Mesa, Cliente, Funcionario, Fornecedor, NotaFiscalEntrada, MovimentoEstoque, RegistroPesoBalança, EstoqueItem  
     - **Serviços**: Agendamento, OrdemServico, Orcamento, Servico, Profissional, Cliente, Categoria, Funcionario  
     - **Cabeleireiro**: BloqueioAgenda, Agendamento, Venda, Funcionario, HorarioFuncionamento, Produto, Servico, Profissional, Cliente  
   - **Clínica da Beleza**: os dados ficam no **schema PostgreSQL** da loja; não há tabelas no default com `loja_id` para esse tipo.  
   - Remove **UserSession** do `owner` da loja.  
   - Em **PostgreSQL**, executa `DROP SCHEMA "<schema_name>" CASCADE`, removendo todo o conteúdo do schema (tabelas de clinica_beleza, whatsapp, etc.).

6. **CASCADE do Django (ao deletar a Loja)**  
   - `FinanceiroLoja` (OneToOne → CASCADE)  
   - `PagamentoLoja` (FK → Loja CASCADE)  
   - `ProfissionalUsuario` (FK → Loja CASCADE)

### 1.3 Conclusão – exclusão de loja

- **Não ficam órfãos** por `loja_id`: o signal limpa por tipo no default e o schema é dropado no Postgres; FKs com CASCADE removem FinanceiroLoja, PagamentoLoja e ProfissionalUsuario.  
- **Asaas**: LojaAssinatura/AsaasPayment/AsaasCustomer são removidos **antes** do `loja.delete()`, então não restam vínculos por `loja_slug` para essa loja.

---

## 2. Fluxo de exclusão de USUÁRIO (UsuarioSistema)

### 2.1 Onde ocorre

- **superadmin/views.py**: `UsuarioSistemaViewSet.destroy()` (DELETE na API de usuários do sistema).

### 2.2 Ordem das operações

1. Remove **UsuarioSistema**.  
2. Remove o **User** do Django (`user_django.delete()`).

### 2.3 CASCADE ao deletar o User

- **ProfissionalUsuario** (FK → User CASCADE)  
- **PushSubscription** (FK → User CASCADE)  
- **UserSession** (OneToOne → User CASCADE)  
- **Loja** (FK owner → User CASCADE): se o usuário for owner de lojas, as lojas seriam deletadas em cascata; na prática a exclusão de usuário do sistema deve ser usada para perfis que não são donos de loja (ex.: suporte).  
- **HistoricoAcessoGlobal** (FK → User SET_NULL): o registro permanece com `user_id = NULL` (auditoria); não gera órfão de vínculo.

### 2.4 Conclusão – exclusão de usuário

- **Não ficam órfãos** de User: vínculos são removidos por CASCADE ou mantidos de forma controlada (SET_NULL no histórico).

---

## 3. Exclusão do OWNER após exclusão da loja

No `destroy` da loja, **depois** de `loja.delete()`:

- Se o owner **não** tiver outras lojas (`outras_lojas_owner == 0`), o código remove o **User** do owner (`user_to_delete.delete()`).  
- Antes disso, o signal já removeu as **UserSession** do owner.  
- Ao deletar o User, CASCADE remove ProfissionalUsuario, PushSubscription, UserSession, etc.

Não há vínculos órfãos nesse fluxo.

---

## 4. Verificação de órfãos (comandos e melhorias)

### 4.1 Comando existente

- **`verificar_dados_orfaos`**  
  - Verifica tabelas no banco **default** que tenham `loja_id` apontando para loja inexistente.  
  - Uso: `python manage.py verificar_dados_orfaos` (só listar) ou `--remover` / `--dry-run`.

### 4.2 Assinaturas Asaas (loja_slug)

- **LojaAssinatura** usa `loja_slug` (CharField), não FK para Loja.  
- Se uma loja for removida por outro caminho (ex.: shell), pode restar **LojaAssinatura** com `loja_slug` inexistente.  
- Já existem:  
  - **asaas_integration**: `show_orphaned_data`, `cleanup_orphaned_asaas`, `cleanup_orphaned_data`.  
- Foi adicionada verificação de **assinaturas órfãs** (loja_slug sem loja) no comando `verificar_dados_orfaos`, para centralizar a checagem.

### 4.3 Recomendações de uso

- Rodar periodicamente:  
  `python manage.py verificar_dados_orfaos`  
  e, se houver órfãos e for desejado removê-los:  
  `python manage.py verificar_dados_orfaos --remover`  
- Para Asaas: usar também os comandos de órfãos do app `asaas_integration` quando houver integração.

---

## 5. Resumo

| Ação                    | Órfãos por loja/user? | Observação                                      |
|-------------------------|------------------------|-------------------------------------------------|
| Excluir loja (API)      | Não                    | Signal + CASCADE + DROP SCHEMA + Asaas antes    |
| Excluir usuário (API)   | Não                    | CASCADE no User                                |
| Excluir owner (após loja) | Não                 | CASCADE no User                                |
| LojaAssinatura (loja_slug) | Só se loja for apagada fora da API | Incluída verificação em `verificar_dados_orfaos` |

O sistema está preparado para **não** deixar cadastros ou vínculos órfãos ao excluir lojas e usuários pela API; a única exceção controlada é LojaAssinatura por `loja_slug`, coberta pelo comando de verificação e pelos comandos de órfãos do Asaas.

---

## 6. Comandos úteis

```bash
# Verificar se existem órfãos (loja_id ou loja_slug sem loja)
python manage.py verificar_dados_orfaos

# Simular remoção (mostra o que seria removido)
python manage.py verificar_dados_orfaos --dry-run

# Listar e remover órfãos
python manage.py verificar_dados_orfaos --remover
```

Em produção (Heroku):

```bash
heroku run "python backend/manage.py verificar_dados_orfaos" --app lwksistemas
heroku run "python backend/manage.py verificar_dados_orfaos --remover" --app lwksistemas
```
