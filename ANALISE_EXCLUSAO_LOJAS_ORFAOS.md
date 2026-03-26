# Análise: Sistema de Exclusão de Lojas e Verificação de Órfãos

**Data**: 25/03/2026  
**Status**: ✅ Sistema limpo após exclusão de 7 lojas de teste

---

## RESUMO EXECUTIVO

O sistema possui um robusto mecanismo de exclusão em cascata que previne dados órfãos quando uma loja é excluída. Após a exclusão de 7 lojas de teste, foi realizada verificação completa e limpeza de 3 usuários órfãos encontrados.

---

## 1. MECANISMO DE EXCLUSÃO AUTOMÁTICA

### 1.1. Signal `delete_all_loja_data` (pre_delete)

**Arquivo**: `backend/superadmin/signals.py` (linhas 311-700)

Este signal é executado ANTES da exclusão da loja e garante limpeza completa de todos os dados relacionados.

#### Ordem de Exclusão (Cascata):

1. **LojaAssinatura** (Asaas)
   - Remove assinaturas vinculadas por `loja_slug`
   - Previne órfãos na integração Asaas

2. **Dados Operacionais por Tipo de App**
   
   **Clínica de Estética**:
   - Funcionários
   - Clientes
   - Agendamentos
   - Profissionais
   - Procedimentos

   **CRM Vendas**:
   - Atividades
   - Oportunidades
   - Leads
   - Contatos
   - Contas
   - Vendedores

   **Restaurante**:
   - Reservas
   - Pedidos
   - Itens Cardápio
   - Categorias
   - Mesas
   - Clientes
   - Funcionários
   - Fornecedores
   - Notas Fiscais
   - Movimentos Estoque (antes de EstoqueItem - FK PROTECT)
   - Registros Peso (antes de EstoqueItem - FK PROTECT)
   - Itens Estoque

   **Serviços**:
   - Agendamentos
   - Ordens de Serviço
   - Orçamentos
   - Serviços
   - Profissionais
   - Clientes
   - Categorias
   - Funcionários

   **Clínica da Beleza**:
   - Pagamentos (antes de Appointment)
   - Agendamentos
   - Bloqueios Horário
   - Horários Trabalho Profissional
   - Campanhas Promoção
   - Procedimentos
   - Profissionais
   - Pacientes

   **Cabeleireiro**:
   - Bloqueios Agenda
   - Agendamentos
   - Vendas
   - Funcionários
   - Horários Funcionamento
   - Produtos
   - Serviços
   - Profissionais
   - Clientes

3. **Sessões de Usuário**
   - Remove todas as sessões do owner (`UserSession`)
   - Usa `owner_id` para evitar problemas de transação

4. **Schema PostgreSQL**
   - Verifica se está usando PostgreSQL (produção)
   - Valida que não é schema público
   - Executa `DROP SCHEMA IF EXISTS "{schema_name}" CASCADE`
   - Remove TODAS as tabelas do schema da loja

5. **Rede de Segurança (Safety Net)**
   - Limpa tabelas do schema `public` com `loja_id`
   - Lista de tabelas: `TABELAS_LOJA_ID_DEFAULT`
   - Cada tabela usa `transaction.atomic()` (savepoint)
   - Falha em uma tabela não aborta a transação principal

6. **Configuração do Banco**
   - Remove config do `settings.DATABASES`
   - Previne nomes órfãos no default

7. **Arquivos Órfãos**
   - Remove diretório `backups/{slug}/`
   - Remove arquivos NF-e em `media/nfe_restaurante/` com prefixo `loja_{id}_`

### 1.2. Signal `remove_owner_if_orphan` (post_delete)

**Arquivo**: `backend/superadmin/signals.py` (linhas 702-730)

Executado APÓS a exclusão da loja para remover o owner se ele ficar órfão.

