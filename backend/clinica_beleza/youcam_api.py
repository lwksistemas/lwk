"""Cliente da YouCam API. A chave vem da clínica e não fica no log."""
from __future__ import annotations

import io
from typing import Any

import requests
from PIL import Image, ImageDraw

BASE = "https://yce-api-01.makeupar.com"
CAMINHOS = {
    "analise": "skin-analysis",
    "pele": "skin-simulation",
    "rosto": "face-reshape",
    "corpo": "body-reshape",
}
PELE = {"wrinkle", "pores", "redness", "spots", "texture"}
ROSTO = {"lip_size", "nose_size", "chin_length", "eye_size"}
CORPO = {
    "arm", "belly", "breast", "hip", "hip_lift", "leg", "neck",
    "shoulder", "squared_shoulder", "slim", "taller", "waist",
}
CORPO_LADOS = {
    "breast": ("breast_left", "breast_right"),
    "neck": ("neck_left", "neck_right"),
    "shoulder": ("shoulder_left", "shoulder_right"),
    "squared_shoulder": ("squared_shoulder_left", "squared_shoulder_right"),
}
CORPO_DE_ZERO = {"neck", "taller"}
ANALISE = [
    "wrinkle", "pore", "texture", "acne", "droopy_upper_eyelid", "droopy_lower_eyelid",
    "firmness", "moisture", "eye_bag", "dark_circle_v2", "age_spot", "radiance",
    "redness", "oiliness", "tear_trough", "skin_type",
]


class YouCamError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def preparar_imagem(conteudo: bytes) -> bytes:
    imagem = Image.open(io.BytesIO(conteudo))
    imagem = imagem.convert("RGB")
    largura, altura = imagem.size
    lado = max(largura, altura)
    if lado > 2000:
        escala = 2000 / lado
        imagem = imagem.resize(
            (max(1, int(largura * escala)), max(1, int(altura * escala))),
            Image.Resampling.LANCZOS,
        )
    saida = io.BytesIO()
    imagem.save(saida, format="JPEG", quality=85)
    return saida.getvalue()


def montar_pedido(modo: str, parametro: str, intensidade: float, file_id: str, _file_url: str) -> dict:
    # A YouCam aceita o arquivo enviado ou uma URL, e recusa os dois juntos.
    origem = {"src_file_id": file_id}
    if modo == "analise":
        return {"src_file_id": file_id, "dst_actions": list(ANALISE), "format": "json"}
    if modo == "pele":
        if parametro not in PELE or intensidade <= 0:
            raise YouCamError("Escolha a preocupação da pele e uma intensidade maior que zero.")
        return {**origem, parametro: round(float(intensidade), 2)}
    if modo == "rosto":
        if parametro not in ROSTO or intensidade == 0:
            raise YouCamError("Escolha o traço do rosto e uma intensidade diferente de zero.")
        valor = int(intensidade)
        # Olhos na documentação são um valor por lado. Os dois recebem o mesmo ajuste.
        features = (
            {"eye_size_left": valor, "eye_size_right": valor}
            if parametro == "eye_size"
            else {parametro: valor}
        )
        return {
            "version": "1.0",
            **origem,
            "features": features,
            "global": {"skin_smooth_strength": 0, "skin_smooth_color_intensity": 0},
        }
    if modo == "corpo":
        if parametro not in CORPO or intensidade == 0:
            raise YouCamError("Escolha a região do corpo e uma intensidade diferente de zero.")
        valor = int(intensidade)
        if parametro in CORPO_DE_ZERO and not 0 < valor <= 100:
            raise YouCamError("Nesta região a intensidade vai de 1 a 100.")
        lados = CORPO_LADOS.get(parametro)
        features = {lado: valor for lado in lados} if lados else {parametro: valor}
        return {"version": "1.0", **origem, "features": features}
    raise YouCamError("Modo de simulação desconhecido.")


def interpretar_resposta(payload: dict) -> tuple[str, str, list]:
    dados = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    status = str(dados.get("task_status") or payload.get("task_status") or "").lower()
    url = str(payload.get("url") or dados.get("url") or "")
    resultados = dados.get("results") if isinstance(dados.get("results"), dict) else {}
    if not url:
        url = str(resultados.get("url") or resultados.get("image_url") or "")
    saida = resultados.get("output") if isinstance(resultados.get("output"), list) else []
    if not status and url:
        status = "success"
    if status in {"running", "pending", "processing"}:
        return "processando", "", []
    if status in {"error", "failed"} or payload.get("error"):
        return "erro", "", []
    if status == "success":
        return "success", url, saida
    return "processando", "", []


def endpoint_tarefa(modo: str) -> str:
    return f"/s2s/v2.0/task/{CAMINHOS[modo]}"


def resumo_pedido(pedido: dict) -> dict:
    """Parâmetros enviados, sem o identificador do arquivo."""
    return {chave: valor for chave, valor in pedido.items() if chave not in {"src_file_id", "src_file_url"}}


def unidades_da_resposta(payload: dict) -> int | None:
    dados = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    for chave in ("units", "unit", "consumed_units", "credit", "credits"):
        valor = dados.get(chave, payload.get(chave))
        if isinstance(valor, int) and valor >= 0:
            return valor
    return None


