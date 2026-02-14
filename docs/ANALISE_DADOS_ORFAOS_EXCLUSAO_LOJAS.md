# Análise: dados órfãos após exclusão de lojas

## Objetivo

Garantir que, ao excluir uma loja (ou todas), **nenhum dado fique órfão** (registros que referenciam uma loja inexistente).

## Fluxo atual de exclusão

1. **views.py `destroy()`** (antes de `loja.delete()`):
   - Remove **Chamados de suporte** (por `loja_slug`)
   - Remove configuração do banco em `settings.DATABASES` e arquivo SQLite (se existir)
   - Remove dados **Asaas** (API + locais: LojaAssinatura, AsaasPayment, AsaasCustomer)

2. **loja.delete()** dispara o signal **pre_delete** `delete_all_loja_data` (signals.py):
   - Por **tipo de loja**: deleta no banco **default** todos os modelos com `loja_id` daquela loja:
     - **Clínica de Estética**: Funcionario, Cliente, Agendamento, Profissional, Procedimento
     - **CRM Vendas**: Vendedor, Cliente, Lead, Venda, Pipeline, Produto
     - **Restaurante**: Reserva, Pedido, ItemCardapio, Categoria, Mesa, Cliente, Funcionario, Fornecedor, NotaFiscalEntrada, **MovimentoEstoque**, **RegistroPesoBalança**, EstoqueItem
     - **Serviços**: Agendamento, OrdemServico, Orcamento, Servico, Profissional, Cliente, Categoria, Funcionario
     - **Cabeleireiro**: BloqueioAgenda, Agendamento, Venda, Funcionario, HorarioFuncionamento, Produto, Servico, Profissional, Cliente
   - **Clínica da Beleza**: dados ficam no **schema PostgreSQL** da loja; o schema é removido com `DROP SCHEMA ... CASCADE`, eliminando todas as tabelas. No banco default, **ProfissionalUsuario** tem FK para Loja com **CASCADE**, então é removido pelo Django.
   - Deleta **UserSession** do owner.
   - **DROP SCHEMA** no PostgreSQL (nome do schema = `database_name` da loja).

3. **Após loja.delete()** (views.py):
   - Remove o **owner** (User) se não for usado por outras lojas.

## Modelos com FK para Loja (CASCADE – removidos automaticamente)

- `FinanceiroLoja` (OneToOne CASCADE)
- `PagamentoLoja` (FK CASCADE)
- `ProfissionalUsuario` (FK CASCADE)

## Modelos com SET_NULL (mantidos de propósito)

- `HistoricoAcessoGlobal.loja` → fica `null` para auditoria.
- `ViolacaoSeguranca.loja` → fica `null` para auditoria.

## Ajuste feito no signal (Restaurante)

- **MovimentoEstoque** e **RegistroPesoBalança** têm FK para **EstoqueItem** com **PROTECT**. Por isso passaram a ser deletados **antes** de **EstoqueItem** no bloco Restaurante, evitando falha na exclusão.

## Comando de verificação

Para conferir se ainda existe algum registro órfão (por exemplo após “excluir todas as lojas”):

```bash
# Apenas listar órfãos (por tabela)
python manage.py verificar_dados_orfaos

# Listar e remover órfãos
python manage.py verificar_dados_orfaos --remover

# Simular remoção (não deleta)
python manage.py verificar_dados_orfaos --dry-run
```

O comando considera tabelas que possuem coluna `loja_id` e contam/deletam registros cujo `loja_id` não existe mais em `superadmin_loja`.

## Resumo

- O signal **delete_all_loja_data** cobre todos os tipos de loja (Clínica de Estética, CRM Vendas, Restaurante, Serviços, Cabeleireiro) e a remoção do schema (Clínica da Beleza e demais que usam schema).
- Restaurante: ordem de exclusão ajustada para MovimentoEstoque e RegistroPesoBalança antes de EstoqueItem.
- Comando **verificar_dados_orfaos** serve para auditoria e limpeza pontual de órfãos após exclusão em massa.
