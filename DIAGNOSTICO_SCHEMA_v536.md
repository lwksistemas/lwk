# Diagnóstico do Problema de Schema - v536

## Problema Crítico Identificado

Os logs mostram uma **contradição impossível**:

```
[BloqueioAgenda] Profissional 5 existe no schema da loja? True
```

Mas o PostgreSQL retorna:

```
Key (profissional_id)=(5) is not present in table "clinica_profissionais"
```

## Causa Raiz

O `Profissional.objects.filter(id=5).exists()` está retornando `True` porque está consultando o **schema errado** (provavelmente o schema público ou de outra loja), não o schema `loja_teste_5889`.

### Por que isso acontece?

1. **DRF carrega o objeto antes da validação**: Quando o serializer recebe `profissional=5`, o DRF automaticamente faz `Profissional.objects.get(id=5)` ANTES de chamar `validate()`

2. **Schema não está configurado corretamente**: O `search_path` do PostgreSQL pode não estar configurado corretamente quando o DRF carrega o objeto

3. **LojaIsolationManager pode não estar sendo usado**: O DRF pode estar usando o manager padrão ao invés do `LojaIsolationManager`

## Solução: Forçar Uso do Schema Correto

### Opção 1: Validar com Query Raw SQL

Modificar a validação para usar SQL direto com `search_path` explícito:

```python
def validate(self, data):
    profissional_id = data.get('profissional')
    
    if profissional_id:
        from tenants.middleware import get_current_loja_id
        from django.db import connection
        from superadmin.models import Loja
        
        loja_id = get_current_loja_id()
        loja = Loja.objects.get(id=loja_id)
        schema_name = loja.database_name.replace('-', '_')
        
        # Consultar diretamente no schema correto
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name}, public")
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM clinica_profissionais WHERE id = %s AND is_active = true)",
                [profissional_id.id if hasattr(profissional_id, 'id') else profissional_id]
            )
            existe = cursor.fetchone()[0]
        
        if not existe:
            raise serializers.ValidationError({
                'profissional': f"Profissional não existe nesta loja"
            })
    
    return data
```

### Opção 2: Desabilitar ForeignKey no Serializer

Fazer o serializer aceitar apenas o ID (int) ao invés do objeto:

```python
class BloqueioAgendaSerializer(serializers.ModelSerializer):
    profissional = serializers.PrimaryKeyRelatedField(
        queryset=Profissional.objects.none(),  # Vazio - validar manualmente
        required=False,
        allow_null=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Definir queryset dinamicamente com o schema correto
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        if loja_id:
            self.fields['profissional'].queryset = Profissional.objects.filter(
                loja_id=loja_id,
                is_active=True
            )
```

### Opção 3: Aceitar Apenas ID (Mais Simples)

Modificar o serializer para aceitar apenas o ID como inteiro:

```python
class BloqueioAgendaSerializer(serializers.ModelSerializer):
    profissional = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_profissional(self, value):
        if value is not None:
            from tenants.middleware import get_current_loja_id
            loja_id = get_current_loja_id()
            
            # Validar com query explícita
            existe = Profissional.objects.filter(
                id=value,
                loja_id=loja_id,
                is_active=True
            ).exists()
            
            if not existe:
                raise serializers.ValidationError(
                    f"Profissional ID {value} não existe nesta loja"
                )
        
        return value
    
    def create(self, validated_data):
        # Converter ID para objeto antes de salvar
        profissional_id = validated_data.pop('profissional', None)
        bloqueio = BloqueioAgenda(**validated_data)
        
        if profissional_id:
            bloqueio.profissional_id = profissional_id
        
        bloqueio.save()
        return bloqueio
```

## Teste para Confirmar o Problema

Execute no Heroku:

```bash
heroku run python backend/manage.py shell --app lwksistemas
```

```python
from superadmin.models import Loja
from clinica_estetica.models import Profissional
from django.db import connection

# Buscar loja
loja = Loja.objects.get(id=114)
schema_name = loja.database_name.replace('-', '_')

print(f"Schema: {schema_name}")

# Configurar search_path
with connection.cursor() as cursor:
    cursor.execute(f"SET search_path TO {schema_name}, public")
    cursor.execute("SELECT id, nome FROM clinica_profissionais ORDER BY id")
    profissionais = cursor.fetchall()
    print(f"Profissionais no schema {schema_name}:")
    for prof in profissionais:
        print(f"  ID: {prof[0]} | Nome: {prof[1]}")
```

## Próximos Passos

1. ✅ Implementar Opção 3 (mais simples e segura)
2. ⏳ Testar em produção
3. ⏳ Confirmar que o problema foi resolvido
