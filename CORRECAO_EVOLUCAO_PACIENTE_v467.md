# Correção - Erro ao Salvar Evolução do Paciente - v467

## 🐛 Problema Identificado

**Erro**: 400 Bad Request ao tentar salvar evolução do paciente na clínica
**URL**: https://lwksistemas.com.br/loja/clinica-harmonis-5898/login
**Endpoint**: `POST /api/clinica/evolucoes/`

### Logs do Erro
```
2026-02-08T02:47:48 Bad Request: /api/clinica/evolucoes/
2026-02-08T02:47:48 "POST /api/clinica/evolucoes/ HTTP/1.1" 400 43
```

## 🔍 Causa Raiz

O serializer `EvolucaoPacienteSerializer` **NÃO estava herdando de `BaseLojaSerializer`**, então:
- ❌ Não adicionava automaticamente o campo `loja_id`
- ❌ Causava erro 400 ao tentar salvar (campo obrigatório faltando)

### Código com Problema (Antes)
```python
class EvolucaoPacienteSerializer(serializers.ModelSerializer):  # ❌ Herda de ModelSerializer
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    agendamento_info = serializers.SerializerMethodField()
    imc = serializers.ReadOnlyField()

    class Meta:
        model = EvolucaoPaciente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'data_evolucao']  # ❌ Sem loja_id
```

## ✅ Solução Implementada

Alterado o serializer para herdar de `BaseLojaSerializer`:

```python
class EvolucaoPacienteSerializer(BaseLojaSerializer):  # ✅ Herda de BaseLojaSerializer
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    profissional_nome = serializers.CharField(source='profissional.nome', read_only=True)
    agendamento_info = serializers.SerializerMethodField()
    imc = serializers.ReadOnlyField()

    class Meta:
        model = EvolucaoPaciente
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'data_evolucao', 'loja_id']  # ✅ Com loja_id
```

### O que `BaseLojaSerializer` faz:
1. ✅ Adiciona automaticamente `loja_id` no `create()`
2. ✅ Garante isolamento de dados por loja
3. ✅ Evita erros de campo obrigatório faltando

## 📋 Campos Obrigatórios do Modelo

O modelo `EvolucaoPaciente` tem 3 campos obrigatórios (sem `blank=True`):
1. **queixa_principal** - TextField (queixa principal do paciente)
2. **areas_tratamento** - TextField (áreas a serem tratadas)
3. **procedimento_realizado** - TextField (descrição do procedimento)

Esses campos estão corretamente marcados como `required` no formulário frontend.

## 🚀 Deploy

**Deploy v467 - Backend**
- Plataforma: Heroku
- Status: ✅ Sucesso
- Arquivo modificado: `backend/clinica_estetica/serializers.py`
- Commit: `fix: EvolucaoPaciente serializer herdar de BaseLojaSerializer (v467)`

## 🧪 Como Testar

1. Acessar: https://lwksistemas.com.br/loja/clinica-harmonis-5898/dashboard
2. Ir para "Sistema de Consultas"
3. Selecionar uma consulta
4. Clicar na aba "Evolução"
5. Clicar em "📊 Registrar Evolução"
6. Preencher os campos obrigatórios:
   - Queixa Principal *
   - Áreas de Tratamento *
   - Procedimento Realizado *
7. Clicar em "Salvar Evolução"
8. ✅ Deve salvar com sucesso e mostrar mensagem "✅ Evolução registrada com sucesso!"

## 📝 Arquivos Modificados

```
backend/clinica_estetica/serializers.py
```

## ✨ Resultado Final

Agora o sistema de evolução do paciente está funcionando corretamente:
- ✅ Salva evolução com sucesso
- ✅ Adiciona `loja_id` automaticamente
- ✅ Mantém isolamento de dados por loja
- ✅ Todos os campos obrigatórios validados

---

**Data**: 08/02/2026
**Versão**: v467
**Status**: ✅ Concluído e em Produção
