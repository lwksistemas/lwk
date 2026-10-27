"""Login por rosto: o aparelho confirma o Face ID e o servidor só guarda a chave pública."""

from __future__ import annotations

import json
import logging
from urllib.parse import urlparse

from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils import timezone
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url, options_to_json
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from core.login_lockout import check_account_locked, record_login_failure
from superadmin.models import CredencialRosto
from superadmin.services.login_service import LoginService, resolver_username_para_login

logger = logging.getLogger(__name__)

_DESAFIO_TTL = 120
_MAX_POR_ESCOPO = 5
_MSG_SEM_ROSTO = "Não há desbloqueio facial ativado para este usuário neste aparelho. Entre com a senha uma vez."


class RostoErro(Exception):
    def __init__(self, mensagem: str, status: int = 400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def origem_confiavel(request) -> tuple[str, str]:
    """O rosto só vale no site da LWK. O domínio é o da página, não o da API."""
    origem = (request.headers.get("Origin") or "").strip()
    parsed = urlparse(origem)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("https", "http") or parsed.path not in ("", "/") or not host:
        raise RostoErro("Origem do login não aceita.", 400)
    permitido = host in {"localhost", "127.0.0.1"} or host == "lwksistemas.com.br" or host.endswith(".lwksistemas.com.br")
    if not permitido:
        raise RostoErro("Origem do login não aceita.", 400)
    if parsed.scheme != "https" and host not in {"localhost", "127.0.0.1"}:
        raise RostoErro("Origem do login não aceita.", 400)
    return host, f"{parsed.scheme}://{parsed.netloc}"


def _escopo(user_type: str, loja_slug: str | None) -> str:
    if user_type == "loja":
        slug = (loja_slug or "").strip()
        if not slug or len(slug) > 64:
            raise RostoErro("Loja obrigatória.", 400)
        return f"loja:{slug}"
    if user_type not in ("superadmin", "suporte"):
        raise RostoErro("Tipo de acesso inválido.", 400)
    return user_type


def _usuario(username: str, user_type: str, loja_slug: str | None) -> User:
    bruto = (username or "").strip()
    if not bruto:
        raise RostoErro("Digite o usuário para usar o desbloqueio facial.", 400)
    if user_type == "loja":
        bruto = resolver_username_para_login(bruto, loja_slug)
    user = User.objects.filter(username__iexact=bruto).first()
    if not user or not user.is_active:
        raise RostoErro(_MSG_SEM_ROSTO, 400)
    return user


def _exigir_escopo_do_usuario(user, user_type: str, loja_slug: str | None) -> str:
    from core.store_membership import user_belongs_to_store

    escopo = _escopo(user_type, loja_slug)
    servico = LoginService()
    real = servico._get_user_type(user, loja_slug)
    if user_type == "loja":
        if real not in ("loja", "unknown") or not user_belongs_to_store(user, loja_slug):
            raise RostoErro("Este usuário não pode ativar o desbloqueio facial nesta loja.", 403)
        return escopo
    if real != user_type:
        raise RostoErro("Este usuário não pode ativar o desbloqueio facial neste acesso.", 403)
    return escopo


def _guardar_desafio(challenge: bytes, acao: str, user_id: int, escopo: str) -> None:
    cache.set(
        f"rosto:{bytes_to_base64url(challenge)}",
        {"acao": acao, "user_id": user_id, "escopo": escopo},
        timeout=_DESAFIO_TTL,
    )


def _consumir_desafio(challenge: bytes, acao: str, user_id: int, escopo: str) -> None:
    chave = f"rosto:{bytes_to_base64url(challenge)}"
    dados = cache.get(chave)
    cache.delete(chave)
    if not dados or dados.get("acao") != acao or dados.get("user_id") != user_id or dados.get("escopo") != escopo:
        raise RostoErro("A confirmação do desbloqueio facial expirou. Tente de novo.", 400)


def _desafio_da_credencial(credential: dict) -> bytes:
    try:
        bruto = (credential or {}).get("response", {}).get("clientDataJSON")
        dados = json.loads(base64url_to_bytes(bruto))
        return base64url_to_bytes(dados["challenge"])
    except Exception as exc:
        raise RostoErro("Confirmação do desbloqueio facial inválida.", 400) from exc


def _travado(user: User) -> None:
    locked_until = check_account_locked(user.username)
    if not locked_until:
        return
    raise RostoErro("Muitas tentativas de login. Aguarde alguns minutos ou contate o suporte.", 403)


def opcoes_registro(request, user, user_type: str, loja_slug: str | None) -> dict:
    rp_id, _origem = origem_confiavel(request)
    escopo = _exigir_escopo_do_usuario(user, user_type, loja_slug)
    existentes = list(CredencialRosto.objects.filter(user=user, escopo=escopo).order_by("-created_at"))
    opcoes = generate_registration_options(
        rp_id=rp_id,
        rp_name="LWK Sistemas",
        user_name=user.username,
        user_id=str(user.pk).encode(),
        user_display_name=user.get_full_name() or user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(item.credential_id))
            for item in existentes
        ],
    )
    _guardar_desafio(opcoes.challenge, "registro", user.pk, escopo)
    return json.loads(options_to_json(opcoes))


