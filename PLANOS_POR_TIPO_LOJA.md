# 💎 PLANOS POR TIPO DE LOJA

## ✅ Implementado: Sistema de Planos Específicos por Tipo

**Novidade**: Cada tipo de loja agora pode ter seus próprios planos personalizados!

---

## 🎯 O QUE FOI IMPLEMENTADO

### 1️⃣ Vinculação Planos ↔ Tipos de Loja
- **Modelo**: Campo `tipos_loja` (ManyToMany) no PlanoAssinatura
- **Flexibilidade**: Um plano pode ser usado por múltiplos tipos
- **Filtro**: API para buscar planos por tipo específico

### 2️⃣ Novos Tipos de Loja Criados

#### 🌸 Clínica de Estética (Rosa #EC4899)
- **Funcionalidades**: Produtos, Serviços, Agendamento, Estoque
- **Template**: clinica
- **Planos Específicos**: 3 planos personalizados

#### 💼 CRM Vendas (Roxo #8B5CF6)
- **Funcionalidades**: Serviços, Agendamento (sem produtos físicos)
- **Template**: crm
- **Planos Específicos**: 3 planos personalizados

### 3️⃣ Planos Personalizados Criados

#### Para Clínica de Estética:
1. **Estética Básica** - R$ 89,90/mês
2. **Estética Profissional** - R$ 149,90/mês  
3. **Estética Premium** - R$ 249,90/mês

#### Para CRM Vendas:
1. **CRM Starter** - R$ 79,90/mês
2. **CRM Business** - R$ 129,90/mês
3. **CRM Enterprise** - R$ 199,90/mês

### 4️⃣ Página de Gerenciamento de Planos
- **URL**: http://localhost:3000/superadmin/planos
- **Funcionalidades**: Listar, criar, editar planos
- **Vinculação**: Selecionar tipos de loja por plano

---

## 📊 RESUMO DO SISTEMA

### Total de Tipos: 5
1. 🟢 **E-commerce** (Verde) - 3 planos gerais
2. 🔵 **Serviços** (Azul) - 3 planos gerais  
3. 🔴 **Restaurante** (Vermelho) - 3 planos gerais
4. 🌸 **Clínica de Estética** (Rosa) - 3 planos específicos
5. 💼 **CRM Vendas** (Roxo) - 3 planos específicos

### Total de Planos: 9
- **3 Planos Gerais**: Básico, Profissional, Enterprise
- **3 Planos Estética**: Estética Básica, Profissional, Premium
- **3 Planos CRM**: CRM Starter, Business, Enterprise

---

## 🔄 COMO FUNCIONA

### 1. Criar Loja - Fluxo Atualizado:
```
Usuário seleciona tipo de loja
         ↓
Sistema carrega planos específicos do tipo
         ↓
Usuário escolhe plano
         ↓
Loja criada com plano correto
```

### 2. API de Planos por Tipo:
```
GET /api/superadmin/planos/por_tipo/?tipo_id=4
```
**Retorna**: Apenas planos disponíveis para o tipo selecionado

### 3. Formulário Dinâmico:
- Seleciona tipo → Carrega planos específicos
- Planos são filtrados automaticamente
- Preços e descrições personalizados

---

## 💰 TABELA DE PREÇOS

### Clínica de Estética:
| Plano | Mensal | Anual | Usuários | Produtos | Storage |
|-------|--------|-------|----------|----------|---------|
| Básica | R$ 89,90 | R$ 899,00 | 3 | 50 | 5GB |
| Profissional | R$ 149,90 | R$ 1.499,00 | 8 | 200 | 15GB |
| Premium | R$ 249,90 | R$ 2.499,00 | 20 | Ilimitado | 50GB |

### CRM Vendas:
| Plano | Mensal | Anual | Usuários | Leads/mês | Storage |
|-------|--------|-------|----------|-----------|---------|
| Starter | R$ 79,90 | R$ 799,00 | 5 | 1.000 | 3GB |
| Business | R$ 129,90 | R$ 1.299,00 | 15 | 5.000 | 10GB |
| Enterprise | R$ 199,90 | R$ 1.999,00 | 50 | Ilimitado | 25GB |

### Planos Gerais (E-commerce, Serviços, Restaurante):
| Plano | Mensal | Anual | Usuários | Produtos | Storage |
|-------|--------|-------|----------|----------|---------|
| Básico | R$ 49,90 | R$ 499,00 | 2 | 50 | 2GB |
| Profissional | R$ 99,90 | R$ 999,00 | 5 | 200 | 10GB |
| Enterprise | R$ 299,90 | R$ 2.999,00 | 50 | Ilimitado | 100GB |

---

## 🎨 PÁGINAS IMPLEMENTADAS

### 1. Tipos de Loja
- **URL**: http://localhost:3000/superadmin/tipos-loja
- **Status**: ✅ Funcionando
- **Novos Tipos**: Clínica de Estética e CRM Vendas visíveis

### 2. Planos de Assinatura  
- **URL**: http://localhost:3000/superadmin/planos
- **Status**: ✅ Funcionando
- **Funcionalidades**:
  - Listar todos os 9 planos
  - Criar novos planos
  - Vincular planos a tipos específicos
  - Ver quantas lojas usam cada plano

### 3. Criar Loja (Atualizado)
- **URL**: http://localhost:3000/superadmin/lojas
- **Status**: ✅ Funcionando
- **Novidade**: Planos filtrados por tipo selecionado

---

## 🧪 COMO TESTAR

### 1. Ver Novos Tipos:
```
1. Acesse: http://localhost:3000/superadmin/tipos-loja
2. Login: superadmin / super123
3. Veja os 5 tipos (incluindo Clínica e CRM)
```

