# Technical Design — Prontuário + Templates (Clínica da Beleza)

## Overview

Sistema de documentos clínicos com templates reutilizáveis, criação durante consulta, prontuário organizado por seções e geração de PDF com timbrado da clínica.

---

## 1. Models (Backend)

### DocumentTemplate
```python
class DocumentTemplate(LojaIsolationMixin, models.Model):
    """Template reutilizável de documento clínico."""
    TIPO_CHOICES = [
        ('receituario', 'Receituário'),
        ('pedido_exame', 'Pedido de Exame'),
        ('atestado', 'Atestado'),
        ('documento_personalizado', 'Documento Personalizado'),
    ]
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='document_templates')
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    conteudo = models.TextField(help_text='Texto com placeholders: {{paciente_nome}}, {{data_atual}}, etc.')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_document_templates'
        ordering = ['-updated_at']
```

### DocumentoClinico
```python
class DocumentoClinico(LojaIsolationMixin, models.Model):
    """Documento clínico gerado durante uma consulta."""
    TIPO_CHOICES = DocumentTemplate.TIPO_CHOICES
    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name='documentos')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documentos_clinicos')
    professional = models.ForeignKey(Professional, on_delete=models.SET_NULL, null=True, related_name='documentos_emitidos')
    template = models.ForeignKey(DocumentTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200, blank=True, default='')
    conteudo = models.TextField(help_text='Conteúdo final renderizado do documento.')
    created_at = models.DateTimeField(auto_now_add=True)
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_documentos_clinicos'
        ordering = ['-created_at']
```

---

## 2. Service Layer

### `documento_service.py`
```python
PLACEHOLDERS = {
    '{{paciente_nome}}': lambda ctx: ctx['patient'].nome,
    '{{paciente_cpf}}': lambda ctx: ctx['patient'].cpf or '',
    '{{paciente_data_nascimento}}': lambda ctx: str(ctx['patient'].data_nascimento or ''),
    '{{profissional_nome}}': lambda ctx: ctx['professional'].nome,
    '{{profissional_registro}}': lambda ctx: ctx['professional'].registro_profissional or '',
    '{{profissional_conselho}}': lambda ctx: ctx['professional'].conselho or '',
    '{{data_atual}}': lambda ctx: ctx['now'].strftime('%d/%m/%Y'),
    '{{consulta_procedimento}}': lambda ctx: ctx['consulta'].procedure.nome if ctx['consulta'].procedure else '',
}

def render_template(template_content: str, context: dict) -> str:
    """Substitui placeholders pelo valor real."""

def criar_documento(*, consulta, professional, tipo, conteudo, template=None, titulo='') -> DocumentoClinico:
    """Cria documento clínico vinculado à consulta. Lança ValueError se consulta não é IN_PROGRESS."""

def listar_prontuario_paciente(patient_id: int, secao: str = None) -> dict:
    """Retorna prontuário do paciente agrupado por seção."""
```

### `prontuario_pdf.py`
```python
def gerar_pdf_documento(documento: DocumentoClinico) -> BytesIO:
    """Gera PDF de um documento com timbrado da clínica (MemedTimbrado)."""

def gerar_pdf_secao(patient_id: int, secao: str) -> BytesIO:
    """Gera PDF com todos os documentos de uma seção do prontuário."""

def gerar_pdf_prontuario_completo(patient_id: int) -> BytesIO:
    """Gera PDF com prontuário completo (todas as seções)."""
```

---

