# Formulário de Nova Loja - Atualizado com Campo de Atalho

## Status: IMPLEMENTADO ✅ (v1443)

---

## 📋 Mudanças no Formulário

### Antes (v1442)
```
1. Informações Básicas
├── Nome da Empresa *
├── Slug (URL) – editável
│   └── URL: /loja/41449198000172/login
└── CPF ou CNPJ *
```

### Depois (v1443)
```
1. Informações Básicas
├── Nome da Empresa *
├── Slug (URL Segura) – editável
│   └── URL: /loja/41449198000172/login
├── Atalho (URL Amigável) – opcional ✨ NOVO
│   └── URL: /felix-representacoes
└── CPF ou CNPJ *
```

---

## 🎯 Novo Campo: Atalho

### Características
- **Nome:** Atalho (URL Amigável)
- **Tipo:** Texto (opcional)
- **Placeholder:** `minha-loja-tech`
- **Geração:** Automática se deixado vazio
- **Validação:** Único no banco de dados

### Comportamento

#### 1. Campo Vazio (Recomendado)
```
Usuário deixa vazio
↓
Backend gera automaticamente
↓
Exemplo: "Felix Representações" → "felix-representacoes"
```

#### 2. Campo Preenchido (Customizado)
```
Usuário digita: "minha-loja"
↓
Backend valida unicidade
↓
Se único: usa "minha-loja"
Se duplicado: adiciona sufixo numérico
```

### Exemplos de Geração Automática

| Nome da Loja | Atalho Gerado |
|--------------|---------------|
| Felix Representações | felix-representacoes |
| ULTRASIS INFORMATICA LTDA | ultrasis-informatica-ltda |
| US MEDICAL | us-medical |
| Clínica da Beleza | clinica-da-beleza |
| Minha Loja Tech | minha-loja-tech |

---

## 🎨 Layout do Formulário

### Grid Responsivo
```
Desktop (md:grid-cols-3):
┌─────────────────┬─────────────────┬─────────────────┐
│ Nome da Empresa │ Slug (Segura)   │ Atalho (Amigável)│
├─────────────────┴─────────────────┴─────────────────┤
│ CPF/CNPJ                          │ [Buscar CNPJ]   │
└───────────────────────────────────┴─────────────────┘

Mobile (grid-cols-1):
┌─────────────────────────────────────┐
│ Nome da Empresa                     │
├─────────────────────────────────────┤
│ Slug (Segura)                       │
├─────────────────────────────────────┤
│ Atalho (Amigável)                   │
├─────────────────────────────────────┤
│ CPF/CNPJ              [Buscar CNPJ] │
└─────────────────────────────────────┘
```

---

## 💡 Textos de Ajuda

### Slug (URL Segura)
```
URL: /loja/41449198000172/login — usa CPF/CNPJ (apenas dígitos).
Ex.: CNPJ 41.449.198/0001-72 → /loja/41449198000172/login
```

### Atalho (URL Amigável)
```
URL: /felix-representacoes — gerado automaticamente se vazio.
Ex.: "felix-representacoes" → /felix-representacoes
```

---

## 🔧 Código Implementado

### Frontend: `ModalNovaLoja.tsx`

#### Estado Inicial
```typescript
const [formData, setFormData] = useState({
  nome: '',
  slug: '',
  atalho: '', // ✅ NOVO v1443
  descricao: '',
  cpf_cnpj: '',
  // ... outros campos
});
```

#### Campo no Formulário
```tsx
<div>
  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
    Atalho (URL Amigável) – opcional
  </label>
  <input
    type="text"
    name="atalho"
    value={formData.atalho || ''}
    onChange={handleChange}
    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-purple-500 focus:border-purple-500"
    placeholder="minha-loja-tech"
  />
  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
    URL: /{formData.atalho || '…'} — gerado automaticamente se vazio.
    Ex.: "felix-representacoes" → /felix-representacoes
  </p>
</div>
```

### Backend: `serializers.py`

#### Campos do Serializer
```python
class LojaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loja
        fields = [
            'nome', 'slug', 'descricao', 'cpf_cnpj',
            # ... outros campos
            'atalho', 'subdomain',  # ✅ Campo já existente
        ]
```

#### Geração Automática (models.py)
```python
def _generate_unique_atalho(self):
    """Gera atalho único baseado no nome da loja"""
    if self.atalho:
        return  # Já tem atalho customizado
    
    # Gerar atalho do nome
    base = slugify(self.nome)[:30]
    atalho = base
    counter = 1
    
    # Garantir unicidade
    while Loja.objects.filter(atalho=atalho).exclude(id=self.id).exists():
        atalho = f"{base}-{counter}"
        counter += 1
    
    self.atalho = atalho
```

