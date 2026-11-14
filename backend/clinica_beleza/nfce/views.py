"""Configuração e reimpressão do cupom fiscal."""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.encryption import encrypt_value

from ..models import NfceConfig, NfceCupom, VendaBalcao
from ..permissions import CLINICA_ADMIN, CLINICA_ESTOQUE
from ..views_base import resolve_loja_id_from_request
from .chave import digitos, dinheiro
from .emissao import NfceErro, _resumo, emitir_da_venda
from .cupom_html import html_cupom


class NfceConfigView(APIView):
    permission_classes = CLINICA_ADMIN

    def get(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=status.HTTP_400_BAD_REQUEST)
        config, _criada = NfceConfig.objects.get_or_create(loja_id=loja_id)
        return Response(_publico(config))

    def put(self, request):
        loja_id = resolve_loja_id_from_request(request)
        if not loja_id:
            return Response({"detail": "Loja não identificada."}, status=status.HTTP_400_BAD_REQUEST)
        config, _criada = NfceConfig.objects.get_or_create(loja_id=loja_id)
        try:
            _gravar(config, request.data)
        except NfceErro as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_publico(config))


class VendaNfceView(APIView):
    """GET imprime o cupom autorizado. POST tenta emitir de novo."""

    permission_classes = CLINICA_ESTOQUE

    def get(self, request, pk):
        loja_id = resolve_loja_id_from_request(request)
        venda = _venda(loja_id, pk)
        if venda is None:
            return Response({"error": "Venda não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        cupom = NfceCupom.objects.filter(venda=venda, status="autorizada").first()
        if cupom is None:
            return Response(
                {"error": "O cupom ainda não foi autorizado pela SEFAZ."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from superadmin.models import Loja

        loja = Loja.objects.using("default").filter(id=loja_id).first()
        return HttpResponse(html_cupom(cupom, venda, loja), content_type="text/html; charset=utf-8")

    def post(self, request, pk):
        loja_id = resolve_loja_id_from_request(request)
        venda = _venda(loja_id, pk)
        if venda is None:
            return Response({"error": "Venda não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        if venda.status == "cancelada":
            return Response({"error": "A venda está cancelada."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            resultado = emitir_da_venda(venda)
        except NfceErro as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if resultado.get("status") == "desligada":
            return Response(
                {"error": "O cupom fiscal está desligado. Informe o regime e o CSC em Cupom fiscal."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(resultado)


def _venda(loja_id, pk):
    if not loja_id:
        return None
    return VendaBalcao.objects.filter(pk=pk, loja_id=loja_id).first()


def _gravar(config: NfceConfig, data) -> None:
    ligar = data.get("habilitada") is True
    regime = str(data.get("regime") or config.regime or "").strip()
    identificador = digitos(data.get("id_csc") or config.id_csc)[:6]
    csc = str(data.get("csc") or "").strip()
    ie = digitos(data.get("inscricao_estadual") if "inscricao_estadual" in data else config.inscricao_estadual)
    ncm = digitos(data.get("ncm_padrao") if "ncm_padrao" in data else config.ncm_padrao)
    ibge = digitos(data.get("codigo_municipio") if "codigo_municipio" in data else config.codigo_municipio)
    if ligar:
        if regime not in {"simples", "normal"}:
            raise NfceErro("Escolha o regime: Simples Nacional ou regime normal.")
        if not identificador:
            raise NfceErro("Informe o ID do CSC.")
        if not csc and not config.csc:
            raise NfceErro("Informe o CSC.")
        if len(ie) < 2:
            raise NfceErro("Informe a inscrição estadual.")
    if regime and regime not in {"simples", "normal"}:
        raise NfceErro("Escolha o regime: Simples Nacional ou regime normal.")
    if ncm and len(ncm) != 8:
        raise NfceErro("O NCM padrão tem 8 dígitos.")
    if ibge and len(ibge) != 7:
        raise NfceErro("O código IBGE do município tem 7 dígitos.")
    try:
        serie = int(data.get("serie") or config.serie or 1)
    except (TypeError, ValueError) as exc:
        raise NfceErro("A série da NFC-e fica entre 1 e 999.") from exc
    if serie < 1 or serie > 999:
        raise NfceErro("A série da NFC-e fica entre 1 e 999.")
    if regime:
        config.regime = regime
    if identificador:
        config.id_csc = identificador
    if csc:
        config.csc = encrypt_value(csc)
    config.inscricao_estadual = ie
    config.ncm_padrao = ncm
    config.codigo_municipio = ibge
    config.serie = serie
    if "ambiente_homologacao" in data:
        config.ambiente_homologacao = data.get("ambiente_homologacao") is not False
    if regime == "normal" and data.get("aliquota_icms") not in (None, ""):
        config.aliquota_icms = dinheiro(data.get("aliquota_icms"))
    config.habilitada = ligar
    config.save()


def _publico(config: NfceConfig) -> dict:
    from ..models import ClinicaBelezaNFSeConfig

    nfse = ClinicaBelezaNFSeConfig.objects.filter(loja_id=config.loja_id).first()
    certificado = bool(getattr(nfse, "issnet_certificado", None))
    return {
        "habilitada": config.habilitada,
        "regime": config.regime,
        "id_csc": config.id_csc,
        "csc_informado": bool(config.csc),
        "inscricao_estadual": config.inscricao_estadual,
        "serie": config.serie,
        "ambiente_homologacao": config.ambiente_homologacao,
        "ncm_padrao": config.ncm_padrao,
        "codigo_municipio": config.codigo_municipio,
        "aliquota_icms": str(config.aliquota_icms),
        "certificado_a1": certificado,
        "proximo_numero": config.proximo_numero_teste if config.ambiente_homologacao else config.proximo_numero,
    }


def resumo_nfce(venda) -> dict | None:
    from django.core.exceptions import ObjectDoesNotExist

    try:
        cupom = venda.cupom_nfce
    except ObjectDoesNotExist:
        return None
    return _resumo(cupom)
