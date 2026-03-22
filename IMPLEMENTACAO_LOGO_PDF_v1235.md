# Implementação: Logo no Cabeçalho dos PDFs (v1235)

## Data: 22/03/2026

---

## 🎯 OBJETIVO

Adicionar o logo da loja no cabeçalho dos PDFs de propostas e contratos gerados pelo CRM.

---

## ✅ IMPLEMENTAÇÃO

### 1️⃣ Backend - Função para adicionar logo

**Arquivo:** `backend/crm_vendas/pdf_proposta_contrato.py`

**Alterações:**

1. **Imports adicionados:**
```python
from reportlab.platypus import Image
import requests
from PIL import Image as PILImage
```

2. **Função `_obter_dados_loja` atualizada:**
```python
def _obter_dados_loja(loja_id):
    # ... código existente ...
    return {
        'nome': getattr(loja, 'nome', '') or '',
        'endereco': endereco,
        'cpf_cnpj': getattr(loja, 'cpf_cnpj', '') or None,
        'admin_nome': admin_nome,
        'admin_email': admin_email,
        'logo': getattr(loja, 'logo', '') or None,  # ✅ NOVO
    }
```

3. **Nova função `_adicionar_logo_cabecalho`:**
```python
def _adicionar_logo_cabecalho(elements, logo_url, max_width=4*cm, max_height=2*cm):
    """
    Adiciona logo no cabeçalho do PDF.
    
    - Baixa imagem do Cloudinary
    - Mantém proporção (aspect ratio)
    - Centraliza no documento
    - Tamanho máximo: 4cm x 2cm
    """
    if not logo_url:
        return
    
    try:
        # Baixar imagem
        response = requests.get(logo_url, timeout=5)
        if response.status_code != 200:
            return
        
        # Calcular dimensões mantendo proporção
        img_buffer = BytesIO(response.content)
        pil_img = PILImage.open(img_buffer)
        img_width, img_height = pil_img.size
        aspect = img_height / float(img_width)
        
        # Ajustar tamanho
        if img_width > img_height:
            width = min(max_width, img_width)
            height = width * aspect
            if height > max_height:
                height = max_height
                width = height / aspect
        else:
            height = min(max_height, img_height)
            width = height / aspect
            if width > max_width:
                width = max_width
                height = width * aspect
        
        # Criar elemento Image
        img_buffer.seek(0)
        img = Image(img_buffer, width=width, height=height)
        img.hAlign = 'CENTER'
        
        elements.append(img)
        elements.append(Spacer(1, 0.3*cm))
        
    except Exception as e:
        print(f"⚠️ Erro ao adicionar logo no PDF: {e}")
        pass
```

4. **Atualizado `gerar_pdf_proposta`:**
```python
def gerar_pdf_proposta(proposta, incluir_assinaturas=True) -> BytesIO:
    # ... código existente ...
    
    # ✅ NOVO: Adicionar logo no cabeçalho
    loja_id = getattr(proposta, 'loja_id', None)
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data and loja_data.get('logo'):
            _adicionar_logo_cabecalho(elements, loja_data['logo'])
    
    elements.append(Paragraph('PROPOSTA COMERCIAL', title_style))
    # ... resto do código ...
```

5. **Atualizado `gerar_pdf_contrato`:**
```python
def gerar_pdf_contrato(contrato, incluir_assinaturas=True) -> BytesIO:
    # ... código existente ...
    
    # ✅ NOVO: Adicionar logo no cabeçalho
    loja_id = getattr(contrato, 'loja_id', None)
    if loja_id:
        loja_data = _obter_dados_loja(loja_id)
        if loja_data and loja_data.get('logo'):
            _adicionar_logo_cabecalho(elements, loja_data['logo'])
    
    elements.append(Paragraph('CONTRATO', title_style))
    # ... resto do código ...
```

---

## 📍 ONDE O LOGO APARECE

### 1️⃣ Sistema (Dashboard, Menus, etc)
- **Campo:** `logo` (Logo da loja principal)
- **Usado em:** Cabeçalho do sistema, menus, navegação

### 2️⃣ Tela de Login
- **Campo:** `login_logo` (prioridade) ou `logo` (fallback)
- **Usado em:** Círculo colorido no centro da tela de login
- **Fundo:** `login_background` (opcional)

### 3️⃣ PDFs de Propostas e Contratos ✅ NOVO
- **Campo:** `logo` (Logo da loja principal)
- **Posição:** Cabeçalho do PDF (topo, centralizado)
- **Tamanho:** Máximo 4cm x 2cm (mantém proporção)
- **Aparece em:**
  - PDF de Proposta Comercial
  - PDF de Contrato

