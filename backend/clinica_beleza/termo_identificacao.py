"""Identificação da clínica e do profissional na primeira página do termo."""
from __future__ import annotations

import re

_PARTICULAS = {"de", "da", "do", "das", "dos", "e", "em", "a", "o", "as", "os"}


def _texto(obj, attr: str) -> str:
    if obj is None:
        return ""
    valor = getattr(obj, attr, None)
    return valor.strip() if isinstance(valor, str) else ""


def formatar_cep(cep: str) -> str:
    digitos = re.sub(r"\D", "", cep or "")
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return (cep or "").strip()


def endereco_completo_loja(loja) -> str:
    """Rua, número, complemento, bairro, cidade, UF e CEP cadastrados na loja."""
    if not loja:
        return ""
    rua = ", ".join(
        parte
        for parte in (
            _texto(loja, "logradouro"),
            _texto(loja, "numero"),
            _texto(loja, "complemento"),
        )
        if parte
    )
    cidade = _texto(loja, "cidade")
    uf = _texto(loja, "uf") or _texto(loja, "estado")
    if cidade and uf:
        local = f"{cidade} - {uf}"
    else:
        local = cidade or uf
    partes = [parte for parte in (rua, _texto(loja, "bairro"), local) if parte]
    cep = formatar_cep(_texto(loja, "cep"))
    if cep:
        partes.append(f"CEP {cep}")
    if partes:
        return ", ".join(partes)
    return _texto(loja, "endereco")


def _em_caixa_alta(texto: str) -> bool:
    letras = [letra for letra in texto if letra.isalpha()]
    if not letras:
        return False
    return sum(1 for letra in letras if letra.isupper()) / len(letras) > 0.6


def capitalizar_exibicao(texto: str) -> str:
    """Tira a caixa alta do cadastro e deixa a primeira letra de cada palavra maiúscula."""
    texto = (texto or "").strip()
    if not texto or texto == "—" or not _em_caixa_alta(texto):
        return texto
    titulo = texto.title()
    titulo = re.sub(
        r"(?<=\s)(De|Da|Do|Das|Dos|E|Em|A|O|As|Os)(?=\s)",
        lambda match: match.group(0).lower(),
        titulo,
    )
    titulo = re.sub(r"\bCep\b", "CEP", titulo)
    titulo = re.sub(
        r"(?<= - )([A-Za-z]{2})(?=\s|,|$)",
        lambda match: match.group(1).upper(),
        titulo,
    )
    return titulo


def telefone_loja(loja) -> str:
    bruto = (
        _texto(loja, "telefone_contato")
        or _texto(loja, "owner_telefone")
        or _texto(loja, "telefone")
    )
    if not bruto:
        return ""
    from core.phone_utils import telefone_exibicao_brasileiro

    return telefone_exibicao_brasileiro(bruto) or bruto


def email_loja(loja) -> str:
    return _texto(loja, "email_contato") or _texto(loja, "email")


def cnpj_loja(loja) -> str:
    bruto = _texto(loja, "cpf_cnpj")
    if not bruto:
        return ""
    from core.cpf_utils import normalizar_cpf_cnpj

    return normalizar_cpf_cnpj(bruto) or bruto


def linhas_clinica_termo(loja) -> list[tuple[str, str]]:
    """Nome fantasia, razão social, CNPJ, endereço e telefone da loja."""
    if not loja:
        return []
    razao = _texto(loja, "razao_social") or _texto(loja, "nome")
    fantasia = _texto(loja, "nome_fantasia")
    linhas: list[tuple[str, str]] = []
    fantasia = capitalizar_exibicao(fantasia)
    razao = capitalizar_exibicao(razao)
    if fantasia and fantasia.casefold() != razao.casefold():
        linhas.append(("Nome fantasia", fantasia))
    if razao:
        linhas.append(("Razão social", razao))
    elif fantasia:
        linhas.append(("Nome fantasia", fantasia))
    cnpj = cnpj_loja(loja)
    if cnpj:
        linhas.append(("CNPJ", cnpj))
    endereco = capitalizar_exibicao(endereco_completo_loja(loja))
    if endereco:
        linhas.append(("Endereço", endereco))
    telefone = telefone_loja(loja)
    if telefone:
        linhas.append(("Telefone", telefone))
    return linhas


def linhas_profissional_termo(prof) -> list[tuple[str, str]]:
    """Nome, conselho e registro do profissional responsável pelo procedimento."""
    if prof is None:
        return [("Profissional", "—"), ("Conselho", "—")]
    nome = capitalizar_exibicao(_texto(prof, "nome")) or "—"
    conselho = _texto(prof, "conselho").upper()
    uf = _texto(prof, "conselho_uf").upper()
    registro = _texto(prof, "registro_profissional")
    sigla = f"{conselho}-{uf}" if conselho and uf else conselho
    linhas = [("Profissional", nome)]
    if sigla:
        linhas.append(("Conselho", sigla))
    if registro:
        linhas.append(("Registro", registro))
    if sigla or registro:
        return linhas
    combo = ""
    formatar = getattr(prof, "formatar_conselho", None)
    if callable(formatar):
        resultado = formatar()
        combo = resultado.strip() if isinstance(resultado, str) else ""
    linhas.append(("Conselho", combo or "—"))
    return linhas
