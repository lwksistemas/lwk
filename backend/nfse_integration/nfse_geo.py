"""Utilitarios geograficos para emissao de NFS-e."""
import logging
import re
import unicodedata
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

_MUNICIPIOS_IBGE_CACHE: dict[str, list[dict]] = {}


def _normalizar_nome_municipio(nome: str) -> str:
    s = unicodedata.normalize("NFD", (nome or "").upper())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def _formatar_cep(cep_digits: str) -> str:
    d = re.sub(r"\D", "", cep_digits or "")
    if len(d) != 8:
        return cep_digits or ""
    return f"{d[:5]}-{d[5:]}"


def _cep_generico_municipio(cep_digits: str) -> bool:
    """CEP terminado em 000 e tipico de municipio (nao aceito pelo ISSNet com IBGE)."""
    d = re.sub(r"\D", "", cep_digits or "")
    return len(d) == 8 and d.endswith("000")


def normalizar_numero_complemento_endereco(
    numero: str,
    complemento: str = "",
    *,
    max_numero: int = 10,
) -> tuple[str, str]:
    """ISSNet exige numero do endereco com no maximo 10 caracteres (erro E120).
    Separa complemento quando o usuario informa tudo no campo numero (ex.: "1025. SALA 304").
    """
    numero_limpo = (numero or "").strip()
    compl = (complemento or "").strip()
    if not numero_limpo:
        return "S/N", compl
    if len(numero_limpo) <= max_numero:
        return numero_limpo, compl

    match = re.match(r"^(\d+)[.\s,\-/]*(.*)$", numero_limpo)
    if match:
        n, resto = match.group(1), (match.group(2) or "").strip()
        if len(n) <= max_numero:
            if resto:
                compl = f"{resto} {compl}".strip() if compl else resto
            return n, compl

    return numero_limpo[:max_numero], compl


def _viacep_item_to_dict(data: dict) -> dict[str, str]:
    cep_raw = re.sub(r"\D", "", str(data.get("cep") or ""))
    return {
        "cep": _formatar_cep(cep_raw),
        "ibge": str(data.get("ibge") or ""),
        "localidade": (data.get("localidade") or "").strip(),
        "uf": (data.get("uf") or "").strip(),
        "logradouro": (data.get("logradouro") or "").strip(),
        "bairro": (data.get("bairro") or "").strip(),
    }


def consultar_viacep(cep: str) -> dict[str, str]:
    """Consulta ViaCEP e retorna dict com ibge, localidade, uf, logradouro, bairro."""
    cep_digits = re.sub(r"\D", "", cep or "")
    if len(cep_digits) != 8:
        return {}
    try:
        resp = requests.get(f"https://viacep.com.br/ws/{cep_digits}/json/", timeout=5)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if data.get("erro"):
            return {}
        return _viacep_item_to_dict(data)
    except Exception as exc:
        logger.warning("Erro ao consultar ViaCEP %s: %s", cep_digits, exc)
        return {}


def consultar_viacep_por_logradouro(
    uf: str,
    cidade: str,
    logradouro: str,
    bairro: str = "",
) -> dict[str, str]:
    """Busca CEP valido por UF/cidade/logradouro (CEPs genericos xxx00-000 falham no ISSNet)."""
    uf_sigla = (uf or "").strip().upper()
    cidade_nome = (cidade or "").strip()
    logradouro_nome = (logradouro or "").strip()
    if not uf_sigla or not cidade_nome or not logradouro_nome:
        return {}
    try:
        url = (
            f"https://viacep.com.br/ws/{quote(uf_sigla)}/"
            f"{quote(cidade_nome)}/{quote(logradouro_nome)}/json/"
        )
        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        if not isinstance(data, list) or not data:
            return {}
        bairro_norm = _normalizar_nome_municipio(bairro)
        if bairro_norm:
            for item in data:
                parsed = _viacep_item_to_dict(item)
                if _normalizar_nome_municipio(parsed.get("bairro", "")) == bairro_norm:
                    return parsed
        return _viacep_item_to_dict(data[0])
    except Exception as exc:
        logger.warning(
            "Erro ao consultar ViaCEP por logradouro (%s/%s/%s): %s",
            uf_sigla,
            cidade_nome,
            logradouro_nome,
            exc,
        )
        return {}


