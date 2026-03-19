# Como Limpar Loja CRM com Dados de Teste

## Problema

A loja **41449198000172** foi criada com dados de teste/exemplo que não deveriam estar lá:
- Vendas cadastradas
- Leads de exemplo
- Atividades de teste
- Outros dados que confundem o cliente

## Solução Imediata

### 1. Identificar a Loja

Primeiro, encontre o ID da loja no banco de dados:

```bash
# No Heroku
heroku run python backend/manage.py shell

# No shell Python
from superadmin.models import Loja
loja = Loja.objects.get(cpf_cnpj='41449198000172')
print(f"ID da loja: {loja.id}")
print(f"Nome: {loja.nome}")
print(f"Slug: {loja.slug}")
exit()
```

### 2. Limpar os Dados

Use o comando criado para limpar TODOS os dados da loja:

```bash
# Primeiro, verificar o que será excluído (sem --confirmar)
heroku run python backend/manage.py limpar_loja_crm <LOJA_ID>

# Exemplo (substitua pelo ID real):
heroku run python backend/manage.py limpar_loja_crm 150

# Se estiver tudo certo, executar com confirmação:
heroku run python backend/manage.py limpar_loja_crm <LOJA_ID> --confirmar
```

O comando irá:
1. Mostrar todos os dados que serão excluídos
2. Pedir confirmação digitando "SIM"
3. Excluir tudo em ordem (respeitando FKs)
4. Verificar se ficou limpo

### 3. Verificar Limpeza

Após executar, verifique se a loja está limpa:

```bash
heroku run python backend/manage.py shell

from crm_vendas.models import Lead, Oportunidade, Atividade
from tenants.middleware import set_current_loja_id

set_current_loja_id(<LOJA_ID>)

print(f"Leads: {Lead.objects.count()}")
print(f"Oportunidades: {Oportunidade.objects.count()}")
print(f"Atividades: {Atividade.objects.count()}")
```

Todos devem retornar **0**.

## Investigação: De Onde Vieram os Dados?

### Possíveis Causas:

1. **Comando Manual Executado**
   - Alguém executou `seed_crm_data` ou `verificar_dados_loja`
   - Esses comandos criam dados de teste

2. **Signal Automático** (improvável)
   - Verificar se há signal que cria dados ao criar loja
   - Não encontramos evidências disso

3. **Dados Copiados de Outra Loja**
   - Verificar se houve migração ou cópia de dados

4. **Teste Manual**
   - Alguém pode ter criado dados manualmente para testar

### Verificar Logs:

```bash
# Ver logs recentes do Heroku
heroku logs --tail --source app

# Procurar por comandos executados
heroku logs --tail | grep "management.commands"
```

## Prevenção: Garantir que Novas Lojas Venham Limpas

### 1. Verificar Signals

Confirmar que NÃO há signal criando dados automaticamente:

```python
# backend/crm_vendas/signals.py
# NÃO deve ter algo como:

@receiver(post_save, sender=Loja)
def criar_dados_exemplo(sender, instance, created, **kwargs):
    if created:
        # ISSO NÃO DEVE EXISTIR
        criar_leads_exemplo(instance)
```

### 2. Documentar Processo de Criação

Criar documentação clara:
- Novas lojas devem vir VAZIAS
- Dados de exemplo só devem ser criados MANUALMENTE
- Comandos de seed são APENAS para desenvolvimento/teste

### 3. Adicionar Aviso nos Comandos

Os comandos `seed_crm_data` e `verificar_dados_loja` já têm avisos, mas podemos melhorar:

```python
# Adicionar no início do comando:
if settings.DEBUG is False:
    self.stdout.write(self.style.ERROR("⚠️  ATENÇÃO: Você está em PRODUÇÃO!"))
    resposta = input("Tem certeza que quer criar dados de teste? (sim/não): ")
    if resposta.lower() != 'sim':
        return
```

## Comando Criado

### `limpar_loja_crm`

**Localização**: `backend/crm_vendas/management/commands/limpar_loja_crm.py`

**Uso**:
```bash
# Ver o que será excluído (sem executar)
python manage.py limpar_loja_crm <LOJA_ID>

# Executar limpeza (com confirmação)
python manage.py limpar_loja_crm <LOJA_ID> --confirmar
```

**O que faz**:
1. Lista todos os dados da loja
2. Pede confirmação (--confirmar + digitar "SIM")
3. Exclui tudo em ordem:
   - Assinaturas Digitais
   - Contratos
   - Propostas
   - Itens de Oportunidade
   - Atividades
   - Oportunidades
   - Contatos
   - Leads
   - Contas
   - Produtos/Serviços
   - Templates
4. Verifica se ficou limpo

**Segurança**:
- Requer `--confirmar` na linha de comando
- Pede confirmação digitando "SIM"
- Usa transaction (rollback em caso de erro)
- Mostra totais antes e depois

## Exemplo Completo

```bash
# 1. Conectar no Heroku
heroku run bash

# 2. Encontrar ID da loja
python backend/manage.py shell
>>> from superadmin.models import Loja
>>> loja = Loja.objects.get(cpf_cnpj='41449198000172')
>>> print(loja.id)
150
>>> exit()

# 3. Ver dados atuais
python backend/manage.py limpar_loja_crm 150

# Saída:
# 🏪 Loja ID: 150
# ============================================================
# 📊 Dados atuais:
#   • Leads: 15
#   • Oportunidades: 8
#   • Atividades: 12
#   • Propostas: 3
#   • Contratos: 1
# 📈 Total de registros: 39
# ❌ Operação cancelada (use --confirmar para executar)

# 4. Executar limpeza
python backend/manage.py limpar_loja_crm 150 --confirmar

# Vai pedir confirmação:
# Digite 'SIM' (em maiúsculas) para confirmar: SIM

# Saída:
# 🗑️  Iniciando limpeza...
#   ✅ 0 assinaturas digitais excluídas
#   ✅ 1 contratos excluídos
#   ✅ 3 propostas excluídas
#   ✅ 0 itens de oportunidade excluídos
#   ✅ 12 atividades excluídas
#   ✅ 8 oportunidades excluídas
#   ✅ 0 contatos excluídos
#   ✅ 15 leads excluídos
#   ✅ 0 contas excluídas
#   ✅ 0 produtos/serviços excluídos
#   ✅ 0 templates de proposta excluídos
#   ✅ 0 templates de contrato excluídos
# ✅ Limpeza concluída com sucesso!
# 📊 Total de registros excluídos: 39
# ✅ Loja completamente limpa!

# 5. Verificar
python backend/manage.py shell
>>> from crm_vendas.models import Lead
>>> from tenants.middleware import set_current_loja_id
>>> set_current_loja_id(150)
>>> Lead.objects.count()
0
```

## Próximos Passos

1. ✅ Limpar a loja 41449198000172
2. ✅ Verificar se há outras lojas com dados de teste
3. ✅ Documentar processo de criação de lojas
4. ✅ Adicionar avisos nos comandos de seed
5. ✅ Comunicar ao cliente que a loja foi limpa

## Contato com Cliente

Mensagem sugerida:

> Olá! Identificamos que sua loja foi criada com alguns dados de exemplo/teste. 
> Já limpamos completamente o sistema e agora está pronto para uso.
> Todos os dados foram removidos e você pode começar a cadastrar seus próprios clientes e vendas.
> Desculpe pelo inconveniente!
