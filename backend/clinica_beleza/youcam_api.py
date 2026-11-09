"""Cliente da YouCam API. A chave vem da clínica e não fica no log."""
from __future__ import annotations

import io
from typing import Any

import requests
from PIL import Image

BASE = "https://yce-api-01.makeupar.com"
CAMINHOS = {
    "analise": "skin-analysis",
    "pele": "skin-simulation",
    "rosto": "face-reshape",
    "corpo": "body-reshape",
}
PELE = {"wrinkle", "pores", "redness", "spots", "texture"}
ROSTO = {"lip_size", "nose_size", "chin_length", "eye_size"}
CORPO = {"waist", "belly", "hip"}
ANALISE = ["wrinkle", "pore", "texture", "acne"]


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
        return {
            "version": "1.0",
            **origem,
            "features": {parametro: valor},
            "global": {"skin_smooth_strength": 0, "skin_smooth_color_intensity": 0},
        }
    if modo == "corpo":
        if parametro not in CORPO or intensidade == 0:
            raise YouCamError("Escolha a região do corpo e uma intensidade diferente de zero.")
        return {"version": "1.0", **origem, "features": {parametro: int(intensidade)}}
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
