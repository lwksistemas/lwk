"""Lê o comprovante (PDF ou foto) e confere o crédito na conta do Asaas ou da Cora.

A baixa só segue quando o comprovante está no nome e no CPF ou CNPJ do cadastro
e o banco devolve um crédito do mesmo valor que ainda não foi usado.
"""
from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
import unicodedata
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from django.utils import timezone

logger = logging.getLogger(__name__)

_E2E = re.compile(r"E[A-Z0-9]{31}")
_VALOR = re.compile(r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}")
_STOP = {
    "LTDA", "EIRELI", "ME", "EPP", "SA", "CIA", "DE", "DA", "DO", "DOS", "DAS",
    "COMERCIO", "SERVICOS", "SERVICO",
}
_BANCO = {
    "TRANSFERENCIA", "RECEBIDA", "RECEBIDO", "PIX", "CREDITO", "DEBITO",
    "PAGAMENTO", "ENVIADO", "BANCO", "CONTA",
}


def ler_comprovante(dados: bytes) -> dict:
    """Extrai o texto do PDF do banco ou da foto do comprovante."""
    if not dados:
        return {"ok": False, "error": "Envie o comprovante em PDF ou uma foto."}
    if dados.startswith(b"%PDF-"):
        texto = _texto_pdf(dados) or _texto_ocr(_png_da_primeira_pagina_pdf(dados))
    elif _eh_imagem(dados):
        texto = _texto_ocr(dados)
    else:
        return {"ok": False, "error": "Envie o comprovante em PDF ou uma foto JPG ou PNG."}
    texto = (texto or "").strip()
    if not texto:
        return {
            "ok": False,
            "error": "Não foi possível ler o comprovante. Envie o PDF do banco ou uma foto nítida.",
        }
    compacto = re.sub(r"\s+", "", texto).upper()
    e2e = ""
    achado = _E2E.search(compacto)
    if achado:
        e2e = achado.group(0)
    return {"ok": True, "texto": texto, "e2e": e2e}


def _eh_imagem(dados: bytes) -> bool:
    if dados.startswith(b"\xff\xd8\xff") or dados.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    return len(dados) >= 12 and dados.startswith(b"RIFF") and dados[8:12] == b"WEBP"


def _texto_pdf(dados: bytes) -> str:
    try:
        from pypdf import PdfReader

        leitor = PdfReader(BytesIO(dados))
        return "\n".join((pagina.extract_text() or "") for pagina in leitor.pages).strip()
    except Exception:
        logger.info("PDF do comprovante sem texto extraível")
        return ""


def _png_da_primeira_pagina_pdf(dados: bytes) -> bytes:
    try:
        import pypdfium2 as pdfium

        documento = pdfium.PdfDocument(dados)
        if len(documento) == 0:
            return b""
        imagem = documento[0].render(scale=2).to_pil()
        buffer = BytesIO()
        imagem.save(buffer, format="PNG")
        documento.close()
        return buffer.getvalue()
    except Exception:
        logger.info("Não foi possível transformar o PDF do comprovante em imagem")
        return b""


