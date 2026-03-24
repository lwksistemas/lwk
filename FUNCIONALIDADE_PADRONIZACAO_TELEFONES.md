# Padronização Automática de Telefones e Texto - v1308

## Data
24/03/2026

## Objetivo
Padronizar automaticamente:
1. Telefones no formato brasileiro
2. Texto em MAIÚSCULAS para campos específicos

Melhora consistência, facilita buscas e apresentação profissional.

## 1. Padronização de Telefones

### Formatos Suportados

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

## 2. Conversão para Maiúsculas

### Campos Convertidos Automaticamente
- Nome
- Empresa / Razão Social
- Cidade
- Estado
- Bairro
- Cargo
- Especialidade
- Segmento

### Entrada (aceita qualquer formato)
- `joão silva`
- `Maria Santos`
- `PEDRO OLIVEIRA`
- `  carlos  ` (com espaços extras)

### Saída (padronizado)
- `JOÃO SILVA`
- `MARIA SANTOS`
- `PEDRO OLIVEIRA`
- `CARLOS` (espaços removidos)

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

#### PhoneNormalizationMixin (apenas telefones)
```python
from core.serializer_mixins import PhoneNormalizationMixin

class MeuSerializer(PhoneNormalizationMixin, serializers.ModelSerializer):
    phone_fields = ['telefone', 'celular']
    
    class Meta:
        model = MeuModel
        fields = '__all__'
```

#### UpperCaseNormalizationMixin (apenas maiúsculas)
```python
from core.serializer_mixins import UpperCaseNormalizationMixin

class MeuSerializer(UpperCaseNormalizationMixin, serializers.ModelSerializer):
    uppercase_fields = ['nome', 'empresa', 'cidade']
    
    class Meta:
        model = MeuModel
        fields = '__all__'
```

#### TextNormalizationMixin (telefones + maiúsculas) - RECOMENDADO
```python
from core.serializer_mixins import TextNormalizationMixin

class MeuSerializer(TextNormalizationMixin, serializers.ModelSerializer):
    phone_fields = ['telefone']
    uppercase_fields = ['nome', 'empresa']
    
    class Meta:
        model = MeuModel
        fields = '__all__'
```

O mixin automaticamente:
- Normaliza telefones na entrada (método `validate`)
- Converte texto para maiúsculas na entrada
- Normaliza telefones na saída (método `to_representation`)
- Converte texto para maiúsculas na saída

### 3. Campos Padrão Normalizados

#### Telefones
Se não especificar `phone_fields`, o mixin normaliza automaticamente:
- `telefone`
- `phone`
- `celular`
- `whatsapp`
- `telefone_comercial`
- `telefone_residencial`
- `owner_telefone`

#### Maiúsculas
Se não especificar `uppercase_fields`, o mixin converte automaticamente:
- `nome`
- `name`
- `empresa`
- `razao_social`
- `cidade`
- `estado`
- `bairro`
- `cargo`
- `especialidade`
- `segmento`

## Serializers Atualizados

### Clínica da Beleza
- ✅ `PatientSerializer`
  - Telefone: `phone`, `telefone`
  - Maiúsculas: `name`, `nome`, `cidade`, `estado`, `address`, `endereco`

### CRM de Vendas
- ✅ `VendedorSerializer`
  - Telefone: `telefone`
  - Maiúsculas: `nome`, `cargo`
  
- ✅ `ContaSerializer`
  - Telefone: `telefone`
  - Maiúsculas: `nome`, `razao_social`, `segmento`, `cidade`, `bairro`, `uf`
  
- ✅ `LeadSerializer` e `LeadListSerializer`
  - Telefone: `telefone`
  - Maiúsculas: `nome`, `empresa`, `cidade`, `bairro`, `uf`
  
- ✅ `ContatoSerializer`
  - Telefone: `telefone`
  - Maiúsculas: `nome`, `cargo`

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
  "name": "joão silva",
  "phone": "11 9 8765-4321",
  "cidade": "são paulo"
}