**Características**:
- Usa `transaction.on_commit()` para executar APÓS o commit
- Verifica se owner possui outras lojas
- Remove owner apenas se não for superuser
- Usa `delete_user_raw()` para evitar problemas com tabelas inexistentes

---

## 2. CAMPOS DE ENDEREÇO NO MODELO LOJA

**Arquivo**: `backend/superadmin/models.py` (linhas 167-173)

```python
# Endereço
cep = models.CharField(max_length=9, blank=True)
logradouro = models.CharField(max_length=200, blank=True)
numero = models.CharField(max_length=20, blank=True)
complemento = models.CharField(max_length=100, blank=True)
bairro = models.CharField(max_length=100, blank=True)
cidade = models.CharField(max_length=100, blank=True)
uf = models.CharField(max_length=2, blank=True)
```

**Observações**:
- Todos os campos são `blank=True` (opcionais)
- Sistema faz consulta automática de CEP no frontend
- Campos são preenchidos automaticamente ao digitar CEP

---

## 3. SERIALIZER DE CRIAÇÃO DE LOJA

**Arquivo**: `backend/superadmin/serializers.py` (linhas 226-350)

### 3.1. Campos Incluídos

```python
fields = [
    'nome', 'slug', 'descricao', 'cpf_cnpj',
    'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
    'tipo_loja', 'plano', 'tipo_assinatura', 'provedor_boleto_preferido',
    'owner_full_name', 'owner_username', 'owner_password', 'owner_email', 'owner_telefone', 'dia_vencimento',
    'logo', 'cor_primaria', 'cor_secundaria', 'dominio_customizado'
]
```

### 3.2. Fluxo de Criação

1. **Processar dados do owner**
   - Extrair nome completo, username, email, telefone
   - Gerar senha provisória se não fornecida

2. **Criar ou atualizar owner**
   - Usa `LojaCreationService.criar_ou_atualizar_owner()`

3. **Gerar slug**
   - Prioridade: slug enviado > CPF/CNPJ (11+ dígitos) > slug vazio
   - Valida e processa slug

4. **Criar loja**
   - Salva todos os campos incluindo endereço completo

5. **Configurar schema do banco**
   - Usa `DatabaseSchemaService.configurar_schema_completo()`

6. **Criar financeiro**
   - Usa `FinanceiroService.criar_financeiro_loja()`

7. **Criar profissional/funcionário admin**
   - Usa `ProfessionalService.criar_profissional_por_tipo()`

8. **Integração Asaas**
   - Signal automático: `create_asaas_subscription_on_loja_creation`
   - Cria: AsaasCustomer, AsaasPayment, LojaAssinatura

---

## 4. VERIFICAÇÃO DE ÓRFÃOS REALIZADA

### 4.1. Scripts Criados

1. **`backend/verificar_orfaos_loja_41449198000172.py`**
   - Verificação específica para uma loja

2. **`backend/verificar_orfaos_sistema_completo.py`**
   - Verificação completa com Django

3. **`backend/verificar_orfaos_simples.py`**
   - Verificação sem dependências Django (usando psycopg2)

### 4.2. Resultados da Verificação

**Executado em**: 25/03/2026 via Heroku CLI

```
✅ Schemas PostgreSQL: Nenhum órfão
   - 3 schemas ativos correspondentes às 3 lojas ativas

❌ Usuários órfãos: 3 encontrados
   - IDs: 156, 167, 168

⚠️ Asaas: Tabela não existe no schema public (normal)

✅ Backups: Diretório não existe

✅ Media: Diretório não existe
```

### 4.3. Limpeza Realizada

**Script**: `backend/limpar_usuarios_orfaos.py`

**Processo**:
1. Identificar usuários órfãos (sem lojas vinculadas)
2. Resolver dependências:
   - `user_sessions`
   - `auth_user_groups`
   - `auth_user_user_permissions`
3. Excluir usuários órfãos

**Resultado**: 3 usuários órfãos excluídos com sucesso

