# Otimização de Código: Limpeza e Consolidação (v998)

**Data**: 17/03/2026  
**Versão**: v998  
**Status**: ✅ CONCLUÍDO

---

## 🎯 OBJETIVO

Realizar limpeza de código obsoleto e consolidar lógica duplicada conforme identificado na análise v994.

---

## 🔧 OTIMIZAÇÕES REALIZADAS

### 1. ✅ Remover Código SQLite Obsoleto

**Arquivo**: `backend/superadmin/services/loja_cleanup_service.py`  
**Método**: `cleanup_database_file()` (linhas 198-242)

**ANTES** (44 linhas):
```python
def cleanup_database_file(self):
    """Remove arquivo SQLite do banco de dados isolado"""
    if not self.database_created:
        self.results['banco_dados'] = {
            'existia': False,
            'nome': self.database_name
        }
        return
    
    try:
        import os
        db_path = settings.BASE_DIR / f'db_{self.database_name}.sqlite3'
        
        if db_path.exists():
            os.remove(db_path)
            logger.info(f"✅ Arquivo do banco removido: {db_path}")
            
            self.results['banco_dados'] = {
                'existia': True,
                'nome': self.database_name,
                'arquivo_removido': True,
                'config_removida': True
            }
        else:
            self.results['banco_dados'] = {
                'existia': True,
                'nome': self.database_name,
                'arquivo_removido': False,
                'motivo': 'Arquivo não encontrado'
            }
            
        # Remover configuração do settings.DATABASES
        if self.database_name in settings.DATABASES:
            del settings.DATABASES[self.database_name]
            logger.info(f"✅ Configuração do banco removida: {self.database_name}")
            
    except Exception as e:
        logger.warning(f"⚠️ Erro ao remover banco: {e}")
        self.results['banco_dados'] = {
            'existia': True,
            'nome': self.database_name,
            'erro': str(e)
        }
```

**DEPOIS** (38 linhas - 13% menor):
```python
def cleanup_database_file(self):
    """
    Remove configuração do banco de dados da loja.
    
    NOTA: Sistema usa PostgreSQL com schemas isolados.
    A remoção do schema é feita pelo signal pre_delete.
    Este método apenas remove a configuração do settings.DATABASES.
    """
    if not self.database_created:
        self.results['banco_dados'] = {
            'existia': False,
            'nome': self.database_name
        }
        return
    
    try:
        # Remover configuração do settings.DATABASES
        if self.database_name in settings.DATABASES:
            del settings.DATABASES[self.database_name]
            logger.info(f"✅ Configuração do banco removida: {self.database_name}")
            
            self.results['banco_dados'] = {
                'existia': True,
                'nome': self.database_name,
                'config_removida': True
            }
        else:
            self.results['banco_dados'] = {
                'existia': True,
                'nome': self.database_name,
                'config_removida': False,
                'motivo': 'Configuração não encontrada'
            }
            
    except Exception as e:
        logger.warning(f"⚠️ Erro ao remover configuração do banco: {e}")
        self.results['banco_dados'] = {
            'existia': True,
            'nome': self.database_name,
            'erro': str(e)
        }
```

**Benefícios**:
- ✅ Removido código SQLite não usado (sistema usa PostgreSQL)
- ✅ Documentação clara sobre responsabilidades
- ✅ Código mais limpo e focado
- ✅ Redução de 6 linhas

---

### 2. ✅ Consolidar Lógica Financeira Duplicada

**Arquivo**: `backend/superadmin/services/loja_creation_service.py`

**Métodos Removidos**:
1. `calcular_valor_mensalidade()` (linhas 179-192)
2. `calcular_datas_vencimento()` (linhas 194-220)

