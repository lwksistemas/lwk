# ✅ Adicionar Cadastro de Funcionários nos Dashboards

## 📋 Status Atual

### Backend - ✅ COMPLETO
- ✅ Modelos de Funcionário existem em todos os tipos de loja:
  - `clinica_estetica.models.Funcionario`
  - `servicos.models.Funcionario`
  - `restaurante.models.Funcionario`
  - `crm_vendas.models.Vendedor` (equivalente a funcionário)
  
- ✅ **Vínculo automático do administrador como funcionário JÁ IMPLEMENTADO**
  - Arquivo: `backend/superadmin/signals.py`
  - Signal: `create_funcionario_for_loja_owner`
  - Quando uma loja é criada, o administrador é automaticamente cadastrado como funcionário

### Frontend - ❌ FALTANDO

**Dashboards que NÃO têm cadastro de funcionários nas Ações Rápidas:**
1. ❌ Clínica de Estética (`clinica-estetica.tsx`)
2. ❌ CRM Vendas (`crm-vendas.tsx`)

## 🎯 O que precisa ser feito

### 1. Dashboard Clínica de Estética

**Adicionar botão nas Ações Rápidas:**
```tsx
<button 
  onClick={handleFuncionarios}
  className="p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-lg"
  style={{ backgroundColor: '#EC4899' }} // Rosa - Funcionários
>
  <div className="text-3xl mb-2">👥</div>
  <div className="text-sm">Funcionários</div>
</button>
```

**Adicionar estado e handler:**
```tsx
const [showModalFuncionarios, setShowModalFuncionarios] = useState(false);
const handleFuncionarios = () => setShowModalFuncionarios(true);
```

**Adicionar modal:**
```tsx
{showModalFuncionarios && (
  <ModalFuncionarios 
    loja={loja}
    onClose={() => setShowModalFuncionarios(false)}
  />
)}
```

### 2. Dashboard CRM Vendas

**Adicionar botão nas Ações Rápidas:**
```tsx
<button 
  onClick={() => setShowModalFuncionarios(true)} 
  className="p-3 md:p-4 rounded-lg text-white font-semibold hover:opacity-90 transition-all transform hover:scale-105 shadow-md" 
  style={{ backgroundColor: loja.cor_primaria }}
>
  <div className="text-2xl md:text-3xl mb-1 md:mb-2">👥</div>
  <div className="text-xs md:text-sm">Funcionários</div>
</button>
```

**Nota:** No CRM Vendas, "Vendedor" é o equivalente a "Funcionário", mas vamos adicionar um botão separado para "Funcionários" para manter consistência.

### 3. Criar Componente Modal de Funcionários

Criar um modal reutilizável que:
- Lista todos os funcionários da loja
- Permite criar novo funcionário
- Permite editar funcionário existente
- Permite excluir funcionário
- Mostra o administrador da loja (criado automaticamente)

## 📝 Endpoints da API

### Clínica de Estética
- GET `/api/clinica/funcionarios/` - Listar
- POST `/api/clinica/funcionarios/` - Criar
- PUT `/api/clinica/funcionarios/{id}/` - Editar
- DELETE `/api/clinica/funcionarios/{id}/` - Excluir

### Serviços
- GET `/api/servicos/funcionarios/` - Listar
- POST `/api/servicos/funcionarios/` - Criar
- PUT `/api/servicos/funcionarios/{id}/` - Editar
- DELETE `/api/servicos/funcionarios/{id}/` - Excluir

### Restaurante
- GET `/api/restaurante/funcionarios/` - Listar
- POST `/api/restaurante/funcionarios/` - Criar
- PUT `/api/restaurante/funcionarios/{id}/` - Editar
- DELETE `/api/restaurante/funcionarios/{id}/` - Excluir

### CRM Vendas (Vendedores)
- GET `/api/crm/vendedores/` - Listar
- POST `/api/crm/vendedores/` - Criar
- PUT `/api/crm/vendedores/{id}/` - Editar
- DELETE `/api/crm/vendedores/{id}/` - Excluir

## ✅ Conclusão

**O que JÁ FUNCIONA:**
- ✅ Backend completo com modelos de Funcionário
- ✅ Vínculo automático do administrador como funcionário ao criar loja
- ✅ APIs REST para CRUD de funcionários

**O que FALTA:**
- ❌ Adicionar botão "Funcionários" nas Ações Rápidas dos dashboards
- ❌ Criar modais de gerenciamento de funcionários no frontend

**Próximos Passos:**
1. Adicionar botão nas Ações Rápidas de cada dashboard
2. Criar modal de gerenciamento de funcionários
3. Integrar com as APIs existentes
4. Testar criação, edição e exclusão de funcionários
