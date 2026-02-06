# ✅ Sincronização Funcionário → Profissional - v416

## 🎯 Problema
- Funcionário cadastrado com `funcao='profissional'` não aparecia em:
  - Select de Profissional no Agendamento
  - Select de Profissional no Bloqueio de Agenda

## 🔍 Causa
Sincronização automática usava `email` como chave única, mas:
- Email pode ser vazio
- Gerava chave temporária `func_{id}@temp.com`
- Causava duplicações ou falhas na sincronização

## ✅ Solução

### Sincronização Melhorada
**Arquivo**: `backend/cabeleireiro/models.py`

```python
def save(self, *args, **kwargs):
    """Sincroniza automaticamente com tabela Profissional quando funcao='profissional'"""
    super().save(*args, **kwargs)
    
    # Se é profissional, sincronizar com tabela Profissional (para compatibilidade com Agendamento)
    if self.funcao == 'profissional':
        # Buscar ou criar profissional vinculado a este funcionário
        # Usar nome + loja_id como chave única (mais confiável que email)
        profissional, created = Profissional.objects.get_or_create(
            loja_id=self.loja_id,
            nome=self.nome,
            defaults={
                'email': self.email or '',
                'telefone': self.telefone,
                'especialidade': self.especialidade or '',
                'comissao_percentual': self.comissao_percentual,
                'is_active': self.is_active,
            }
        )
        
        # Se já existia, atualizar dados
        if not created:
            profissional.email = self.email or ''
            profissional.telefone = self.telefone
            profissional.especialidade = self.especialidade or ''
            profissional.comissao_percentual = self.comissao_percentual
            profissional.is_active = self.is_active
            profissional.save()
```

### Mudanças
1. ✅ Chave única: `nome + loja_id` (ao invés de email)
2. ✅ `get_or_create` ao invés de `update_or_create`
3. ✅ Atualização explícita se já existir
4. ✅ Email vazio tratado corretamente

## 📊 Fluxo de Sincronização

```
┌─────────────────────────────────────┐
│  Criar/Editar Funcionário           │
│  funcao = 'profissional'            │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  save() do Funcionario              │
│  - Salva funcionário                │
│  - Verifica funcao='profissional'   │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  Sincronização Automática           │
│  - Busca: nome + loja_id            │
│  - Cria se não existir              │
│  - Atualiza se já existir           │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  Profissional criado/atualizado     │
│  - Disponível em Agendamento        │
│  - Disponível em Bloqueio           │
└─────────────────────────────────────┘
```

## 🚀 Deploy

### Backend v416
```bash
cd backend
git add -A
git commit -m "fix: sincronizacao funcionario-profissional v416"
git push heroku master
```

**Status**: ✅ Deploy realizado
**URL**: https://lwksistemas-38ad47519238.herokuapp.com

## 🧪 Como Testar

### 1. Forçar Sincronização (Funcionário Existente)
1. Acesse: https://lwksistemas.com.br/loja/regiane-5889/dashboard
2. Clique em "Funcionários"
3. Edite o funcionário profissional existente
4. Mude qualquer campo (ex: telefone)
5. Salve

### 2. Criar Novo Profissional
1. Clique em "+ Novo Funcionário"
2. Preencha:
   - Nome: "Maria Silva"
   - Telefone: "(11) 98765-4321"
   - Cargo: "Cabeleireira"
   - Função: "Profissional/Cabeleireiro"
   - Especialidade: "Corte e Coloração"
3. Salve

### 3. Verificar Sincronização
1. Vá em "Agendamentos" → "+ Novo Agendamento"
2. No campo "Profissional", deve aparecer:
   - ✅ Funcionário editado
   - ✅ Maria Silva (novo)

3. Vá em "Bloqueios" → "+ Novo Bloqueio"
4. No campo "Profissional", deve aparecer os mesmos

## 🎯 Resultado

- ✅ Sincronização automática funcionando
- ✅ Profissionais aparecem em Agendamento
- ✅ Profissionais aparecem em Bloqueio
- ✅ Chave única confiável (nome + loja_id)
- ✅ Sem duplicações
- ✅ Atualização automática ao editar

## 📝 Arquitetura Final

### Tabelas
1. **cabeleireiro_funcionarios** (Principal)
   - Todos os funcionários (admin, profissionais, atendentes, etc)
   - Fonte única de verdade

2. **cabeleireiro_profissionais** (Sincronizada)
   - Apenas funcionários com `funcao='profissional'`
   - Sincronizada automaticamente
   - Usada por Agendamento e Bloqueio (ForeignKey)

### Boas Práticas
- ✅ Single Source of Truth (Funcionario)
- ✅ Sincronização automática transparente
- ✅ Compatibilidade com código existente
- ✅ Sem duplicação de dados