## 3. API Endpoints

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/templates/` | Listar templates do profissional |
| POST | `/templates/` | Criar template |
| GET | `/templates/<id>/` | Detalhe do template |
| PUT | `/templates/<id>/` | Atualizar template |
| DELETE | `/templates/<id>/` | Desativar template |
| GET | `/consultas/<id>/documentos/` | Listar documentos da consulta |
| POST | `/consultas/<id>/documentos/` | Criar documento (manual ou template) |
| DELETE | `/consultas/<id>/documentos/<doc_id>/` | Excluir documento |
| GET | `/patients/<id>/prontuario/` | Prontuário agrupado por seção |
| GET | `/patients/<id>/prontuario/pdf/?secao=receituario` | PDF de uma seção |
| GET | `/patients/<id>/prontuario/pdf/` | PDF completo |
| GET | `/documentos/<id>/pdf/` | PDF de um documento individual |

---

## 4. Frontend — Páginas e Componentes

### Página: `/clinica-beleza/templates/` (gestão de templates)
- Lista de templates do profissional com filtro por tipo
- Botão "Novo Template" → página dedicada `/templates/novo`
- Editor de texto com sugestão de placeholders

### Componente: Criação de documentos na consulta
- Localização: dentro da consulta (status IN_PROGRESS), novo tab ou seção no Atendimento
- Botões: "Receituário", "Exames", "Atestado", "Documento"
- Cada botão abre opções:
  - "Usar Memed" (Receituário/Exames — existente)
  - "Usar Template" → select de templates + preview → confirmar
  - "Digitar Manual" → editor de texto livre → salvar

### Página: `/clinica-beleza/pacientes/<id>/prontuario/`
- Tabs: Receitas | Exames | Atestados | Atendimento | Anamnese | Evolução
- Cada tab mostra lista de documentos daquela seção
- Botão "Imprimir" por documento individual
- Botão "Imprimir Seção" (todos de uma vez)
- Botão "Imprimir Prontuário Completo"

---

## 5. PDF com Timbrado

O sistema suporta **2 modos** de cabeçalho para PDFs, na seguinte prioridade:

### Modo 1: Papel Timbrado (PDF completo)
- Fonte: `MemedTimbrado.pdf` configurado em `/configuracoes/memed`
- Extrai header/footer como imagem de fundo
- Usado quando: `MemedTimbrado` tem PDF salvo para a loja

### Modo 2: Logo + Dados (imagem)
- Fonte: Logo da clínica salva em `/configuracoes/login` (campo `Loja.logo`)
- Gera cabeçalho com: logo centralizada + nome da clínica + endereço
- Usado quando: não tem timbrado PDF, mas tem logo configurada

### Modo 3: Texto simples (fallback)
- Gera cabeçalho com texto: nome da clínica + endereço + CNPJ
- Usado quando: não tem timbrado nem logo

```
Prioridade: MemedTimbrado.pdf > Loja.logo > Texto simples

┌──────────────────────────────┐
│  [Logo ou Timbrado Header]   │
│  Nome da Clínica             │
│  Endereço · CNPJ             │
├──────────────────────────────┤
│                              │
│  CONTEÚDO DO DOCUMENTO       │
│                              │
│  Profissional: Dr. X         │
│  CRM: 123456/SP              │
│  Data: 02/06/2026            │
│                              │
├──────────────────────────────┤
│  [Timbrado Footer ou vazio]  │
└──────────────────────────────┘
```

### Lógica no `prontuario_pdf.py`:
```python
def _resolver_cabecalho(loja_id):
    """Resolve qual cabeçalho usar no PDF."""
    # 1. Timbrado PDF (prioridade máxima)
    timbrado = MemedTimbrado.objects.filter(loja_id=loja_id).first()
    if timbrado and timbrado.pdf:
        return ('timbrado', bytes(timbrado.pdf))
    
    # 2. Logo da clínica
    from superadmin.models import Loja
    loja = Loja.objects.filter(id=loja_id).first()
    if loja and loja.logo:
        return ('logo', loja.logo)  # URL da imagem
    
    # 3. Texto simples
    return ('texto', loja)
```

---

## 6. Placeholders Suportados

| Placeholder | Valor |
|-------------|-------|
| `{{paciente_nome}}` | Nome do paciente |
| `{{paciente_cpf}}` | CPF do paciente |
| `{{paciente_data_nascimento}}` | Data de nascimento |
| `{{profissional_nome}}` | Nome do profissional |
| `{{profissional_registro}}` | Nº registro profissional |
| `{{profissional_conselho}}` | Conselho (CRM, COREN, etc.) |
| `{{data_atual}}` | Data do dia (DD/MM/AAAA) |
| `{{consulta_procedimento}}` | Nome do procedimento da consulta |

---

## 7. Fluxo de Dados

```
Profissional cria template → salva em DocumentTemplate
                                      ↓
Consulta IN_PROGRESS → "Usar Template" → render_template() → DocumentoClinico
                     → "Digitar Manual" → texto livre → DocumentoClinico
                     → "Usar Memed" → (fluxo existente) → PrescricaoMemed
                                      ↓
Consulta COMPLETED → Prontuário Viewer ← agrega DocumentoClinico + PrescricaoMemed + ConsultaEvolucao + PatientAnamnese
                                      ↓
                              PDF com timbrado (MemedTimbrado)
```

---

## 8. Migrations Necessárias

1. `0029_document_template.py` — Cria `DocumentTemplate`
2. `0030_documento_clinico.py` — Cria `DocumentoClinico`
3. SQL em todos os schemas (tabelas novas)