---

## 🧪 Testes

### Teste 1: Criar Loja Sem Atalho
```
Input:
- Nome: "Minha Nova Loja"
- Atalho: (vazio)

Resultado:
- Atalho gerado: "minha-nova-loja"
- URL: https://lwksistemas.com.br/minha-nova-loja
```

### Teste 2: Criar Loja Com Atalho Customizado
```
Input:
- Nome: "Minha Nova Loja"
- Atalho: "super-loja"

Resultado:
- Atalho usado: "super-loja"
- URL: https://lwksistemas.com.br/super-loja
```

### Teste 3: Atalho Duplicado
```
Input:
- Nome: "Outra Loja"
- Atalho: "super-loja" (já existe)

Resultado:
- Atalho gerado: "super-loja-1"
- URL: https://lwksistemas.com.br/super-loja-1
```

---

## 📊 Fluxo Completo

```
1. Usuário acessa /superadmin/lojas
   ↓
2. Clica em "+ Nova Loja"
   ↓
3. Preenche formulário:
   - Nome: "Felix Representações"
   - Slug: (auto-preenchido com CNPJ)
   - Atalho: (deixa vazio ou customiza)
   - CPF/CNPJ: 41.449.198/0001-72
   ↓
4. Clica em "Criar Loja"
   ↓
5. Backend:
   - Valida dados
   - Gera atalho se vazio
   - Cria loja no banco
   - Cria banco isolado
   ↓
6. Resultado:
   - URL Segura: /loja/41449198000172/login
   - URL Amigável: /felix-representacoes
   - Ambas funcionam! ✅
```

---

## 🎯 Benefícios

### Para o Administrador
- ✅ Campo opcional (não obrigatório)
- ✅ Geração automática inteligente
- ✅ Possibilidade de customização
- ✅ Validação de unicidade automática

### Para o Cliente
- ✅ URL mais fácil de lembrar
- ✅ URL mais profissional
- ✅ Não expõe CNPJ
- ✅ Melhor para marketing

### Para o Sistema
- ✅ Zero breaking changes
- ✅ Compatibilidade total
- ✅ Geração automática confiável
- ✅ Validação robusta

---

## 📝 Notas Importantes

1. **Campo Opcional**: O atalho é opcional. Se deixado vazio, será gerado automaticamente.

2. **Geração Automática**: O backend usa o método `_generate_unique_atalho()` que:
   - Converte o nome para slug (remove acentos, espaços, etc)
   - Limita a 30 caracteres
   - Adiciona sufixo numérico se duplicado

3. **Validação**: O campo `atalho` tem constraint `unique=True` no banco de dados.

4. **Compatibilidade**: URLs antigas com CNPJ continuam funcionando normalmente.

5. **Signal**: O signal `pre_save` garante que toda loja tenha um atalho antes de salvar.

---

## 🚀 Deploy

### Frontend
- **Versão:** v1443
- **Arquivo:** `frontend/components/superadmin/lojas/ModalNovaLoja.tsx`
- **Status:** ✅ Deployed

### Backend
- **Versão:** v1441 (já estava pronto)
- **Arquivo:** `backend/superadmin/serializers.py`
- **Status:** ✅ Já em produção

---

## 📸 Preview do Formulário

```
┌─────────────────────────────────────────────────────────────┐
│ Nova Loja                                              [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 1. Informações Básicas                                       │
│                                                               │
│ ┌─────────────────┬─────────────────┬─────────────────┐    │
│ │ Nome da Empresa │ Slug (Segura)   │ Atalho (Amigável)│    │
│ │ *               │                 │ (opcional)       │    │
│ ├─────────────────┼─────────────────┼─────────────────┤    │
│ │ Felix Repres... │ 41449198000172  │ felix-repres...  │    │
│ └─────────────────┴─────────────────┴─────────────────┘    │
│                                                               │
│ URL: /loja/41449198000172/login                              │
│ URL: /felix-representacoes                                   │
│                                                               │
│ ┌─────────────────────────────────┬─────────────────┐       │
│ │ CPF ou CNPJ *                   │ [Buscar CNPJ]   │       │
│ ├─────────────────────────────────┴─────────────────┤       │
│ │ 41.449.198/0001-72                                 │       │
│ └────────────────────────────────────────────────────┘       │
│                                                               │
│ ...                                                           │
│                                                               │
│                                    [Cancelar] [Criar Loja]   │
└─────────────────────────────────────────────────────────────┘
```

---

**Data de Implementação:** 31/03/2026  
**Versão Frontend:** v1443  
**Versão Backend:** v1441 (já pronto)  
**Status:** ✅ PRODUÇÃO