def unidades_tabela(modo: str, pedido: dict | None = None) -> int | None:
    """Tabela publicada da YouCam. A resposta da tarefa não traz o saldo."""
    pedido = pedido or {}
    if modo == "pele":
        preocupacoes = sum(1 for chave in PELE if float(pedido.get(chave) or 0) > 0)
        if preocupacoes <= 0:
            return None
        return 4 if preocupacoes <= 4 else 6
    if modo in {"rosto", "corpo"}:
        return 1
    if modo == "analise":
        # Tabela SD da V2.1, sem relatório avançado. A chamada usa o caminho v2.0.
        quantidade = len(pedido.get("dst_actions") or [])
        if quantidade <= 4:
            return 9
        if quantidade <= 8:
            return 12
        if quantidade <= 12:
            return 14
        return 16
    return None


AVISO_IMAGEM = "Simulação ilustrativa. Não é previsão de dose e não substitui o termo de consentimento."


def carimbar_aviso(conteudo: bytes) -> bytes:
    """Acrescenta o aviso abaixo da foto, para ele seguir em qualquer arquivo salvo."""
    imagem = Image.open(io.BytesIO(conteudo)).convert("RGB")
    faixa = 64
    quadro = Image.new("RGB", (imagem.width, imagem.height + faixa), (20, 20, 20))
    quadro.paste(imagem, (0, 0))
    ImageDraw.Draw(quadro).text((12, imagem.height + 22), AVISO_IMAGEM, fill=(255, 255, 255))
    saida = io.BytesIO()
    quadro.save(saida, format="JPEG", quality=90)
    return saida.getvalue()


def mensagem_erro(payload: dict) -> str:
    dados = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    codigo = str(payload.get("error_code") or dados.get("error_code") or dados.get("error") or "")
    textos = {
        "CreditInsufficiency": "A conta YouCam desta clínica está sem unidades.",
        "InvalidParameters": "A YouCam não aceitou os parâmetros desta foto.",
        "error_src_face_out_of_bound": (
            "A YouCam precisa do rosto inteiro dentro da foto, sem cortar a testa, o queixo ou as laterais."
        ),
        "error_below_min_image_size": "A foto é pequena demais para a YouCam.",
    }
    if codigo in textos:
        return textos[codigo]
    texto = str(dados.get("error_message") or payload.get("error") or "").strip()
    if texto and " " in texto and not texto.startswith("error_"):
        return "A YouCam não aceitou esta foto."
    return "A YouCam não concluiu esta geração."


class YouCamClient:
    def __init__(self, api_key: str, sessao: requests.Session | None = None):
        self.api_key = api_key
        self.sessao = sessao or requests.Session()

    def _cabecalho(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _json(self, resposta: requests.Response) -> dict[str, Any]:
        try:
            corpo = resposta.json()
        except ValueError as exc:
            raise YouCamError("A YouCam respondeu de um jeito inesperado.") from exc
        if resposta.status_code == 401:
            raise YouCamError("A chave YouCam desta clínica foi recusada.")
        if resposta.status_code >= 400:
            raise YouCamError(mensagem_erro(corpo if isinstance(corpo, dict) else {}))
        return corpo if isinstance(corpo, dict) else {}

    def enviar_arquivo(self, conteudo: bytes) -> str:
        meta = self._json(self.sessao.post(
            f"{BASE}/s2s/v2.0/file",
            json={"files": [{
                "content_type": "image/jpeg",
                "file_name": "consulta.jpg",
                "file_size": len(conteudo),
            }]},
            headers={**self._cabecalho(), "Content-Type": "application/json"},
            timeout=25,
        ))
        arquivo = ((meta.get("data") or {}).get("files") or [{}])[0]
        pedido = (arquivo.get("requests") or [{}])[0]
        destino = pedido.get("url")
        file_id = arquivo.get("file_id")
        if not destino or not file_id:
            raise YouCamError("A YouCam não abriu o envio da foto.")
        envio = self.sessao.put(
            destino,
            data=conteudo,
            headers=pedido.get("headers") or {"Content-Type": "image/jpeg"},
            timeout=40,
        )
        if envio.status_code >= 400:
            raise YouCamError("A foto não chegou na YouCam.")
        return str(file_id)

    def criar_tarefa(self, modo: str, pedido: dict) -> str:
        caminho = CAMINHOS[modo]
        corpo = self._json(self.sessao.post(
            f"{BASE}/s2s/v2.0/task/{caminho}",
            json=pedido,
            headers={**self._cabecalho(), "Content-Type": "application/json"},
            timeout=25,
        ))
        task_id = str((corpo.get("data") or {}).get("task_id") or "")
        if not task_id:
            raise YouCamError("A YouCam não devolveu a tarefa.")
        return task_id

    def consultar(self, modo: str, task_id: str) -> dict:
        caminho = CAMINHOS[modo]
        return self._json(self.sessao.get(
            f"{BASE}/s2s/v2.0/task/{caminho}/{task_id}",
            headers=self._cabecalho(),
            timeout=20,
        ))

    def apagar(self, task_id: str) -> None:
        if not task_id:
            return
        try:
            self.sessao.post(
                f"{BASE}/s2s/v2.0/task/delete",
                json={"task_id": task_id},
                headers={**self._cabecalho(), "Content-Type": "application/json"},
                timeout=15,
            )
        except requests.RequestException:
            return
