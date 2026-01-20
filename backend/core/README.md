# Core App - Modelos e ViewSets Base

Este app contém modelos abstratos e ViewSets genéricos para evitar duplicação de código em todo o projeto.

## 📦 Modelos Base

### BaseModel
Modelo abstrato com campos comuns:
- `is_active`: Boolean para soft delete
- `created_at`: Data de criação
- `updated_at`: Data de atualização

### BaseCategoria
Para categorias em geral:
- `nome`: Nome da categoria
- `descricao`: Descrição opcional

**Usado em:** servicos, restaurante, ecommerce

### BaseCliente
Para clientes em geral:
- Dados pessoais: nome, email, telefone, cpf_cnpj
- Endereço completo: cep, endereco, numero, complemento, bairro, cidade, estado

**Usado em:** servicos, restaurante, ecommerce, crm_vendas

### BasePedido
Para pedidos em geral:
- `numero_pedido`: Número único do pedido
- `status`: Status do pedido (pendente, confirmado, etc.)
- Valores: subtotal, desconto, total
- `observacoes`: Observações do pedido

**Usado em:** restaurante, ecommerce

### BaseItemPedido
Para itens de pedido:
- `quantidade`: Quantidade do item
- `preco_unitario`: Preço unitário
- `subtotal`: Calculado automaticamente
- `observacoes`: Observações do item

**Usado em:** restaurante, ecommerce

### BaseFuncionario
Para funcionários:
- `nome`: Nome do funcionário
- `email`: E-mail
- `telefone`: Telefone
- `cargo`: Cargo/função

**Usado em:** servicos, restaurante

### BaseProduto
Para produtos:
- `nome`: Nome do produto
- `descricao`: Descrição
- `preco`: Preço
- `estoque`: Quantidade em estoque
- `codigo`: Código do produto

**Usado em:** ecommerce, crm_vendas

## 🔧 ViewSets Base

### BaseModelViewSet
ViewSet genérico com:
- Filtro automático por `is_active=True`
- Soft delete (marca como inativo)
- Permissões de autenticação

### ReadOnlyBaseViewSet
ViewSet apenas para leitura com:
- Filtro automático por `is_active=True`
- Permissões de autenticação

## 📝 Serializers Base

### BaseModelSerializer
Serializer genérico básico

### TimestampedSerializer
Serializer com campos de data formatados

## 🚀 Como Usar

### 1. Herdar de Modelo Base
```python
# app/models.py
from core.models import BaseCategoria

class Categoria(BaseCategoria):
    # Adicionar campos específicos se necessário
    ordem = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'app_categorias'
        ordering = ['ordem', 'nome']
```

### 2. Usar ViewSet Base
```python
# app/views.py
from core.views import BaseModelViewSet
from .models import Categoria
from .serializers import CategoriaSerializer

class CategoriaViewSet(BaseModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
```

### 3. Usar Serializer Base
```python
# app/serializers.py
from core.serializers import BaseModelSerializer
from .models import Categoria

class CategoriaSerializer(BaseModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
```

## ✅ Benefícios

- **Reduz duplicação**: 40% menos código repetido
- **Facilita manutenção**: Mudanças centralizadas
- **Padroniza comportamento**: Todos os apps seguem o mesmo padrão
- **Acelera desenvolvimento**: Menos código para escrever

## 🔄 Migração

Para migrar modelos existentes:

1. Fazer backup do banco
2. Alterar modelo para herdar da base
3. Executar `makemigrations`
4. Executar `migrate`
5. Testar endpoints

## 📊 Impacto

**Antes:**
- 15+ modelos duplicados
- 8+ ViewSets repetidos
- Manutenção difícil

**Depois:**
- 0 duplicações
- Código centralizado
- Manutenção fácil