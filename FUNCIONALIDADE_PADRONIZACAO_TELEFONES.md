# Padronização Automática de Telefones - v1307

## Data
24/03/2026

## Objetivo
Padronizar automaticamente todos os telefones cadastrados no sistema para o formato brasileiro, melhorando consistência e facilitando buscas.

## Formatos Suportados

### Entrada (aceita qualquer formato)
- `11987654321`
- `(11) 98765-4321`
- `11 9 8765-4321`
- `11 9 8765 4321`
- `+55 11 98765-4321`

### Saída (padronizado)
- Celular com DDD (11 dígitos): `(11) 98765-4321`
- Fixo com DDD (10 dígitos): `(11) 3333-4444`
- Celular sem DDD (9 dígitos): `98765-4321`
- Fixo sem DDD (8 dígitos): `3333-4444`

## Implementação

### 1. Utilitários de Telefone
**Arquivo**: `backend/core/phone_utils.py`

Funções disponíveis:
- `limpar_telefone(telefone)`: Remove caracteres não numéricos
- `formatar_telefone_brasileiro(telefone)`: Formata no padrão brasileiro
- `validar_telefone_brasileiro(telefone)`: Valida formato e DDD
- `normalizar_telefone(telefone)`: Função principal (limpa + formata)

```python
from core.phone_utils import normalizar_telefone

# Exemplo
telefone = normalizar_telefone("11 9 8765-4321")
# Resultado: "(11) 98765-4321"
```

### 2. Mixin para Serializers
**Arquivo**: `backend/core/serializer_mixins.py`

```python
from core.serializer_mixins import PhoneNormalizationMixin

class MeuSerializer(PhoneNormalizationMixin, serializers.ModelSerializer):
    # Campos de telefone a normalizar (opcional)
    phone_fields = ['telefone', 'celular']
    
    class Meta:
        model = MeuModel
        fields = '__all__'
```

O mixin automaticamente:
- Normaliza telefones na entrada (método `validate`)
- Normaliza telefones na saída (método `to_representation`)

### 3. Campos Padrão Normalizados

Se não especificar `phone_fields`, o mixin normaliza automaticamente:
- `telefone`
- `phone`
- `celular`
- `whatsapp`
- `telefone_comercial`
- `telefone_residencial`
- `owner_telefone`

## Serializers Atualizados

### Clínica da Beleza
- ✅ `PatientSerializer` - campo `phone` e `telefone`

### CRM de Vendas
- ✅ `VendedorSerializer` - campo `telefone`
- ✅ `ContaSerializer` - campo `telefone`
- ✅ `LeadSerializer` - campo `telefone`
- ✅ `LeadListSerializer` - campo `telefone`
- ✅ `ContatoSerializer` - campo `telefone`

## Validações

### Quantidade de Dígitos
- ✅ 8 dígitos: Fixo sem DDD
- ✅ 9 dígitos: Celular sem DDD
- ✅ 10 dígitos: Fixo com DDD
- ✅ 11 dígitos: Celular com DDD
- ❌ Outros: Retorna apenas números (pode ser internacional)

### DDD Válido
- ✅ DDDs entre 11 e 99
- ❌ DDDs menores que 11 ou maiores que 99

### Celular
- ✅ Deve começar com 9 (após DDD)
- ❌ Celular que não começa com 9 é inválido

## Exemplos de Uso

### Cadastro de Paciente
```json
POST /api/clinica-beleza/patients/
{
  "name": "João Silva",
  "phone": "11 9 8765-4321"
}

Resposta:
{
  "id": 1,
  "name": "João Silva",
  "phone": "(11) 98765-4321"
}
```

### Cadastro de Lead
```json
POST /api/crm-vendas/leads/
{
  "nome": "Maria Santos",
  "telefone": "21987654321"
}

Resposta:
{
  "id": 1,
  "nome": "Maria Santos",
  "telefone": "(21) 98765-4321"
}
```

## Testes

**Arquivo**: `backend/core/tests_phone_utils.py`

Executar testes:
```bash
python backend/manage.py test core.tests_phone_utils
```

Testes cobrem:
- ✅ Limpeza de telefones
- ✅ Formatação de celular com/sem DDD
- ✅ Formatação de fixo com/sem DDD
- ✅ Telefones já formatados
- ✅ Telefones vazios
- ✅ Telefones inválidos
- ✅ Validação de DDD
- ✅ Validação de celular
- ✅ Normalização completa

## Benefícios

1. **Consistência**: Todos os telefones no mesmo formato
2. **Busca Facilitada**: Buscar por telefone funciona independente do formato digitado
3. **UX Melhorada**: Usuário pode digitar como quiser, sistema padroniza
4. **Validação**: Detecta telefones inválidos automaticamente
5. **Manutenibilidade**: Centralizado em um único lugar
6. **Reutilizável**: Mixin pode ser aplicado em qualquer serializer

## Próximos Passos

### Aplicar em Outros Apps
- [ ] Clínica Estética
- [ ] Cabeleireiro
- [ ] Restaurante
- [ ] Serviços
- [ ] Superadmin (Loja.owner_telefone)

### Melhorias Futuras
- [ ] Suporte a telefones internacionais
- [ ] Máscara de input no frontend
- [ ] Validação de telefone via API (verificar se existe)
- [ ] Formatação automática no frontend (React)
- [ ] Migração para normalizar telefones existentes no banco

## Arquivos Criados/Modificados

### Criados
- `backend/core/phone_utils.py` - Utilitários de telefone
- `backend/core/serializer_mixins.py` - Mixin para serializers
- `backend/core/tests_phone_utils.py` - Testes unitários
- `FUNCIONALIDADE_PADRONIZACAO_TELEFONES.md` - Esta documentação

### Modificados
- `backend/clinica_beleza/serializers.py` - PatientSerializer com mixin
- `backend/crm_vendas/serializers.py` - Serializers do CRM com mixin

## Deploy
- **Versão**: v1307 (próximo deploy)
- **Plataforma**: Heroku
- **Impacto**: Baixo - apenas formatação, não quebra dados existentes