**Verificação Final**: Sistema limpo ✅

---

## 5. LOJAS ATIVAS NO SISTEMA

Após a limpeza, o sistema possui 3 lojas ativas:

- **Loja ID 134**
- **Loja ID 167**
- **Loja ID 168**

---

## 6. PROBLEMA DE EMISSÃO DE NOTA FISCAL

### 6.1. Contexto

**Problema**: Lojas criadas ANTES do v1320 já têm clientes no Asaas SEM endereço

**Correção v1320**: Incluir endereço completo ao criar cliente no Asaas

**Arquivos Modificados**:
1. `backend/superadmin/sync_service.py` (linhas 575-585)
2. `backend/superadmin/asaas_service.py` (linhas 120-132)
3. `backend/superadmin/cobranca_service.py` (linhas 60-67)

**Campos Adicionados ao `loja_data`**:
```python
loja_data = {
    'nome': loja.nome,
    'slug': loja.slug,
    'email': loja.owner.email,
    'cpf_cnpj': loja.cpf_cnpj or '000.000.000-00',
    'telefone': getattr(loja.owner, 'telefone', ''),
    # ✅ CORREÇÃO v1320: Incluir endereço completo para emissão de NF
    'endereco': loja.logradouro or '',
    'numero': loja.numero or '',
    'complemento': loja.complemento or '',
    'bairro': loja.bairro or '',
    'cidade': loja.cidade or '',
    'estado': loja.uf or '',
    'cep': loja.cep or '',
}
```

### 6.2. Teste Planejado

**Loja de Teste**: https://lwksistemas.com.br/loja/41449198000172/login  
**CNPJ**: 41.449.198/0001-72

**Fluxo**:
1. ⏳ Excluir loja existente
2. ⏳ Importar backup da loja
3. ⏳ Pagar boleto da loja restaurada
4. 🔍 Verificar se NF é emitida com sucesso

---

## 7. CONCLUSÕES

### 7.1. Pontos Fortes

✅ **Sistema de exclusão robusto**
- Signal `delete_all_loja_data` cobre todos os tipos de app
- Ordem de exclusão respeita dependências (FK PROTECT)
- Rede de segurança para tabelas no schema public

✅ **Prevenção de órfãos**
- Schema PostgreSQL é removido com CASCADE
- Arquivos (backups, media) são limpos
- Owner órfão é removido automaticamente

✅ **Serializer completo**
- Todos os campos de endereço incluídos
- Validação e processamento de dados
- Integração automática com Asaas

### 7.2. Pontos de Atenção

⚠️ **Lojas antigas sem endereço**
- Criadas antes do v1320
- Cliente no Asaas sem endereço
- Emissão de NF falha

⚠️ **Usuários órfãos**
- 3 usuários órfãos encontrados após exclusão de 7 lojas
- Signal `remove_owner_if_orphan` deveria ter removido automaticamente
- Possível falha no signal ou exclusão manual de lojas

### 7.3. Recomendações

1. **Monitorar signal `remove_owner_if_orphan`**
   - Verificar logs para identificar falhas
   - Adicionar mais logging para debug

2. **Executar verificação periódica**
   - Script `verificar_orfaos_simples.py` via cron
   - Alertar se órfãos forem encontrados

3. **Teste de emissão de NF**
   - Aguardar usuário importar backup
   - Monitorar logs quando boleto for pago
   - Validar que NF é emitida com sucesso

4. **Documentação**
   - Manter `INSTRUCOES_VERIFICAR_ORFAOS.md` atualizado
   - Adicionar troubleshooting para problemas comuns

---

## 8. ARQUIVOS RELACIONADOS

### 8.1. Backend

