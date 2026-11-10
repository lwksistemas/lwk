"""Reconhecimento de item de NF-e contra o estoque, sem gravar nada."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal

_PARADA = {"DE", "DA", "DO", "DAS", "DOS", "E", "COM", "PARA", "ML", "MG", "UN", "CX", "UND"}


def normalizar_nome(nome: str) -> str:
    texto = unicodedata.normalize("NFKD", nome or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^A-Z0-9 ]", " ", texto.upper())
    return re.sub(r"\s+", " ", texto).strip()


def tokens_nome(nome: str) -> set[str]:
    return {t for t in normalizar_nome(nome).split() if len(t) > 2 and t not in _PARADA}


def gtin_util(valor: str) -> str:
    bruto = (valor or "").strip().upper()
    if bruto in {"", "SEM GTIN"}:
        return ""
    digitos = re.sub(r"\D", "", bruto)
    if len(digitos) not in (8, 12, 13, 14) or set(digitos) <= {"0"}:
        return ""
    return digitos


_CONTEUDO_EMBALAGEM = {
    "AMPOLA": "ampola",
    "AMPOLAS": "ampola",
    "AMP": "ampola",
    "CAPSULA": "cápsula",
    "CAPSULAS": "cápsula",
    "COMPRIMIDO": "comprimido",
    "COMPRIMIDOS": "comprimido",
    "DRAGEA": "drágea",
    "DRAGEAS": "drágea",
    "SACHE": "sachê",
    "SACHES": "sachê",
    "SERINGA": "seringa",
    "SERINGAS": "seringa",
    "FRASCO": "frasco",
    "FRASCOS": "frasco",
    "UNIDADE": "unidade",
    "UNIDADES": "unidade",
    "UND": "unidade",
    "UNDS": "unidade",
    "DOSE": "dose",
    "DOSES": "dose",
}
_EMBALAGEM_RE = re.compile(
    r"(?:\b(?:CX|CAIXA|KIT|PACK|PACOTE|DISPLAY)\b[\s/]*)?(?:\bCOM\b|\bC\b)?\s*(\d{1,4})\s+"
    r"(AMPOLAS?|AMP|CAPSULAS?|COMPRIMIDOS?|DRAGEAS?|SACHES?|SERINGAS?|FRASCOS?|UNIDADES?|UNDS?|DOSES?)\b",
    re.IGNORECASE,
)


def embalagem_na_descricao(nome: str) -> dict | None:
    """Caixa descrita no nome, quando a nota não separa a unidade de estoque.

    "CX COM 10 AMPOLAS 2ML" vale 10 ampolas. "2ML" sozinho não é embalagem.
    """
    texto = normalizar_nome(nome)
    achado = _EMBALAGEM_RE.search(texto)
    if not achado:
        return None
    quantidade = Decimal(achado.group(1))
    if quantidade <= 1 or quantidade > 1000:
        return None
    unidade = _CONTEUDO_EMBALAGEM.get(achado.group(2).upper())
    if not unidade:
        return None
    return {"quantidade": quantidade, "unidade": unidade}


def fator_da_unidade(q_com: Decimal, q_trib: Decimal, u_com: str, u_trib: str) -> Decimal:
    """Unidades de estoque que entram para cada unidade comercial da nota.

    Uma caixa com 5 frascos vem como qCom=1 CX e qTrib=5 UN. A razão vira o fator.
    """
    if q_com <= 0 or q_trib <= 0:
        return Decimal("1")
    if (u_com or "").strip().upper() == (u_trib or "").strip().upper():
        return Decimal("1")
    razao = (q_trib / q_com).quantize(Decimal("0.0001"))
    if razao == razao.to_integral_value() and Decimal("1") < razao <= Decimal("1000"):
        return razao
    return Decimal("1")


def quantidade_estoque(q_com: Decimal, fator: Decimal) -> Decimal:
    if fator <= 0:
        fator = Decimal("1")
    return (q_com * fator).quantize(Decimal("0.01"))


def custo_comercial_efetivo(
    v_un: Decimal,
    q_com: Decimal,
    v_prod: Decimal = Decimal("0"),
    v_desc: Decimal = Decimal("0"),
    v_frete: Decimal = Decimal("0"),
    v_seg: Decimal = Decimal("0"),
    v_outro: Decimal = Decimal("0"),
) -> Decimal:
    """Preço da unidade comercial depois do desconto e das despesas do item."""
    bruto = v_prod if v_prod > 0 else v_un * (q_com if q_com > 0 else Decimal("1"))
    liquido = bruto - v_desc + v_frete + v_seg + v_outro
    if liquido < 0:
        liquido = Decimal("0")
    base = q_com if q_com > 0 else Decimal("1")
    return (liquido / base).quantize(Decimal("0.0001"))


def custo_unitario_estoque(preco_comercial: Decimal, fator: Decimal) -> Decimal:
    if fator <= 0:
        fator = Decimal("1")
    return (preco_comercial / fator).quantize(Decimal("0.01"))


def custo_total_estoque(custo_unitario: Decimal, quantidade: Decimal) -> Decimal:
    return (custo_unitario * quantidade).quantize(Decimal("0.01"))


def serie_da_chave(chave: str) -> str:
    """Série da NF-e, posições 23 a 25 da chave de 44 dígitos."""
    digitos = re.sub(r"\D", "", chave or "")
    if len(digitos) != 44:
        return ""
    return digitos[22:25].lstrip("0") or "0"


def chave_item_identico(item: dict) -> str:
    """Linhas da mesma nota que são o mesmo item. Nome parecido não entra aqui."""
    gtin = gtin_util(item.get("gtin") or "")
    if gtin:
        return f"gtin:{gtin}"
    nome = normalizar_nome(item.get("nome") or "")
    if nome:
        return f"nome:{nome}"
    return ""


def decisao_pendente(acao: str, produto_id) -> bool:
    if acao not in ("vincular", "novo", "ignorar"):
        return True
    return acao == "vincular" and not produto_id


def rastreio_obrigatorio_faltando(exige: bool, acao: str, lote: str, validade) -> bool:
    if not exige or (acao or "") == "ignorar":
        return False
    return not (lote or "").strip() or not validade


def semelhanca(a: str, b: str) -> float:
    ta, tb = tokens_nome(a), tokens_nome(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _produto(produtos: list[dict], produto_id) -> dict | None:
    for produto in produtos:
        if produto["id"] == produto_id:
            return produto
    return None


def classificar_item(item: dict, produtos: list[dict], vinculos: list[dict]) -> dict:
    """Decide vincular, cadastrar ou pedir confirmação.

    Confiança alta vincula sozinha. Dúvida deixa a ação vazia para o usuário escolher.
    """
    doc = re.sub(r"\D", "", item.get("documento") or "")
    codigo = (item.get("codigo") or "").strip()
    gtin = gtin_util(item.get("gtin") or "")
    nome = item.get("nome") or ""
    fator = item.get("fator") if isinstance(item.get("fator"), Decimal) else Decimal(str(item.get("fator") or "1"))
    if fator <= 0:
        fator = Decimal("1")

    def _cand(produto: dict) -> dict:
        return {"id": produto["id"], "nome": produto["nome"], "exige_lote": bool(produto.get("exige_lote"))}

    def resposta(acao: str, confianca: str, produto: dict | None, *, fator_uso=None, alerta: str = "", candidatos=None):
        escolhido = produto
        return {
            "acao": acao,
            "confianca": confianca,
            "produto_id": escolhido["id"] if escolhido else None,
            "produto_nome": escolhido["nome"] if escolhido else "",
            "fator": str(fator_uso if fator_uso is not None else fator),
            "exige_lote": bool(escolhido.get("exige_lote")) if escolhido else False,
            "alerta": alerta,
            "candidatos": candidatos if candidatos is not None else ([_cand(escolhido)] if escolhido else []),
        }

    por_codigo = None
    fator_codigo = None
    if doc and codigo:
        for vinculo in vinculos:
            if vinculo.get("documento") == doc and vinculo.get("codigo") == codigo:
                encontrado = _produto(produtos, vinculo.get("produto_id"))
                if encontrado:
                    por_codigo = encontrado
                    fator_codigo = Decimal(str(vinculo.get("fator") or "1"))
                    break

    por_gtin = None
    if gtin:
        for vinculo in vinculos:
            if gtin_util(vinculo.get("gtin") or "") == gtin:
                encontrado = _produto(produtos, vinculo.get("produto_id"))
                if encontrado:
                    por_gtin = encontrado
                    break

    if por_codigo and por_gtin and por_codigo["id"] != por_gtin["id"]:
        return resposta(
            "",
            "duvida",
            None,
            alerta="O código deste fornecedor e o GTIN apontam para produtos diferentes. Escolha qual vincular.",
            candidatos=[_cand(por_codigo), _cand(por_gtin)],
        )

    if por_codigo:
        return resposta(
            "vincular",
            "alta",
            por_codigo,
            fator_uso=fator_codigo if fator_codigo and fator_codigo > 0 else fator,
            alerta="Código deste fornecedor já vinculado.",
        )

    if por_gtin:
        return resposta("vincular", "alta", por_gtin, alerta="GTIN já vinculado a este produto.")

    exatos = [p for p in produtos if normalizar_nome(p.get("nome") or "") == normalizar_nome(nome) and normalizar_nome(nome)]
    if len(exatos) == 1:
        return resposta("vincular", "alta", exatos[0], alerta="Nome igual a um produto do estoque.")
    if len(exatos) > 1:
        return resposta(
            "",
            "duvida",
            None,
            alerta="Há mais de um produto com este nome. Escolha qual vincular.",
            candidatos=[_cand(p) for p in exatos[:8]],
        )

    parecidos = []
    for produto in produtos:
        nota = semelhanca(nome, produto.get("nome") or "")
        if nota >= 0.5:
            parecidos.append((nota, produto))
    parecidos.sort(key=lambda par: -par[0])
    if parecidos:
        melhor = parecidos[0][1]
        return resposta(
            "",
            "duvida",
            melhor,
            alerta="Produto parecido no estoque. Confirme se é o mesmo antes de cadastrar outro.",
            candidatos=[_cand(p) for _, p in parecidos[:5]],
        )

    return resposta("novo", "nenhuma", None)


def marcar_repetidos(itens: list[dict]) -> None:
    """Itens iguais na mesma nota não viram dois cadastros sem o usuário ver."""
    grupos: dict[str, list[int]] = {}
    for indice, item in enumerate(itens):
        chave = chave_item_identico(item)
        item["grupo"] = chave
        if chave:
            grupos.setdefault(chave, []).append(indice)
    aviso = "Esta nota repete este produto. Se os dois ficarem como novo, entram no mesmo cadastro."
    for indices in grupos.values():
        if len(indices) < 2:
            continue
        for indice in indices:
            item = itens[indice]
            atual = (item.get("alerta") or "").strip()
            item["alerta"] = f"{atual} {aviso}".strip() if atual else aviso
            if item.get("acao") == "novo":
                item["confianca"] = "duvida"
                item["acao"] = ""