def consultar_brasilapi_cep(cep: str) -> dict[str, str]:
    """Fallback para CEPs genericos de municipio (ViaCEP retorna erro)."""
    cep_digits = re.sub(r"\D", "", cep or "")
    if len(cep_digits) != 8:
        return {}
    try:
        resp = requests.get(f"https://brasilapi.com.br/api/cep/v1/{cep_digits}", timeout=8)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        return {
            "localidade": (data.get("city") or "").strip(),
            "uf": (data.get("state") or "").strip(),
            "logradouro": (data.get("street") or "").strip(),
            "bairro": (data.get("neighborhood") or "").strip(),
        }
    except Exception as exc:
        logger.warning("Erro ao consultar BrasilAPI CEP %s: %s", cep_digits, exc)
        return {}


def buscar_codigo_ibge_por_cidade_uf(cidade: str, uf: str) -> str:
    """Resolve codigo IBGE pelo nome do municipio e UF (API IBGE)."""
    uf_sigla = (uf or "").strip().upper()
    cidade_norm = _normalizar_nome_municipio(cidade)
    if not uf_sigla or not cidade_norm:
        return ""

    if uf_sigla not in _MUNICIPIOS_IBGE_CACHE:
        try:
            resp = requests.get(
                f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf_sigla}/municipios",
                timeout=12,
            )
            if resp.status_code == 200:
                _MUNICIPIOS_IBGE_CACHE[uf_sigla] = resp.json()
            else:
                _MUNICIPIOS_IBGE_CACHE[uf_sigla] = []
        except Exception as exc:
            logger.warning("Erro ao listar municipios IBGE (%s): %s", uf_sigla, exc)
            _MUNICIPIOS_IBGE_CACHE[uf_sigla] = []

    for municipio in _MUNICIPIOS_IBGE_CACHE.get(uf_sigla, []):
        if _normalizar_nome_municipio(municipio.get("nome", "")) == cidade_norm:
            return str(municipio.get("id") or "")
    return ""


def buscar_codigo_ibge_por_cep(cep: str) -> str:
    """Busca codigo IBGE do municipio pelo CEP (ViaCEP ou BrasilAPI + IBGE)."""
    endereco = {"cep": cep}
    return endereco.get("codigo_municipio", "") if enriquecer_endereco_por_cep(endereco) else ""


def _aplicar_endereco_viacep(endereco: dict[str, str], viacep: dict[str, str]) -> None:
    if viacep.get("cep"):
        endereco["cep"] = viacep["cep"]
    if viacep.get("ibge"):
        endereco["codigo_municipio"] = viacep["ibge"]
    if viacep.get("localidade"):
        endereco["cidade"] = viacep["localidade"]
    if viacep.get("uf"):
        endereco["uf"] = viacep["uf"]
    if viacep.get("logradouro"):
        endereco["logradouro"] = viacep["logradouro"]
    if viacep.get("bairro"):
        endereco["bairro"] = viacep["bairro"]


def _enriquecer_sem_cep_valido(endereco: dict[str, str]) -> bool:
    """Tenta enriquecer endereco quando o CEP é ausente/inválido, buscando por logradouro."""
    logradouro = (endereco.get("logradouro") or "").strip()
    cidade = (endereco.get("cidade") or "").strip()
    uf = (endereco.get("uf") or "").strip()
    if logradouro and cidade and uf:
        por_rua = consultar_viacep_por_logradouro(uf, cidade, logradouro, endereco.get("bairro") or "")
        if por_rua.get("ibge") and por_rua.get("cep"):
            _aplicar_endereco_viacep(endereco, por_rua)
            logger.info("CEP vazio/inválido corrigido via logradouro para %s", endereco.get("cep"))
            return True
    return False