def confirmar_registro(request, user, user_type: str, loja_slug: str | None, credential: dict) -> None:
    rp_id, origem = origem_confiavel(request)
    escopo = _exigir_escopo_do_usuario(user, user_type, loja_slug)
    desafio = _desafio_da_credencial(credential)
    _consumir_desafio(desafio, "registro", user.pk, escopo)
    try:
        verificado = verify_registration_response(
            credential=credential,
            expected_challenge=desafio,
            expected_rp_id=rp_id,
            expected_origin=origem,
            require_user_verification=True,
        )
    except Exception as exc:
        logger.info("rosto.registro_recusado user_id=%s", user.pk)
        raise RostoErro("Não foi possível ativar o desbloqueio facial neste aparelho.", 400) from exc

    cred_id = bytes_to_base64url(verificado.credential_id)
    chave = bytes_to_base64url(verificado.credential_public_key)
    outro = CredencialRosto.objects.filter(credential_id=cred_id).exclude(user=user).first()
    if outro:
        raise RostoErro("Não foi possível ativar o desbloqueio facial neste aparelho.", 400)
    CredencialRosto.objects.update_or_create(
        credential_id=cred_id,
        defaults={"user": user, "escopo": escopo, "public_key": chave, "sign_count": verificado.sign_count or 0},
    )
    sobrando = CredencialRosto.objects.filter(user=user, escopo=escopo).order_by("-created_at")[_MAX_POR_ESCOPO:]
    if sobrando:
        CredencialRosto.objects.filter(pk__in=[item.pk for item in sobrando]).delete()


def opcoes_entrada(request, username: str, user_type: str, loja_slug: str | None) -> dict:
    rp_id, _origem = origem_confiavel(request)
    user = _usuario(username, user_type, loja_slug)
    _travado(user)
    escopo = _exigir_escopo_do_usuario(user, user_type, loja_slug)
    credenciais = list(CredencialRosto.objects.filter(user=user, escopo=escopo))
    if not credenciais:
        raise RostoErro(_MSG_SEM_ROSTO, 400)
    opcoes = generate_authentication_options(
        rp_id=rp_id,
        user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(item.credential_id))
            for item in credenciais
        ],
    )
    _guardar_desafio(opcoes.challenge, "entrada", user.pk, escopo)
    return json.loads(options_to_json(opcoes))


def confirmar_entrada(request, username: str, user_type: str, loja_slug: str | None, credential: dict):
    rp_id, origem = origem_confiavel(request)
    user = _usuario(username, user_type, loja_slug)
    _travado(user)
    escopo = _exigir_escopo_do_usuario(user, user_type, loja_slug)
    desafio = _desafio_da_credencial(credential)
    _consumir_desafio(desafio, "entrada", user.pk, escopo)
    cred_id = (credential or {}).get("id") or ""
    registro = CredencialRosto.objects.filter(user=user, escopo=escopo, credential_id=cred_id).first()
    if not registro and credential.get("rawId"):
        registro = CredencialRosto.objects.filter(
            user=user, escopo=escopo, credential_id=credential.get("rawId"),
        ).first()
    if not registro:
        record_login_failure(user.username)
        raise RostoErro(_MSG_SEM_ROSTO, 400)
    try:
        verificado = verify_authentication_response(
            credential=credential,
            expected_challenge=desafio,
            expected_rp_id=rp_id,
            expected_origin=origem,
            credential_public_key=base64url_to_bytes(registro.public_key),
            credential_current_sign_count=registro.sign_count,
            require_user_verification=True,
        )
    except Exception as exc:
        record_login_failure(user.username)
        logger.info("rosto.entrada_recusada user_id=%s", user.pk)
        raise RostoErro("O desbloqueio facial não foi confirmado. Tente de novo ou entre com a senha.", 401) from exc

    registro.sign_count = verificado.new_sign_count or 0
    registro.last_used_at = timezone.now()
    registro.save(update_fields=["sign_count", "last_used_at"])
    logger.info("rosto.ok user_id=%s", user.pk)
    return LoginService().emitir_sessao(request, user, user_type, loja_slug, user.username)
