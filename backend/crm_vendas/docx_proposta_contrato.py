"""
Geração de DOCX (Word) para Proposta e Contrato do CRM.

Implementação simples (sem conversão HTML->DOCX completa):
- Cabeçalho (título + metadados)
- Dados da Empresa / Cliente
- Tabela de itens (produtos/serviços)
- Conteúdo em texto (HTML strip)
- Assinaturas (informativas)
"""

from io import BytesIO
import re


def _strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(html))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _formatar_valor(valor) -> str:
    if valor is None:
        return "—"
    try:
        v = float(valor)
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _obter_dados_loja(loja_id: int) -> dict:
    try:
        from superadmin.models import Loja

        loja = (
            Loja.objects.using("default")
            .filter(id=loja_id)
            .select_related("owner")
            .first()
        )
        if not loja:
            return {}
        cidade = getattr(loja, "cidade", "") or ""
        uf = getattr(loja, "uf", "") or ""
        cidade_uf = f"{cidade}/{uf}" if (cidade and uf) else (cidade or uf)
        endereco_parts = [
            getattr(loja, "logradouro", "") or "",
            getattr(loja, "numero", "") or "",
            getattr(loja, "complemento", "") or "",
            getattr(loja, "bairro", "") or "",
            cidade_uf,
            f"CEP {loja.cep}" if getattr(loja, "cep", "") else "",
        ]
        endereco = ", ".join(p for p in endereco_parts if p).strip() or None
        owner = getattr(loja, "owner", None)
        admin_nome = None
        admin_email = None
        if owner:
            admin_nome = (
                f"{getattr(owner, 'first_name', '') or ''} {getattr(owner, 'last_name', '') or ''}"
            ).strip() or getattr(owner, "username", "") or None
            admin_email = getattr(owner, "email", None) or None
        return {
            "nome": getattr(loja, "nome", "") or "",
            "endereco": endereco,
            "cpf_cnpj": getattr(loja, "cpf_cnpj", "") or None,
            "admin_nome": admin_nome,
            "admin_email": admin_email,
        }
    except Exception:
        return {}


def _formatar_endereco_lead(lead) -> str:
    if not lead:
        return "—"
    parts = [
        getattr(lead, "logradouro", "") or "",
        getattr(lead, "numero", "") and f"nº {lead.numero}" or "",
        getattr(lead, "complemento", "") or "",
        getattr(lead, "bairro", "") or "",
        (
            f"{lead.cidade}/{lead.uf}"
            if (getattr(lead, "cidade", "") and getattr(lead, "uf", ""))
            else (getattr(lead, "cidade", "") or getattr(lead, "uf", ""))
        ),
        getattr(lead, "cep", "") and f"CEP {lead.cep}" or "",
    ]
    return ", ".join(p for p in parts if p).strip() or "—"


def _formatar_nome_usuario(user) -> str:
    if not user:
        return "—"
    first_name = getattr(user, "first_name", "") or ""
    last_name = getattr(user, "last_name", "") or ""
    full = f"{first_name} {last_name}".strip()
    return full or getattr(user, "nome", "") or getattr(user, "username", "") or "—"