### 2. Ver Planos por Tipo:
```
1. Acesse: http://localhost:3000/superadmin/planos
2. Veja os 9 planos organizados
3. Note os planos específicos para cada tipo
```

### 3. Criar Loja com Planos Específicos:
```
1. Acesse: http://localhost:3000/superadmin/lojas
2. Clique em "+ Nova Loja"
3. Selecione "Clínica de Estética"
4. Veja apenas os 3 planos de estética
5. Selecione "CRM Vendas"
6. Veja apenas os 3 planos de CRM
```

### 4. Testar API:
```bash
# Planos para Clínica de Estética (ID: 4)
curl "http://localhost:8000/api/superadmin/planos/por_tipo/?tipo_id=4" \
  -H "Authorization: Bearer $TOKEN"

# Planos para CRM Vendas (ID: 5)  
curl "http://localhost:8000/api/superadmin/planos/por_tipo/?tipo_id=5" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### Backend:

#### 1. Modelo Atualizado:
```python
class PlanoAssinatura(models.Model):
    # ... campos existentes ...
    tipos_loja = models.ManyToManyField(
        TipoLoja, 
        related_name='planos', 
        blank=True
    )
```

#### 2. API Endpoint:
```python
@action(detail=False, methods=['get'])
def por_tipo(self, request):
    tipo_id = request.query_params.get('tipo_id')
    if tipo_id:
        planos = self.queryset.filter(
            tipos_loja__id=tipo_id, 
            is_active=True
        )
        return Response(serializer.data)
```

#### 3. Script de Criação:
```python
# backend/criar_novos_tipos.py
# Cria tipos e planos automaticamente
```

### Frontend:

#### 1. Carregamento Dinâmico:
```typescript
const loadPlanosPorTipo = async (tipoId: string) => {
  const response = await apiClient.get(
    `/superadmin/planos/por_tipo/?tipo_id=${tipoId}`
  );
  setPlanos(response.data);
};
```

#### 2. Formulário Reativo:
```typescript
// Quando tipo muda, carrega planos específicos
if (name === 'tipo_loja' && value) {
  loadPlanosPorTipo(value);
  setFormData(prev => ({ ...prev, plano: '' }));
}
```

---

## 📈 VANTAGENS DO SISTEMA

### 1. Personalização por Segmento:
- Clínicas têm planos focados em agendamento
- CRM tem planos focados em leads/vendas
- E-commerce tem planos focados em produtos

### 2. Preços Adequados:
- Clínicas: R$ 89,90 - R$ 249,90
- CRM: R$ 79,90 - R$ 199,90  
- E-commerce: R$ 49,90 - R$ 299,90

### 3. Funcionalidades Específicas:
- Clínicas: Agendamento + Produtos de beleza
- CRM: Sem produtos físicos, foco em leads
- E-commerce: Produtos + Delivery + Estoque

### 4. Limites Apropriados:
- CRM: Sem limite de produtos (não usa)
- Clínicas: Limite médio de produtos
- E-commerce: Foco em volume de produtos

---

## 🎯 PRÓXIMOS PASSOS

### 1. Dashboards Específicos:
- [ ] Dashboard para clínicas (agenda, procedimentos)
- [ ] Dashboard para CRM (funil de vendas, leads)
- [ ] Templates visuais diferenciados

### 2. Funcionalidades Avançadas:
- [ ] Migração entre planos
- [ ] Planos com trial específico por tipo
- [ ] Descontos por tipo de negócio

### 3. Relatórios:
- [ ] Relatórios por tipo de loja
- [ ] Análise de conversão por plano
- [ ] Métricas específicas por segmento

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Backend:
- [x] Adicionar campo tipos_loja ao modelo PlanoAssinatura
- [x] Criar migration
- [x] Criar tipos Clínica de Estética e CRM Vendas
- [x] Criar planos específicos para cada tipo
- [x] Implementar API por_tipo
- [x] Atualizar serializers

### Frontend:
- [x] Criar página de planos (/superadmin/planos)
- [x] Atualizar formulário de criação de loja
- [x] Implementar carregamento dinâmico de planos
- [x] Mostrar planos filtrados por tipo

### Documentação:
- [x] Criar PLANOS_POR_TIPO_LOJA.md
- [x] Documentar novos tipos e planos
- [x] Guia de testes

---

## 🎉 RESULTADO FINAL

### ✅ Sistema Completo:
- 5 tipos de loja (incluindo 2 novos)
- 9 planos personalizados
- Planos específicos por tipo
- Formulário dinâmico
- Página de gerenciamento
- APIs funcionando

### 🎨 Novos Tipos Bonitos:
- **Clínica de Estética**: Rosa, focada em beleza e agendamento
- **CRM Vendas**: Roxo, focada em vendas e relacionamento

### 💰 Preços Personalizados:
- Cada tipo tem planos adequados ao seu negócio
- Preços competitivos por segmento
- Funcionalidades específicas

**Sistema de Planos por Tipo 100% Implementado! 💎**

---

## 📚 ARQUIVOS CRIADOS/MODIFICADOS

### Backend:
- `backend/superadmin/models.py` (campo tipos_loja)
- `backend/superadmin/views.py` (endpoint por_tipo)
- `backend/superadmin/serializers.py` (tipos_loja_nomes)
- `backend/criar_novos_tipos.py` (script de criação)
- `backend/superadmin/migrations/0003_*.py` (migration)

### Frontend:
- `frontend/app/(dashboard)/superadmin/planos/page.tsx` (nova página)
- `frontend/app/(dashboard)/superadmin/lojas/page.tsx` (formulário atualizado)

### Documentação:
- `PLANOS_POR_TIPO_LOJA.md` (este arquivo)

**Pronto para criar lojas com planos específicos! 🚀**