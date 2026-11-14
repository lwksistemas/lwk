"""DANFE da NFC-e para impressão no caixa. Só sai depois da autorização."""
from __future__ import annotations

import base64
import html
import io
from decimal import Decimal

import qrcode


def html_cupom(cupom, venda, loja) -> str:
    imagem = _qr(cupom.qrcode)
    itens = []
    total = Decimal("0.00")
    for item in venda.itens.select_related("produto").all():
        if item.estornado:
            continue
        bruto = (
            Decimal(str(item.quantidade or 0)) * Decimal(str(item.preco_unitario or 0))
            - Decimal(str(item.desconto or 0))
        ).quantize(Decimal("0.01"))
        if bruto < 0:
            bruto = Decimal("0.00")
        total += bruto
        quantidade = f"{item.quantidade:.2f}".rstrip("0").rstrip(".")
        itens.append(
            "<tr>"
            f"<td>{html.escape(item.produto.nome)}</td>"
            f"<td>{html.escape(quantidade)}</td>"
            f"<td>R$ {bruto:.2f}</td>"
            "</tr>"
        )
    chave = cupom.chave
    chave_exibida = " ".join(chave[i:i + 4] for i in range(0, len(chave), 4))
    ambiente = "NFC-e de teste, sem valor fiscal" if cupom.homologacao else "NFC-e"
    nome = html.escape(getattr(loja, "nome", "") or "Clínica")
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Cupom {cupom.numero}</title>
<style>
body {{ font-family: sans-serif; width: 80mm; margin: 0 auto; color: #111; }}
h1 {{ font-size: 14px; text-align: center; margin: 8px 0; }}
p, td {{ font-size: 12px; }}
table {{ width: 100%; border-collapse: collapse; }}
td {{ padding: 2px 0; vertical-align: top; }}
td:last-child {{ text-align: right; white-space: nowrap; }}
.centro {{ text-align: center; }}
img {{ width: 180px; height: 180px; }}
@media print {{ button {{ display: none; }} }}
</style></head><body>
<h1>{nome}</h1>
<p class="centro">{ambiente}<br>Número {cupom.numero} · Série {cupom.serie}</p>
<table>{''.join(itens)}</table>
<p><strong>Total R$ {total:.2f}</strong></p>
<p class="centro"><img alt="QR Code da NFC-e" src="{imagem}"><br>{html.escape(chave_exibida)}<br>Protocolo {html.escape(cupom.protocolo)}</p>
<button onclick="window.print()">Imprimir</button>
<script>window.onload = function () {{ window.print(); }}</script>
</body></html>"""


def _qr(url: str) -> str:
    imagem = qrcode.make(url or "https://www.nfce.fazenda.sp.gov.br/consulta")
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    codigo = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{codigo}"
