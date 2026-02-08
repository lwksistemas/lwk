# Sistema de Profissionais e Funcionários - v468

## 📋 Estrutura Atual (CORRETO)

### ✅ Sistema Implementado Corretamente

O sistema já está funcionando conforme solicitado:

## 🏥 Clínica de Estética

### 1️⃣ Botão "Profissional" (👨‍⚕️)
**Função**: Gerenciar profissionais que realizam procedimentos
- Cadastrar profissionais (esteticistas, dermatologistas, etc.)
- Editar dados dos profissionais
- Definir especialidades
- Vincular a agendamentos e consultas
- **NÃO cria funcionário automaticamente**

**Modelo**: `clinica_estetica.models.Profissional`
```python
class Profissional(LojaIsolationMixin, models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    especialidade = models.CharField(max_length=100)
    registro_profissional = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
```

### 2️⃣ Botão "Funcionários" (👥)
**Função**: Gerenciar equipe administrativa e operacional
- **Admin da loja** (criado automaticamente ao criar loja) ✅
- Gerentes
- Atendentes/Recepcionistas
- Caixa
- Outros funcionários administrativos
- **NÃO inclui profissionais**

**Modelo**: `clinica_estetica.models.Funcionario`
```python
class Funcionario(LojaIsolationMixin, models.Model):
    nome = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    telefone = models.CharField(max_length=20)
    cargo = models.CharField(max_length=100)
    funcao = models.CharField(max_length=50, choices=FUNCAO_CHOICES)
    especialidade = models.CharField(max_length=200, blank=True, null=True)
    is_admin = models.BooleanField(default=False)  # Admin da loja
    is_active = models.BooleanField(default=True)
```

## 🔄 Criação Automática do Admin

### Signal: `create_funcionario_for_loja_owner`
**Arquivo**: `backend/superadmin/signals.py`

**Quando**: Ao criar uma nova loja (`post_save` com `created=True`)

**O que faz**:
1. Pega o `owner` da loja (usuário que criou)
2. Cria um `Funcionario` automaticamente com:
   - Nome: `owner.get_full_name()` ou `owner.username`
   - Email: `owner.email`
   - Cargo: `"Administrador"`
   - `is_admin=True` (marca como admin da loja)
   - `loja_id`: ID da loja criada

**Código**:
```python
@receiver(post_save, sender='superadmin.Loja')
def create_funcionario_for_loja_owner(sender, instance, created, **kwargs):
    if not created:
        return
    
    tipo_loja_nome = instance.tipo_loja.nome
    owner = instance.owner
    
    funcionario_data = {
        'nome': owner.get_full_name() or owner.username,
        'email': owner.email,
        'telefone': '',
        'cargo': 'Administrador',
        'is_admin': True,
        'loja_id': instance.id
    }
    
    if tipo_loja_nome == 'Clínica de Estética':
        from clinica_estetica.models import Funcionario
        if not Funcionario.objects.filter(email=owner.email, loja_id=instance.id).exists():
            Funcionario.objects.create(**funcionario_data)
```

## 🛡️ Proteções Implementadas

### No Modal de Funcionários
**Arquivo**: `frontend/components/clinica/modals/ModalFuncionarios.tsx`

1. **Não permite editar admin**:
```typescript
if (funcionario.is_admin) {
  alert('⚠️ O administrador da loja não pode ser editado por aqui.');
  return;
}
```

2. **Não permite excluir admin**:
```typescript
if (is_admin) {
  alert('⚠️ O administrador da loja não pode ser excluído.');
  return;
}
```

3. **Badge visual**: Admin tem badge azul "Admin" para identificação

## 📊 Diferenças Entre Profissional e Funcionário

| Aspecto | Profissional | Funcionário |
|---------|-------------|-------------|
| **Função** | Realiza procedimentos | Administra/opera a clínica |
| **Vinculação** | Agendamentos, Consultas | Gestão, Atendimento |
| **Criação Automática** | ❌ Não | ✅ Sim (apenas admin) |
| **Especialidade** | Obrigatória | Opcional |
| **Registro Profissional** | Sim (CRM, etc.) | Não |
| **Permissões** | Executar procedimentos | Gerenciar sistema |
| **Botão** | 👨‍⚕️ Profissional | 👥 Funcionários |

## ✅ Verificação do Sistema

### Checklist de Funcionamento Correto

- [x] Admin da loja é criado automaticamente como Funcionário ao criar loja
- [x] Botão "Profissional" gerencia apenas profissionais
- [x] Botão "Funcionários" gerencia apenas funcionários
- [x] Profissional NÃO cria funcionário automaticamente
- [x] Admin não pode ser editado/excluído pelo modal
- [x] Modelos separados (Profissional ≠ Funcionario)
- [x] Sem código duplicado ou redundante
- [x] Signal funciona corretamente

## 🎯 Fluxo de Uso

### Ao Criar Loja
1. SuperAdmin cria loja no painel
2. Define owner (usuário administrador)
3. **Signal automático**: Cria Funcionario com `is_admin=True`
4. Owner pode fazer login e gerenciar a loja

### No Dashboard da Clínica
1. **Cadastrar Profissionais**: Botão "👨‍⚕️ Profissional"
   - Esteticistas, dermatologistas, etc.
   - Vinculados a agendamentos e consultas
   
2. **Gerenciar Equipe**: Botão "👥 Funcionários"
   - Admin (já criado automaticamente)
   - Gerentes, atendentes, caixa
   - Controle de permissões

## 📝 Arquivos Principais

### Backend
```
backend/clinica_estetica/models.py          # Modelos Profissional e Funcionario
backend/clinica_estetica/serializers.py     # Serializers (sem vinculação)
backend/clinica_estetica/views.py           # ViewSets separados
backend/superadmin/signals.py               # Signal de criação automática
```

### Frontend
```
frontend/app/(dashboard)/loja/[slug]/dashboard/templates/clinica-estetica.tsx
frontend/components/clinica/modals/ModalProfissionais.tsx
frontend/components/clinica/modals/ModalFuncionarios.tsx
```

## ✨ Conclusão

O sistema está **100% correto** e funcionando conforme solicitado:
- ✅ Profissionais e Funcionários são **separados**
- ✅ Admin é criado **automaticamente** ao criar loja
- ✅ **Não há** vinculação automática entre profissional e funcionário
- ✅ **Não há** código duplicado ou redundante
- ✅ Proteções implementadas para admin

---

**Data**: 08/02/2026
**Versão**: v468
**Status**: ✅ Sistema Correto e Funcionando