def _tentar_enriquecer_por_logradouro(endereco: dict[str, str], cep_digits: str) -> bool:
    """Busca CEP válido via logradouro para substituir CEP genérico. Retorna True se ok."""
    logradouro = (endereco.get("logradouro") or "").strip()
    if not logradouro:
        return False
    por_rua = consultar_viacep_por_logradouro(
        endereco.get("uf") or "", endereco.get("cidade") or "", logradouro, endereco.get("bairro") or "",
    )
    if por_rua.get("ibge") and por_rua.get("cep"):
        _aplicar_endereco_viacep(endereco, por_rua)
        logger.info("CEP genérico %s substituído por %s via logradouro %r", cep_digits, endereco.get("cep"), logradouro)
        return True
    return False


def _enriquecer_cep_generico(endereco: dict[str, str], cep_digits: str, viacep: dict[str, str]) -> bool:
    """Para CEPs genéricos de município, tenta BrasilAPI + busca por logradouro + IBGE."""
    brasilapi = consultar_brasilapi_cep(cep_digits)
    if brasilapi.get("localidade"):
        endereco["cidade"] = brasilapi["localidade"]
    if brasilapi.get("uf"):
        endereco["uf"] = brasilapi["uf"]
    if not (endereco.get("logradouro") or "").strip() and brasilapi.get("logradouro"):
        endereco["logradouro"] = brasilapi["logradouro"]
    if not (endereco.get("bairro") or "").strip() and brasilapi.get("bairro"):
        endereco["bairro"] = brasilapi["bairro"]

    if _tentar_enriquecer_por_logradouro(endereco, cep_digits):
        return True

    if viacep.get("ibge"):
        _aplicar_endereco_viacep(endereco, viacep)
        return True

    cidade = (endereco.get("cidade") or "").strip()
    uf = (endereco.get("uf") or "").strip()
    ibge = buscar_codigo_ibge_por_cidade_uf(cidade, uf) if cidade and uf else ""
    if ibge:
        endereco["codigo_municipio"] = ibge
        logger.warning("IBGE %s resolvido mas CEP %s permanece genérico — ISSNet pode rejeitar", ibge, cep_digits)
        return True

    logger.warning("Não foi possível resolver endereço para CEP %s (cidade=%r, uf=%r)", cep_digits, cidade, uf)
    return False


def enriquecer_endereco_por_cep(endereco: dict[str, str]) -> bool:
    """Alinha codigo IBGE, cidade, UF e CEP (exigencia ISSNet E058/E061).
    ViaCEP para CEPs de logradouro; busca por rua para CEPs genericos de municipio.
    Retorna True se obteve codigo de municipio e CEP valido para o ISSNet.
    """
    cep_digits = re.sub(r"\D", "", endereco.get("cep") or "")
    if len(cep_digits) != 8:
        return _enriquecer_sem_cep_valido(endereco)

    viacep = consultar_viacep(cep_digits)
    if viacep.get("ibge") and not _cep_generico_municipio(cep_digits):
        _aplicar_endereco_viacep(endereco, viacep)
        return True

    return _enriquecer_cep_generico(endereco, cep_digits, viacep)


def preparar_endereco_tomador_emissao(
    endereco: dict[str, str],
    *,
    email: str = "",
) -> tuple[dict[str, str], str | None]:
    """Alinha CEP, cidade, UF e codigo IBGE do tomador (ISSNet E058/E061).
    Retorna (endereco_pronto, mensagem_erro).
    """
    endereco_final = {k: (v or "") for k, v in (endereco or {}).items()}
    if email:
        endereco_final["email"] = email.strip()
    if enriquecer_endereco_por_cep(endereco_final):
        return endereco_final, None
    cep = endereco_final.get("cep") or "vazio"
    return endereco_final, (
        f"CEP do tomador inválido ou código do município não encontrado ({cep}). "
        "Corrija o CEP, cidade e UF do cliente antes de emitir (erro ISSNet E058)."
    )