Resposta:
{
  "id": 1,
  "name": "JOÃO SILVA",
  "phone": "(11) 98765-4321",
  "cidade": "SÃO PAULO"
}
```

### Cadastro de Lead
```json
POST /api/crm-vendas/leads/
{
  "nome": "maria santos",
  "empresa": "empresa teste ltda",
  "telefone": "21987654321",
  "cidade": "rio de janeiro"
}

Resposta:
{
  "id": 1,
  "nome": "MARIA SANTOS",
  "empresa": "EMPRESA TESTE LTDA",
  "telefone": "(21) 98765-4321",
  "cidade": "RIO DE JANEIRO"
}
```

### Cadastro de Conta
```json
POST /api/crm-vendas/contas/
{
  "nome": "pedro oliveira",
  "razao_social": "pedro oliveira me",
  "segmento": "tecnologia",
  "telefone": "1133334444",
  "cidade": "são paulo",
  "bairro": "centro"
}

Resposta:
{
  "id": 1,
  "nome": "PEDRO OLIVEIRA",
  "razao_social": "PEDRO OLIVEIRA ME",
  "segmento": "TECNOLOGIA",
  "telefone": "(11) 3333-4444",
  "cidade": "SÃO PAULO",
  "bairro": "CENTRO"
}
```

## Testes

**Arquivos**: 
- `backend/core/tests_phone_utils.py` - Testes de telefone
- `backend/core/tests_uppercase_mixin.py` - Testes de maiúsculas

Executar testes:
```bash
# Todos os testes
python backend/manage.py test core

# Apenas telefones
python backend/manage.py test core.tests_phone_utils

# Apenas maiúsculas
python backend/manage.py test core.tests_uppercase_mixin
```

Testes cobrem:

### Telefones
- ✅ Limpeza de telefones
- ✅ Formatação de celular com/sem DDD
- ✅ Formatação de fixo com/sem DDD
- ✅ Telefones já formatados
- ✅ Telefones vazios
- ✅ Telefones inválidos
- ✅ Validação de DDD
- ✅ Validação de celular
- ✅ Normalização completa

### Maiúsculas
- ✅ Conversão de texto para maiúsculas
- ✅ Campos vazios não causam erro
- ✅ Remoção de espaços extras
- ✅ Texto já em maiúsculas permanece igual
- ✅ Caracteres especiais preservados
- ✅ Campos não especificados não são convertidos
- ✅ Mixin combinado (telefone + maiúsculas)

## Benefícios

1. **Consistência**: Todos os telefones e textos no mesmo formato
2. **Busca Facilitada**: Buscar funciona independente do formato digitado
3. **UX Melhorada**: Usuário pode digitar como quiser, sistema padroniza
4. **Apresentação Profissional**: Dados sempre em maiúsculas ficam mais formais
5. **Validação**: Detecta telefones inválidos automaticamente
6. **Manutenibilidade**: Centralizado em um único lugar
7. **Reutilizável**: Mixin pode ser aplicado em qualquer serializer
8. **Sem Duplicatas**: Evita cadastros duplicados por diferença de case (JOÃO vs joão)

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
- `backend/core/serializer_mixins.py` - Mixins para serializers (telefone + maiúsculas)
- `backend/core/tests_phone_utils.py` - Testes de telefone
- `backend/core/tests_uppercase_mixin.py` - Testes de maiúsculas
- `FUNCIONALIDADE_PADRONIZACAO_TELEFONES.md` - Esta documentação

### Modificados
- `backend/clinica_beleza/serializers.py` - PatientSerializer com TextNormalizationMixin
- `backend/crm_vendas/serializers.py` - Serializers do CRM com TextNormalizationMixin

## Deploy
- **Versão**: v1308 (próximo deploy)
- **Plataforma**: Heroku
- **Impacto**: Baixo - apenas formatação, não quebra dados existentes
