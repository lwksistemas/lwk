# Análise: Erro 400 no Cadastro de Pacientes

## Data
24/03/2026 - 18:55

## Problema Identificado

Múltiplos erros 400 (Bad Request) no endpoint `POST /api/clinica-beleza/patients/`

### Logs do Heroku
```
2026-03-24T18:55:21.296793+00:00 app[web.1]: Bad Request: /api/clinica-beleza/patients/
2026-03-24T18:55:21.297163+00:00 app[web.1]: 10.1.31.78 - - [24/Mar/2026:15:55:21 -0300] "POST /api/clinica-beleza/patients/ HTTP/1.1" 400 83
```

## Análise Técnica

### 1. Endpoint
- **Arquivo**: `backend/clinica_beleza/views.py`
- **Classe**: `PatientListView`
- **Método**: `post()`
- **Linha**: 207-212

```python
def post(self, request):
    serializer = PatientSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### 2. Serializer
- **Arquivo**: `backend/clinica_beleza/serializers.py`
- **Classe**: `PatientSerializer`
- **Linha**: 150-163

```python
class PatientSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'])

    class Meta:
        model = Patient
        exclude = ['loja_id']
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'cpf': {'required': False, 'allow_blank': True, 'allow_null': True},
            'address': {'required': False, 'allow_blank': True, 'allow_null': True},
            'notes': {'required': False, 'allow_blank': True, 'allow_null': True},
        }
```

### 3. Modelo
- **Arquivo**: `backend/clinica_beleza/models.py`
- **Classe**: `Patient` (herda de `ClienteBase`)
- **Arquivo Base**: `backend/agenda_base/models.py`

```python
class ClienteBase(LojaIsolationMixin, models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome")  # OBRIGATÓRIO
    email = models.EmailField(blank=True, null=True)  # OPCIONAL
    telefone = models.CharField(max_length=20, verbose_name="Telefone")  # OBRIGATÓRIO
    cpf = models.CharField(max_length=14, blank=True, null=True)  # OPCIONAL
    # ... outros campos
```

## Possíveis Causas do Erro 400

### 1. Campo `telefone` Obrigatório
- No modelo `ClienteBase`, o campo `telefone` NÃO tem `blank=True`
- Isso significa que é OBRIGATÓRIO no banco de dados
- Mas o serializer marca `phone` como `required=False`
- **CONFLITO**: Serializer aceita sem telefone, mas modelo rejeita

### 2. Campo `nome` Obrigatório
- O campo `nome` também é obrigatório no modelo
- Se o frontend enviar `name` ao invés de `nome`, pode falhar
- Patient tem property `name` que mapeia para `nome`, mas serializer pode não estar usando

### 3. Mapeamento de Campos
O modelo Patient usa properties para compatibilidade:
- `name` → `nome`
- `phone` → `telefone`
- `birth_date` → `data_nascimento`
- `address` → `endereco`
- `notes` → `observacoes`
- `active` → `is_active`

Mas o serializer pode não estar respeitando esse mapeamento corretamente.

## Solução Proposta

### Opção 1: Tornar `telefone` Opcional no Modelo (RECOMENDADO)
Modificar `ClienteBase` para permitir telefone vazio:

```python
telefone = models.CharField(
    max_length=20, 
    blank=True,  # ← ADICIONAR
    null=True,   # ← ADICIONAR
    verbose_name="Telefone"
)
```

**Justificativa**: 
- Migração 0007 já tornou phone opcional: `patient_phone_optional.py`
- Mas a migração pode não ter sido aplicada corretamente
- Ou foi aplicada apenas no Patient, não no ClienteBase

### Opção 2: Tornar `phone` Obrigatório no Serializer
```python
phone = serializers.CharField(required=True, max_length=20)
```

**Problema**: Força usuário a sempre informar telefone, pode não ser desejado.

### Opção 3: Adicionar Validação Customizada
Adicionar validação no serializer para garantir que campos obrigatórios sejam enviados.

## Próximos Passos

1. ✅ Verificar migração 0007 (`patient_phone_optional.py`)
2. ✅ Confirmar se migração foi aplicada no banco
3. ✅ Se não foi aplicada, aplicar migração
4. ✅ Se foi aplicada mas não funcionou, criar nova migração para ClienteBase
5. ✅ Adicionar logging detalhado no endpoint para capturar `serializer.errors`
6. ✅ Testar cadastro de paciente sem telefone

## Logs Necessários

Para diagnosticar melhor, precisamos adicionar logging:

```python
def post(self, request):
    serializer = PatientSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # ✅ ADICIONAR LOGGING
    logger.error(f"Erro ao criar paciente: {serializer.errors}")
    logger.error(f"Dados recebidos: {request.data}")
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

## Status
🔍 **EM INVESTIGAÇÃO** - Aguardando verificação das migrações e logs detalhados