---

## 🎨 LAYOUT DO PDF

```
┌─────────────────────────────────────────┐
│                                         │
│           [LOGO CENTRALIZADO]           │ ← Logo aqui (4cm x 2cm max)
│                                         │
│                                         │
│      PROPOSTA COMERCIAL / CONTRATO      │
│                                         │
│  Título: Nome da Proposta               │
│                                         │
│  Dados da Empresa                       │
│  Nome: ...                              │
│  Endereço: ...                          │
│  CPF/CNPJ: ...                          │
│                                         │
│  Dados do Cliente                       │
│  Nome: ...                              │
│  Email: ...                             │
│                                         │
│  Produtos e Serviços                    │
│  [Tabela]                               │
│                                         │
│  Valor total: R$ ...                    │
│                                         │
│  Conteúdo                               │
│  [Texto da proposta/contrato]           │
│                                         │
│  Assinaturas                            │
│  [Campos de assinatura]                 │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔄 FLUXO DE FUNCIONAMENTO

1. **Usuário cria proposta/contrato no CRM**
2. **Clica em "Gerar PDF"**
3. **Sistema busca dados da loja** (incluindo logo)
4. **Se logo existe:**
   - Baixa imagem do Cloudinary
   - Calcula dimensões mantendo proporção
   - Adiciona no topo do PDF (centralizado)
5. **Gera resto do PDF** (dados, produtos, assinaturas)
6. **Retorna PDF completo** com logo no cabeçalho

---

## ✅ BENEFÍCIOS

1. **Identidade Visual:** Logo da empresa aparece no PDF
2. **Profissionalismo:** Documentos mais profissionais
3. **Branding:** Reforça marca da empresa
4. **Automático:** Não precisa configurar nada extra
5. **Flexível:** Mantém proporção da imagem
6. **Robusto:** Se falhar ao carregar logo, continua sem ele

---

## 🧪 COMO TESTAR

### Passo 1: Configurar logo
1. Acesse: https://lwksistemas.com.br/loja/[slug]/crm-vendas/configuracoes/login
2. Faça upload do logo em "Logo da loja (principal)"
3. Salve

### Passo 2: Criar proposta
1. Acesse: https://lwksistemas.com.br/loja/[slug]/crm-vendas/propostas
2. Crie uma nova proposta
3. Preencha os dados
4. Clique em "Gerar PDF"

### Passo 3: Verificar PDF
1. Abra o PDF gerado
2. Verifique se o logo aparece no topo (centralizado)
3. Verifique se a proporção está correta
4. Verifique se o tamanho está adequado

---

## 📊 ESPECIFICAÇÕES TÉCNICAS

### Tamanho do Logo no PDF
- **Largura máxima:** 4cm
- **Altura máxima:** 2cm
- **Proporção:** Mantida automaticamente
- **Alinhamento:** Centro

### Formatos Suportados
- JPG
- PNG
- GIF
- WebP

### Timeout
- **Download:** 5 segundos
- **Fallback:** Se falhar, continua sem logo

### Cache
- Não há cache (baixa sempre do Cloudinary)
- Cloudinary já faz cache próprio

---

## 🐛 TRATAMENTO DE ERROS

### Cenários tratados:
1. **Logo não configurado:** PDF gerado sem logo
2. **URL inválida:** PDF gerado sem logo
3. **Timeout no download:** PDF gerado sem logo
4. **Imagem corrompida:** PDF gerado sem logo
5. **Formato inválido:** PDF gerado sem logo

**Princípio:** Nunca falhar a geração do PDF por causa do logo.

---

## 📝 ARQUIVOS MODIFICADOS

1. `backend/crm_vendas/pdf_proposta_contrato.py`
   - Adicionados imports (Image, requests, PILImage)
   - Atualizada função `_obter_dados_loja`
   - Criada função `_adicionar_logo_cabecalho`
   - Atualizada função `gerar_pdf_proposta`
   - Atualizada função `gerar_pdf_contrato`

---

## 🚀 DEPLOY

- **Backend:** Heroku v1232 ✅
- **Versão:** v1235
- **Data:** 22/03/2026

---

## 📚 DOCUMENTAÇÃO RELACIONADA

- `ANALISE_LOGOS_TELA_LOGIN.md` - Análise completa de onde cada logo aparece
- `COMPARACAO_PDF_PROPOSTA_CONTRATO.md` - Comparação entre proposta e contrato

---

## ✅ CONCLUSÃO

O logo da loja agora aparece automaticamente no cabeçalho dos PDFs de propostas e contratos, tornando os documentos mais profissionais e reforçando a identidade visual da empresa.

**Status:** Implementado e deployado ✅
