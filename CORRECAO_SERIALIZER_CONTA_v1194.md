# Correção: Serializer de Conta Não Salvava CNPJ e Endereço - v1194

## Data
19/03/2026

## Problema Identificado

Ao cadastrar ou editar uma Conta em:
https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers

Os campos CNPJ e endereço completo não estavam sendo salvos, mesmo após preencher o formulário.

## Causa Raiz

O `ContaSerializer` no backend não incluía os novos campos adicionados na migration `0027_add_complete_company_data_to_conta.py`.

### Serializer Antigo (Incompleto)
```python
class ContaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conta
        fields = [
            'id', 'nome', 'segmento', 'telefone', 'email', 'cidade', 'endereco',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
```

**Campos faltantes:**
- `razao_social`
- `cnpj`
- `inscricao_estadual`
- `site`
- `cep`
- `logradouro`
- `numero`
- `complemento`
- `bairro`
- `uf`

## Solução Implementada

Atualizado o `ContaSerializer` para incluir todos os campos do modelo.

### Serializer Corrigido (Completo)
```python
class ContaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conta
        fields = [
            'id', 'nome', 'razao_social', 'cnpj', 'inscricao_estadual', 'segmento', 
            'telefone', 'email', 'site',
            'cep', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'uf',
            'endereco', 'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
```

## Impacto

### Antes da Correção
❌ CNPJ não era salvo
❌ Razão social não era salva
❌ Inscrição estadual não era salva
❌ Site não era salvo
❌ CEP não era salvo
❌ Logradouro não era salvo
❌ Número não era salvo
❌ Complemento não era salvo
❌ Bairro não era salvo
❌ UF não era salvo
❌ Dados incompletos para propostas e contratos

### Depois da Correção
✅ Todos os campos são salvos corretamente
✅ CNPJ disponível para propostas e contratos
✅ Endereço completo disponível para documentos
✅ Consulta de CNPJ funciona e salva dados
✅ Consulta de CEP funciona e salva dados

## Arquivos Modificados

1. `backend/crm_vendas/serializers.py`
   - Atualizado `ContaSerializer` com todos os campos

## Deploy

- **Versão**: v1194 (backend)
- **Data**: 19/03/2026
- **Status**: ✅ Sucesso

## Como Testar

1. Acesse: https://lwksistemas.com.br/loja/41449198000172/crm-vendas/customers
2. Clique em "Nova Conta" ou edite uma conta existente
3. Preencha os campos:
   - CNPJ (use o botão "Consultar CNPJ" para preencher automaticamente)
   - Razão Social
   - Inscrição Estadual
   - Site
   - CEP (preenche endereço automaticamente)
   - Logradouro, Número, Complemento, Bairro, Cidade, UF
4. Clique em "Salvar"
5. Visualize a conta para confirmar que os dados foram salvos

## Observações

- O campo `endereco` (legado) foi mantido para compatibilidade
- Todos os novos campos são opcionais, exceto "Nome Fantasia"
- Os dados salvos estarão disponíveis para uso em propostas e contratos
- A consulta de CNPJ e CEP agora funciona completamente (busca E salva)

## Lições Aprendidas

Ao adicionar novos campos em um modelo:
1. Criar/atualizar a migration
2. Atualizar o serializer correspondente
3. Atualizar o frontend (formulário)
4. Testar o fluxo completo (criar, editar, visualizar)
5. Verificar se os dados são salvos e recuperados corretamente

## Próximos Passos

- ✅ Testar cadastro de conta com CNPJ
- ✅ Testar consulta de CNPJ
- ✅ Testar consulta de CEP
- Validar uso dos dados em propostas (verificar se CNPJ e endereço aparecem)
- Validar uso dos dados em contratos (verificar se CNPJ e endereço aparecem)