- `backend/superadmin/signals.py` - Signals de exclusão
- `backend/superadmin/models.py` - Modelo Loja com campos de endereço
- `backend/superadmin/serializers.py` - LojaCreateSerializer
- `backend/superadmin/services.py` - Services de criação de loja
- `backend/superadmin/sync_service.py` - Sincronização com Asaas
- `backend/superadmin/asaas_service.py` - Integração Asaas
- `backend/superadmin/cobranca_service.py` - Cobrança de lojas
- `backend/asaas_integration/invoice_service.py` - Emissão de NF

### 8.2. Scripts de Verificação

- `backend/verificar_orfaos_loja_41449198000172.py`
- `backend/verificar_orfaos_sistema_completo.py`
- `backend/verificar_orfaos_simples.py`
- `backend/limpar_usuarios_orfaos.py`

### 8.3. Documentação

- `INSTRUCOES_VERIFICAR_ORFAOS.md`
- `STATUS_EMISSAO_NOTA_FISCAL.md`
- `ANALISE_EXCLUSAO_LOJAS_ORFAOS.md` (este arquivo)

---

## 9. VERIFICAÇÃO DO FRONTEND

### 9.1. Análise Realizada

**Documento**: `ANALISE_FRONTEND_ORFAOS.md`

**Resultado**: ✅ Nenhum dado órfão encontrado no código fonte

**Verificações**:
- ✅ Nenhuma referência hardcoded a lojas excluídas
- ✅ Nenhum arquivo estático específico de loja
- ✅ Apenas uso dinâmico de storage (sem dados hardcoded)
- ⚠️ Cache de build (.next) contém referências compiladas (558MB)

### 9.2. Referências Encontradas

**Apenas exemplos em placeholders**:
- `frontend/components/superadmin/lojas/ModalNovaLoja.tsx`
  - Linha 110: Comentário explicativo
  - Linha 446: Placeholder do input
  - Linha 450: Exemplo de URL

**Observação**: Estas referências são aceitáveis pois são apenas exemplos para o usuário.

### 9.3. Limpeza Recomendada

**Cache de Build (.next)**:
- Tamanho: 558MB
- Contém código compilado com referências antigas
- Deve ser limpo antes do próximo deploy

**Scripts Criados**:
1. `limpar-cache-frontend.sh` - Limpeza local
2. `deploy-limpo-vercel.sh` - Deploy limpo no Vercel

**Execução**:
```bash
# Limpeza local
./limpar-cache-frontend.sh

# Deploy limpo
./deploy-limpo-vercel.sh
```

### 9.4. Arquitetura de Dados

**Roteamento Dinâmico**:
- Padrão: `/loja/[slug]/*`
- Todas as rotas são dinâmicas
- Dados buscados via API

**Storage**:
- Cookies: `loja_slug`, `loja_usa_crm`, `user_type`
- SessionStorage: `current_loja_id`, `loja_slug`
- LocalStorage: `pwa_loja_slug`, `crm_loja_info`

**Observação**: Todos os dados são dinâmicos, sem valores hardcoded.

---

## 10. PRÓXIMOS PASSOS

### 10.1. Backend

1. ⏳ **Aguardar usuário importar backup da loja 41449198000172**
2. ⏳ **Monitorar logs quando boleto for pago**
3. ⏳ **Verificar se NF é emitida com sucesso**
4. 🔍 **Investigar por que signal `remove_owner_if_orphan` não removeu os 3 usuários**
5. 📝 **Adicionar mais logging no signal para debug**

### 10.2. Frontend

1. ⏳ **Limpar cache de build**: Executar `./limpar-cache-frontend.sh`
2. ⏳ **Deploy limpo no Vercel**: Executar `./deploy-limpo-vercel.sh`
3. ⏳ **Testar páginas**: Confirmar que lojas excluídas retornam 404
4. ⏳ **Verificar logs do Vercel**: Monitorar erros 404
5. 📝 **Documentar processo**: Adicionar ao README

---

**Última Atualização**: 25/03/2026  
**Autor**: Kiro AI Assistant
