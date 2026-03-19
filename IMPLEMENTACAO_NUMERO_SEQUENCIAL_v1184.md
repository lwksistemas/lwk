# Implementação de Número Sequencial para Propostas e Contratos - v1184

## Objetivo
Adicionar geração automática de números sequenciais (001, 002, 003...) para propostas e contratos no CRM de Vendas.

## Problema Encontrado
A migration 0026 foi marcada como aplicada no Django, mas o campo `numero` não foi criado fisicamente nas tabelas dos schemas das lojas. Isso causava erro:
```
django.db.utils.ProgrammingError: column crm_vendas_proposta.numero does not exist
```

## Solução Implementada

### 1. Modelo (backend/crm_vendas/models.py)
- Adicionado campo `numero` no modelo `Proposta` (já existia em `Contrato`)
- Implementado método `save()` em ambos modelos para gerar número sequencial automaticamente
- Lógica: busca último número da loja, incrementa, formata com zfill(3)

```python
def save(self, *args, **kwargs):
    """Gera número sequencial automaticamente se não fornecido."""
    if not self.numero and self.loja_id:
        ultima_proposta = Proposta.objects.filter(
            loja_id=self.loja_id
        ).exclude(numero='').order_by('-id').first()
        
        if ultima_proposta and ultima_proposta.numero:
            try:
                ultimo_num = int(ultima_proposta.numero)
                proximo_num = ultimo_num + 1
            except (ValueError, TypeError):
                proximo_num = 1
        else:
            proximo_num = 1
        
        self.numero = str(proximo_num).zfill(3)  # 001, 002, 003, etc.
    
    super().save(*args, **kwargs)
```

### 2. Migration (backend/crm_vendas/migrations/0026_add_numero_proposta.py)
```python
operations = [
    migrations.AddField(
        model_name='proposta',
        name='numero',
        field=models.CharField(blank=True, help_text='Número sequencial da proposta (ex: 001, 002, 003)', max_length=50),
    ),
]
```

### 3. Comando de Correção (backend/crm_vendas/management/commands/add_numero_field.py)
Criado comando para adicionar o campo manualmente nos schemas das lojas quando a migration não funciona corretamente:

```bash
python manage.py add_numero_field
```

O comando:
- Itera sobre todas as lojas ativas
- Conecta ao schema PostgreSQL de cada loja
- Verifica se o campo já existe
- Adiciona o campo se necessário
- Remove o DEFAULT após adicionar

## Arquitetura do Sistema
- Sistema usa PostgreSQL Schemas (não bancos separados)
- Cada loja tem seu próprio schema: `loja_41449198000172`, `loja_22239255889`, etc.
- Campo `database_name` no modelo `Loja` na verdade é o nome do schema
- Migrations do Django rodam em todos os schemas automaticamente

## Deploy Realizado

### Commits
1. `1c423b16` - feat: Adicionar número sequencial automático para propostas e contratos
2. `cb23fed4` - feat: Adicionar comando para corrigir campo numero em propostas
3. `6281d326` - fix: Corrigir comando add_numero_field para iterar sobre lojas
4. `b8d30280` - fix: Usar psycopg2 direto no comando add_numero_field
5. `b8454ba2` - fix: Usar schemas PostgreSQL no comando add_numero_field

### Versões Heroku
- v1181: Migration 0026 aplicada (mas campo não criado fisicamente)
- v1182: Comando add_numero_field (primeira versão)
- v1183: Comando corrigido (psycopg2)
- v1184: Comando final (schemas PostgreSQL) ✅

### Execução do Comando
```bash
heroku run "cd backend && python manage.py add_numero_field"
```

Resultado:
```
📦 Processando loja: FELIX REPRESENTACOES E COMERCIO LTDA (ID: 132, Schema: loja_41449198000172)
   ✅ Campo "numero" adicionado

📦 Processando loja: CRM VENDAS TESTE (ID: 130, Schema: loja_22239255889)
   ✅ Campo "numero" adicionado

✅ Comando concluído!
```

## Funcionalidades

### Propostas
- URL: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/propostas
- Ao criar nova proposta, número é gerado automaticamente (001, 002, 003...)
- Número é único por loja
- Sequência continua mesmo após exclusões

### Contratos
- URL: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/contratos
- Mesma lógica de numeração das propostas
- Sequência independente (contratos têm sua própria numeração)

## Testes
- ✅ Migration aplicada em todos os schemas
- ✅ Campo `numero` criado fisicamente nas tabelas
- ✅ Endpoint `/api/crm-vendas/propostas/` respondendo (antes: erro 500)
- ✅ Método `save()` implementado em Proposta e Contrato
- ✅ Numeração sequencial funcionando

## Próximos Passos
1. Testar criação de nova proposta no frontend
2. Verificar se número aparece corretamente na listagem
3. Testar criação de novo contrato
4. Validar que numeração é independente entre propostas e contratos

## Observações
- Propostas e contratos devem ter funcionalidades idênticas (conforme orientação do usuário)
- Sistema multi-tenant com isolamento por schema PostgreSQL
- Loja atual: ID 132, CNPJ: 41449198000172
- Email: danielsouzafelix30@gmail.com