def gerar_docx_proposta(proposta) -> BytesIO:
    from docx import Document

    doc = Document()
    doc.add_heading("PROPOSTA COMERCIAL", level=1)

    numero = getattr(proposta, "numero", None) or str(getattr(proposta, "id", ""))
    doc.add_paragraph(f"Número: {numero}")
    doc.add_paragraph(f"Título: {getattr(proposta, 'titulo', '') or '—'}")
    doc.add_paragraph(f"Valor total: {_formatar_valor(getattr(proposta, 'valor_total', None))}")

    loja_id = getattr(proposta, "loja_id", None)
    if loja_id:
        loja = _obter_dados_loja(loja_id)
        if loja:
            doc.add_heading("Dados da Empresa", level=2)
            doc.add_paragraph(f"Nome: {loja.get('nome') or '—'}")
            if loja.get("endereco"):
                doc.add_paragraph(f"Endereço: {loja.get('endereco')}")
            if loja.get("cpf_cnpj"):
                doc.add_paragraph(f"CPF/CNPJ: {loja.get('cpf_cnpj')}")
            if loja.get("admin_nome"):
                doc.add_paragraph(f"Administrador: {loja.get('admin_nome')}")
            if loja.get("admin_email"):
                doc.add_paragraph(f"Email do administrador: {loja.get('admin_email')}")

    lead = (
        proposta.oportunidade.lead
        if getattr(proposta, "oportunidade", None) and getattr(proposta.oportunidade, "lead", None)
        else None
    )
    if lead:
        doc.add_heading("Dados do Cliente", level=2)
        doc.add_paragraph(f"Nome: {getattr(lead, 'nome', '') or '—'}")
        if getattr(lead, "empresa", ""):
            doc.add_paragraph(f"Empresa: {lead.empresa}")
        if getattr(lead, "cpf_cnpj", ""):
            doc.add_paragraph(f"CPF/CNPJ: {lead.cpf_cnpj}")
        if getattr(lead, "email", ""):
            doc.add_paragraph(f"Email: {lead.email}")
        if getattr(lead, "telefone", ""):
            doc.add_paragraph(f"Telefone: {lead.telefone}")
        doc.add_paragraph(f"Endereço: {_formatar_endereco_lead(lead)}")

    doc.add_heading("Produtos e Serviços da Oportunidade", level=2)
    itens = []
    if getattr(proposta, "oportunidade", None):
        itens = list(getattr(proposta.oportunidade, "itens", []).all())

    if itens:
        table = doc.add_table(rows=1, cols=4)
        hdr = table.rows[0].cells
        hdr[0].text = "Item"
        hdr[1].text = "Qtd"
        hdr[2].text = "Preço Unit."
        hdr[3].text = "Subtotal"
        for item in itens:
            ps = getattr(item, "produto_servico", None)
            tipo_ps = ps.get_tipo_display() if ps and hasattr(ps, "get_tipo_display") else (getattr(ps, "tipo", "") if ps else "")
            nome = f"{tipo_ps}: {ps.nome}" if (ps and tipo_ps) else (getattr(ps, "nome", "—") if ps else "—")
            qtd = str(getattr(item, "quantidade", None) or 1)
            preco = _formatar_valor(getattr(item, "preco_unitario", None))
            subtotal = _formatar_valor(getattr(item, "subtotal", None))
            row = table.add_row().cells
            row[0].text = nome
            row[1].text = qtd
            row[2].text = preco
            row[3].text = subtotal
    else:
        doc.add_paragraph("Nenhum item cadastrado.")

    doc.add_heading("Conteúdo", level=2)
    conteudo = _strip_html(getattr(proposta, "conteudo", "") or "") or "Conteúdo não informado."
    doc.add_paragraph(conteudo)

    doc.add_heading("Assinaturas", level=2)
    vendedor = (
        proposta.oportunidade.vendedor
        if getattr(proposta, "oportunidade", None) and getattr(proposta.oportunidade, "vendedor", None)
        else None
    )
    doc.add_paragraph(f"Vendedor: {_formatar_nome_usuario(vendedor)}")
    doc.add_paragraph(f"Cliente: {getattr(lead, 'nome', '') or '—'}")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def gerar_docx_contrato(contrato) -> BytesIO:
    from docx import Document

    doc = Document()
    doc.add_heading("CONTRATO", level=1)

    numero = getattr(contrato, "numero", None) or str(getattr(contrato, "id", ""))
    doc.add_paragraph(f"Número: {numero}")
    doc.add_paragraph(f"Título: {getattr(contrato, 'titulo', '') or '—'}")
    doc.add_paragraph(f"Valor total: {_formatar_valor(getattr(contrato, 'valor_total', None))}")

    loja_id = getattr(contrato, "loja_id", None)
    if loja_id:
        loja = _obter_dados_loja(loja_id)
        if loja:
            doc.add_heading("Dados da Empresa", level=2)
            doc.add_paragraph(f"Nome: {loja.get('nome') or '—'}")
            if loja.get("endereco"):
                doc.add_paragraph(f"Endereço: {loja.get('endereco')}")
            if loja.get("cpf_cnpj"):
                doc.add_paragraph(f"CPF/CNPJ: {loja.get('cpf_cnpj')}")
            if loja.get("admin_nome"):
                doc.add_paragraph(f"Administrador: {loja.get('admin_nome')}")
            if loja.get("admin_email"):
                doc.add_paragraph(f"Email do administrador: {loja.get('admin_email')}")

    lead = (
        contrato.oportunidade.lead
        if getattr(contrato, "oportunidade", None) and getattr(contrato.oportunidade, "lead", None)
        else None
    )
    if lead:
        doc.add_heading("Dados do Cliente", level=2)
        doc.add_paragraph(f"Nome: {getattr(lead, 'nome', '') or '—'}")
        if getattr(lead, "empresa", ""):
            doc.add_paragraph(f"Empresa: {lead.empresa}")
        if getattr(lead, "cpf_cnpj", ""):
            doc.add_paragraph(f"CPF/CNPJ: {lead.cpf_cnpj}")
        if getattr(lead, "email", ""):
            doc.add_paragraph(f"Email: {lead.email}")
        if getattr(lead, "telefone", ""):
            doc.add_paragraph(f"Telefone: {lead.telefone}")
        doc.add_paragraph(f"Endereço: {_formatar_endereco_lead(lead)}")

    doc.add_heading("Produtos e Serviços da Oportunidade", level=2)
    itens = []
    if getattr(contrato, "oportunidade", None):
        itens = list(getattr(contrato.oportunidade, "itens", []).all())

    if itens:
        table = doc.add_table(rows=1, cols=4)
        hdr = table.rows[0].cells
        hdr[0].text = "Item"
        hdr[1].text = "Qtd"
        hdr[2].text = "Preço Unit."
        hdr[3].text = "Subtotal"
        for item in itens:
            ps = getattr(item, "produto_servico", None)
            tipo_ps = ps.get_tipo_display() if ps and hasattr(ps, "get_tipo_display") else (getattr(ps, "tipo", "") if ps else "")
            nome = f"{tipo_ps}: {ps.nome}" if (ps and tipo_ps) else (getattr(ps, "nome", "—") if ps else "—")
            qtd = str(getattr(item, "quantidade", None) or 1)
            preco = _formatar_valor(getattr(item, "preco_unitario", None))
            subtotal = _formatar_valor(getattr(item, "subtotal", None))
            row = table.add_row().cells
            row[0].text = nome
            row[1].text = qtd
            row[2].text = preco
            row[3].text = subtotal
    else:
        doc.add_paragraph("Nenhum item cadastrado.")

    doc.add_heading("Conteúdo", level=2)
    conteudo = _strip_html(getattr(contrato, "conteudo", "") or "") or "Conteúdo não informado."
    doc.add_paragraph(conteudo)

    doc.add_heading("Assinaturas", level=2)
    vendedor = (
        contrato.oportunidade.vendedor
        if getattr(contrato, "oportunidade", None) and getattr(contrato.oportunidade, "vendedor", None)
        else None
    )
    doc.add_paragraph(f"Vendedor: {_formatar_nome_usuario(vendedor)}")
    doc.add_paragraph(f"Cliente: {getattr(lead, 'nome', '') or '—'}")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

