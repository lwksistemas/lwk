# 🧪 Guia de Testes - Sistema de Monitoramento

## 📋 Visão Geral

Este guia explica como executar e criar testes para o Sistema de Monitoramento e Segurança.

## 🚀 Executando Testes

### Método 1: Script Automatizado

```bash
./scripts/run_tests.sh
```

Este script:
- Ativa o ambiente virtual
- Instala dependências de teste
- Executa todos os testes
- Gera relatório de coverage

### Método 2: Manual

```bash
cd backend
source venv/bin/activate
pip install -r requirements-test.txt
pytest superadmin/tests/ -v
```

### Executar Testes Específicos

```bash
# Apenas testes do SecurityDetector
pytest superadmin/tests/test_security_detector.py -v

# Apenas testes do Cache
pytest superadmin/tests/test_cache.py -v

# Teste específico
pytest superadmin/tests/test_security_detector.py::TestSecurityDetector::test_detect_brute_force -v
```

### Com Coverage

```bash
pytest superadmin/tests/ --cov=superadmin --cov-report=html
```

Relatório gerado em: `backend/htmlcov/index.html`

## 📊 Testes Implementados

### 1. test_security_detector.py

Testa o detector de padrões suspeitos.

**Testes**:
- ✅ `test_detect_brute_force` - Detecção de brute force
- ✅ `test_detect_rate_limit` - Detecção de rate limit
- ✅ `test_detect_cross_tenant` - Detecção de cross-tenant
- ✅ `test_detect_mass_deletion` - Detecção de mass deletion
- ✅ `test_detect_ip_change` - Detecção de mudança de IP
- ✅ `test_no_false_positives` - Sem falsos positivos
- ✅ `test_run_all_detections` - Execução de todas as detecções
- ✅ `test_criticidade_automatica` - Mapeamento de criticidade

**Cobertura**: ~90% do SecurityDetector

### 2. test_cache.py

Testa o serviço de cache.

**Testes**:
- ✅ `test_set_and_get` - Armazenar e recuperar
- ✅ `test_get_nonexistent` - Valor inexistente
- ✅ `test_delete` - Deletar valor
- ✅ `test_clear_all` - Limpar tudo
- ✅ `test_get_or_set_cache_miss` - Cache miss
- ✅ `test_get_or_set_cache_hit` - Cache hit
- ✅ `test_ttl_expiration` - Expiração de TTL
- ✅ `test_prefix_isolation` - Isolamento de prefixo
- ✅ `test_decorator_cache_miss` - Decorator com miss
- ✅ `test_decorator_with_params` - Decorator com parâmetros
- ✅ `test_decorator_custom_ttl` - Decorator com TTL customizado
- ✅ `test_cache_performance` - Melhoria de performance

**Cobertura**: ~95% do CacheService

## 🎯 Estrutura de Testes

```
backend/superadmin/tests/
├── __init__.py
├── test_security_detector.py  # Testes do detector
└── test_cache.py              # Testes do cache
```

## 📝 Criando Novos Testes

### Exemplo: Teste de ViewSet

```python
import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def superadmin_user(db):
    user = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='pass'
    )
    return user

@pytest.mark.django_db
class TestViolacaoViewSet:
    def test_list_violacoes(self, api_client, superadmin_user):
        # Autenticar
        api_client.force_authenticate(user=superadmin_user)
        
        # Fazer requisição
        response = api_client.get('/api/superadmin/violacoes-seguranca/')
        
        # Verificar resposta
        assert response.status_code == 200
        assert 'results' in response.data
```

### Exemplo: Teste de Modelo

```python
import pytest
from superadmin.models import ViolacaoSeguranca

@pytest.mark.django_db
class TestViolacaoSeguranca:
    def test_create_violacao(self):
        violacao = ViolacaoSeguranca.objects.create(
            tipo='brute_force',
            criticidade='alta',
            usuario_email='test@example.com',
            usuario_nome='Test User',
            descricao='Teste',
            detalhes_tecnicos={},
            ip_address='192.168.1.1'
        )
        
        assert violacao.id is not None
        assert violacao.status == 'nova'
        assert violacao.get_criticidade_color() == '#EF4444'
```

## 🔧 Configuração

### pytest.ini

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --disable-warnings
```

### Fixtures Úteis

```python
@pytest.fixture
def setup_data(db):
    """Cria dados de teste"""
    # Criar tipo de loja, plano, loja, usuário
    ...
    return data

@pytest.fixture(autouse=True)
def clear_cache():
    """Limpa cache antes de cada teste"""
    cache.clear()
    yield
    cache.clear()
```

## 📊 Métricas de Qualidade

### Coverage Atual

- **SecurityDetector**: ~90%
- **CacheService**: ~95%
- **Total**: ~85%

### Meta

- **Coverage**: >80%
- **Testes**: >50
- **Tempo de execução**: <30s

## 🎯 Boas Práticas

### 1. Nomenclatura

```python
# ✅ Bom
def test_detect_brute_force():
    ...

# ❌ Ruim
def test1():
    ...
```

### 2. Arrange-Act-Assert

```python
def test_example():
    # Arrange (preparar)
    user = create_user()
    
    # Act (executar)
    result = function(user)
    
    # Assert (verificar)
    assert result == expected
```

### 3. Isolamento

```python
# ✅ Bom - cada teste é independente
@pytest.fixture(autouse=True)
def clear_data():
    cache.clear()
    yield
    cache.clear()

# ❌ Ruim - testes dependem uns dos outros
def test_1():
    global data
    data = create_data()

def test_2():
    assert data is not None  # Depende de test_1
```

### 4. Mocks

```python
from unittest.mock import patch

def test_with_mock():
    with patch('module.function') as mock_func:
        mock_func.return_value = 'mocked'
        result = call_function()
        assert result == 'mocked'
```

## 🐛 Debugging

### Executar com pdb

```bash
pytest superadmin/tests/test_security_detector.py --pdb
```

### Ver output completo

```bash
pytest superadmin/tests/ -v -s
```

### Executar apenas testes que falharam

```bash
pytest --lf
```

## 📈 CI/CD

### GitHub Actions (exemplo)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest superadmin/tests/ --cov=superadmin
```

## 🔍 Troubleshooting

### Erro: "No module named 'pytest'"

```bash
pip install -r requirements-test.txt
```

### Erro: "Database access not allowed"

```python
# Adicionar decorator
@pytest.mark.django_db
def test_function():
    ...
```

### Erro: "Cache not working"

```python
# Limpar cache antes do teste
@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
```

## 📚 Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [Django Testing](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)

## 🎓 Próximos Passos

### Testes a Adicionar

1. **test_views.py** - Testes de ViewSets
2. **test_models.py** - Testes de modelos
3. **test_serializers.py** - Testes de serializers
4. **test_notifications.py** - Testes de notificações
5. **test_commands.py** - Testes de comandos

### Melhorias

1. Aumentar coverage para >90%
2. Adicionar testes de integração
3. Adicionar testes de performance
4. Configurar CI/CD
5. Adicionar testes E2E (frontend)

---

**Versão**: v514  
**Data**: 2026-02-08  
**Autor**: Equipe LWK Sistemas