def _texto_ocr(dados: bytes) -> str:
    """Lê a foto. Sem o Tesseract no servidor, a foto não é interpretada."""
    if not dados:
        return ""
    try:
        from PIL import Image

        imagem = Image.open(BytesIO(dados)).convert("RGB")
        buffer = BytesIO()
        imagem.save(buffer, format="PNG")
        png = buffer.getvalue()
    except Exception:
        logger.info("A foto do comprovante não abriu")
        return ""
    arquivo = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        arquivo.write(png)
        arquivo.close()
        for idioma in ("por+eng", "eng"):
            try:
                resultado = subprocess.run(
                    ["tesseract", arquivo.name, "stdout", "-l", idioma, "--psm", "6"],
                    capture_output=True,
                    timeout=25,
                    check=False,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.warning("Tesseract indisponível para ler a foto do comprovante")
                return ""
            texto = resultado.stdout.decode("utf-8", errors="replace").strip()
            if resultado.returncode == 0 and texto:
                return texto
        return ""
    finally:
        try:
            os.remove(arquivo.name)
        except OSError:
            pass


def conferir_cadastro(leitura: dict, nome_loja: str, documento_loja: str, valor) -> dict:
    """O pagador do PDF precisa ser o nome e o documento gravados na loja, no valor da mensalidade."""
    if not leitura.get("ok"):
        return leitura
    texto = leitura.get("texto") or ""
    documento = re.sub(r"\D", "", documento_loja or "")
    if len(documento) not in (11, 14):
        return {"ok": False, "error": "A loja não tem CPF ou CNPJ no cadastro."}
    sem_pontuacao = re.sub(r"[.\-/\s]", "", texto)
    if documento not in sem_pontuacao:
        return {"ok": False, "error": "O comprovante não está no CPF ou CNPJ do cadastro da loja."}
    if not _nome_confere(nome_loja, texto):
        return {"ok": False, "error": "O comprovante não está no nome do cadastro da loja."}
    if not _texto_tem_valor(texto, valor):
        return {"ok": False, "error": "O valor do comprovante não é o da mensalidade."}
    return {"ok": True, "texto": texto, "e2e": leitura.get("e2e") or ""}


def forma_do_comprovante(leitura: dict, forma: str = "") -> str:
    """O código do PIX no comprovante define a busca. Sem ele, procura transferência."""
    forma = (forma or "").strip().lower()
    if forma in ("pix", "transferencia"):
        return forma
    return "pix" if (leitura or {}).get("e2e") else "transferencia"


def localizar_credito(provedor: str, forma: str, leitura: dict, valor, documento_loja: str) -> dict:
    """Consulta o banco e devolve o identificador do crédito, sem dar baixa."""
    from .models import PagamentoLoja

    forma = forma_do_comprovante(leitura, forma)
    if provedor == "cora":
        credito = _credito_cora(forma, leitura, valor, documento_loja)
    else:
        credito = _credito_asaas(forma, leitura, valor)
    if not credito.get("ok"):
        return credito
    identificador = credito["id"]
    if identificador and PagamentoLoja.objects.filter(observacoes__contains=f"credito:{identificador}").exists():
        return {"ok": False, "error": "Este comprovante já baixou outro pagamento."}
    credito["forma"] = forma
    return credito


def anotar_credito(pagamento, identificador: str) -> None:
    if pagamento is None or not identificador:
        return
    linha = f"credito:{identificador}"
    atual = (pagamento.observacoes or "").strip()
    if linha in atual:
        return
    pagamento.observacoes = f"{atual}\n{linha}".strip()
    pagamento.save(update_fields=["observacoes"])


def _credito_asaas(forma: str, leitura: dict, valor) -> dict:
    from asaas_integration.client import AsaasClient
    from asaas_integration.models import AsaasConfig

    api_key = AsaasConfig.resolve_api_key()
    if not api_key:
        return {"ok": False, "error": "Asaas não configurado."}
    client = AsaasClient(api_key=api_key, sandbox=AsaasConfig.effective_sandbox(api_key))
    hoje = timezone.localdate()
    inicio = (hoje - timedelta(days=45)).isoformat()
    try:
        if forma == "pix":
            e2e = leitura.get("e2e") or ""
            if not e2e:
                return {"ok": False, "error": "O comprovante de PIX não tem o identificador da transação."}
            resposta = client.listar_transacoes_pix(type="CREDIT", endToEndIdentifier=e2e, limit=10)
            return _escolher_pix_asaas(resposta.get("data") or [], e2e, valor, leitura["texto"])
        resposta = client.listar_extrato(startDate=inicio, finishDate=hoje.isoformat(), limit=100)
        return _escolher_transferencia_asaas(resposta.get("data") or [], valor, leitura["texto"])
    except Exception:
        logger.exception("Falha ao consultar crédito no Asaas")
        return {"ok": False, "error": "Não foi possível consultar a conta no Asaas. O pagamento não foi baixado."}


def _credito_cora(forma: str, leitura: dict, valor, documento_loja: str) -> dict:
    from .cora_service import cliente_da_config

    hoje = timezone.localdate()
    inicio = (hoje - timedelta(days=45)).isoformat()
    tipo = "PIX" if forma == "pix" else "TRANSFER"
    try:
        client, _config = cliente_da_config()
        entradas = client.consultar_extrato(inicio, hoje.isoformat(), tipo)
    except Exception:
        logger.exception("Falha ao consultar extrato da Cora")
        return {"ok": False, "error": "Não foi possível consultar o extrato da Cora. O pagamento não foi baixado."}
    return _escolher_cora(entradas, leitura, valor, documento_loja)


def _escolher_pix_asaas(transacoes: list, e2e: str, valor, texto: str) -> dict:
    compativeis = []
    for item in transacoes:
        if (item.get("endToEndIdentifier") or "").upper() != e2e:
            continue
        if (item.get("type") or "").upper() != "CREDIT":
            continue
        if (item.get("status") or "").upper() != "DONE":
            continue
        if not _mesmo_valor(item.get("value"), valor):
            continue
        conta = item.get("externalAccount") or {}
        if not _documento_api_compativel(conta.get("cpfCnpj") or "", texto):
            continue
        if conta.get("name") and not _nome_confere(conta.get("name"), texto):
            continue
        compativeis.append(item.get("id") or e2e)
    if len(compativeis) != 1:
        return {"ok": False, "error": "Não localizei esse PIX na conta do Asaas."}
    return {"ok": True, "id": compativeis[0]}


def _escolher_transferencia_asaas(lancamentos: list, valor, texto: str) -> dict:
    tipos = {"TRANSFER", "CREDIT"}
    compativeis = []
    for item in lancamentos:
        if (item.get("type") or "").upper() not in tipos:
            continue
        if not _mesmo_valor(item.get("value"), valor):
            continue
        descricao = item.get("description") or ""
        if not _nome_confere_ou_documento(descricao, texto):
            continue
        if item.get("id"):
            compativeis.append(item["id"])
    if len(compativeis) != 1:
        return {"ok": False, "error": "Não localizei essa transferência na conta do Asaas."}
    return {"ok": True, "id": compativeis[0]}


def _escolher_cora(entradas: list, leitura: dict, valor, documento_loja: str) -> dict:
    documento = re.sub(r"\D", "", documento_loja or "")
    e2e = leitura.get("e2e") or ""
    texto = leitura.get("texto") or ""
    candidatos = []
    for item in entradas:
        if (item.get("type") or "").upper() != "CREDIT":
            continue
        if not _mesmo_valor(Decimal(item.get("amount") or 0) / Decimal(100), valor):
            continue
        transacao = item.get("transaction") or {}
        contraparte = transacao.get("counterParty") or {}
        identidade = re.sub(r"\D", "", contraparte.get("identity") or "")
        if identidade != documento:
            continue
        if contraparte.get("name") and not _nome_confere(contraparte["name"], texto):
            continue
        identificador = item.get("id") or transacao.get("id")
        if not identificador:
            continue
        descricao = re.sub(r"\s+", "", transacao.get("description") or "").upper()
        candidatos.append((identificador, bool(e2e) and e2e in descricao))
    if e2e and any(tem_codigo for _identificador, tem_codigo in candidatos):
        escolhidos = [identificador for identificador, tem_codigo in candidatos if tem_codigo]
    else:
        escolhidos = [identificador for identificador, _tem_codigo in candidatos]
    unicos = list(dict.fromkeys(escolhidos))
    if len(unicos) != 1:
        return {"ok": False, "error": "Não localizei esse pagamento no extrato da Cora."}
    return {"ok": True, "id": unicos[0]}


def _documento_api_compativel(documento_api: str, texto: str) -> bool:
    """A API às vezes devolve o CPF mascarado. Os dígitos visíveis precisam estar no comprovante."""
    if not documento_api or "*" not in documento_api and not re.sub(r"\D", "", documento_api):
        return True
    if "*" in documento_api:
        visiveis = re.sub(r"[^\d]", "", documento_api)
        sem_pontuacao = re.sub(r"[.\-/\s]", "", texto)
        return bool(visiveis) and visiveis in sem_pontuacao
    digitos = re.sub(r"\D", "", documento_api)
    return digitos in re.sub(r"[.\-/\s]", "", texto)


def _nome_confere_ou_documento(descricao: str, texto: str) -> bool:
    """A linha do extrato precisa citar o nome que está no comprovante, ou o documento."""
    palavras = [
        palavra for palavra in _normalizar(descricao).split()
        if len(palavra) >= 4 and palavra not in _STOP and palavra not in _BANCO
    ]
    comprovante = _normalizar(texto)
    if any(palavra in comprovante for palavra in palavras):
        return True
    digitos = re.sub(r"\D", "", descricao)
    return len(digitos) in (11, 14) and digitos in re.sub(r"[.\-/\s]", "", texto)


def _nome_confere(nome: str, texto: str) -> bool:
    palavras = [p for p in _normalizar(nome).split() if len(p) >= 4 and p not in _STOP]
    if not palavras:
        return True
    principal = max(palavras, key=len)
    return principal in _normalizar(texto)


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto or "")
    base = "".join(caractere for caractere in base if not unicodedata.combining(caractere))
    return re.sub(r"[^A-Z0-9 ]", " ", base.upper())


def _texto_tem_valor(texto: str, valor) -> bool:
    esperado = _centavos(valor)
    for achado in _VALOR.finditer(texto or ""):
        bruto = achado.group(0).replace(".", "").replace(",", ".")
        if _centavos(bruto) == esperado:
            return True
    return False


def _mesmo_valor(encontrado, valor) -> bool:
    if encontrado is None:
        return False
    return _centavos(encontrado) == _centavos(valor)


def _centavos(valor) -> int:
    return int((Decimal(str(valor)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