**ANTES** (51 linhas de código duplicado):
```python
@staticmethod
def calcular_valor_mensalidade(loja) -> float:
    """
    Calcula valor da mensalidade baseado no tipo de assinatura
    
    Args:
        loja: Objeto Loja
        
    Returns:
        Valor da mensalidade
    """
    if loja.tipo_assinatura == 'anual':
        return loja.plano.preco_anual / 12 if loja.plano.preco_anual else loja.plano.preco_mensal
    return loja.plano.preco_mensal

@staticmethod
def calcular_datas_vencimento(dia_vencimento: int) -> Tuple:
    """
    Calcula datas de vencimento para primeiro boleto e próxima cobrança
    
    Args:
        dia_vencimento: Dia do mês para vencimento
        
    Returns:
        Tupla (primeiro_vencimento, proxima_cobranca)
    """
    from datetime import date, timedelta
    from calendar import monthrange
    
    hoje = date.today()
    
    # Primeiro boleto: 3 dias a partir de hoje
    primeiro_vencimento = hoje + timedelta(days=3)
    
    # Próxima cobrança: dia fixo no próximo mês
    if hoje.month == 12:
        proximo_mes = 1
        proximo_ano = hoje.year + 1
    else:
        proximo_mes = hoje.month + 1
        proximo_ano = hoje.year
    
    # Ajustar dia se o mês não tiver esse dia
    ultimo_dia_mes = monthrange(proximo_ano, proximo_mes)[1]
    dia_cobranca = min(dia_vencimento, ultimo_dia_mes)
    
    return primeiro_vencimento, primeiro_vencimento
```

**DEPOIS** (0 linhas - métodos removidos):
```python
# Métodos removidos - usar FinanceiroService diretamente
```

**Justificativa**:
- ✅ Lógica já existe em `FinanceiroService` (fonte única de verdade)
- ✅ Nenhum código estava usando esses métodos
- ✅ Evita duplicação e inconsistências
- ✅ Redução de 51 linhas

---

### 3. ✅ Verificar Imports no LojaCreateSerializer

**Arquivo**: `backend/superadmin/serializers.py`

**Status**: ✅ JÁ CORRETO

O serializer já está usando `FinanceiroService` corretamente:

```python
from .services import (
    LojaCreationService,
    DatabaseSchemaService,
    FinanceiroService,  # ✅ Importado
    ProfessionalService
)

# Uso correto
FinanceiroService.criar_financeiro_loja(loja, dia_vencimento)
```

**Nenhuma alteração necessária**.

---

## 📊 ESTATÍSTICAS

### Linhas de Código Removidas
- Código SQLite obsoleto: 6 linhas
- Métodos duplicados: 51 linhas
- **Total removido**: 57 linhas

### Arquivos Modificados
1. `backend/superadmin/services/loja_cleanup_service.py`
2. `backend/superadmin/services/loja_creation_service.py`

### Arquivos Verificados (sem alteração)
1. `backend/superadmin/serializers.py` ✅

---

## ✅ BENEFÍCIOS

### Manutenibilidade
- ✅ Código mais limpo e focado
- ✅ Menos duplicação
- ✅ Fonte única de verdade para lógica financeira

### Performance
- ✅ Menos código para carregar
- ✅ Menos imports desnecessários

### Documentação
- ✅ Comentários claros sobre responsabilidades
- ✅ Código autoexplicativo

---

## 🧪 TESTES NECESSÁRIOS

### Criação de Loja
- ⏳ Criar nova loja via API
- ⏳ Verificar que financeiro é criado corretamente
- ⏳ Verificar que schema PostgreSQL é criado

### Exclusão de Loja
- ⏳ Excluir loja via API
- ⏳ Verificar que configuração é removida
- ⏳ Verificar que schema PostgreSQL é removido
- ⏳ Verificar que não há órfãos

---

## 📝 PRÓXIMOS PASSOS

### Opcional (Futuro)
1. ⏳ Remover imports não usados em outros arquivos
2. ⏳ Consolidar outras duplicações se encontradas
3. ⏳ Adicionar type hints completos

---

## 📈 VERSÕES

| Versão | Descrição |
|--------|-----------|
| v994 | Análise e identificação de código obsoleto |
| v995 | Correção FK CASCADE |
| v996 | Limpeza de órfãos |
| v997 | Correção de arquivos corrompidos |
| v998 | Limpeza e consolidação de código |

---

## ✅ CONCLUSÃO

Código otimizado com sucesso:
- ✅ 57 linhas removidas
- ✅ Duplicação eliminada
- ✅ Documentação melhorada
- ✅ Sistema mais limpo e manutenível

**Status**: Pronto para testes e deploy.
