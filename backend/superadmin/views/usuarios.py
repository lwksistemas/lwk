import logging

from django.contrib.auth.models import User
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from core.throttling import PasswordResetThrottle

logger = logging.getLogger(__name__)
from ..models import (
    Loja,
    MercadoPagoConfig,
    UsuarioSistema,
)
from ..serializers import UsuarioSistemaSerializer
from .permissions import IsOwnerOrSuperAdmin, IsSuperAdmin


class UsuarioSistemaViewSet(viewsets.ModelViewSet):
    serializer_class = UsuarioSistemaSerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):
        return UsuarioSistema.objects.select_related("user").prefetch_related("lojas_acesso").all()

    def create(self, request, *args, **kwargs):
        """Criar usuário com senha provisória gerada automaticamente"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        senha_provisoria = getattr(serializer.instance, "_senha_provisoria_gerada", None)

        response_data = serializer.data
        response_data["senha_provisoria"] = senha_provisoria
        response_data["message"] = "Usuário criado com sucesso! Senha provisória enviada por email."

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        """Exclusão completa do usuário (UsuarioSistema + User do Django)."""
        usuario_sistema = self.get_object()
        user_django = usuario_sistema.user
        username = user_django.username
        user_id = user_django.id

        lojas_owned = Loja.objects.filter(owner=user_django).exists()
        if lojas_owned:
            return Response(
                {
                    "error": "Não é possível excluir usuário que é proprietário de uma ou mais lojas. Exclua as lojas primeiro ou transfira a propriedade.",
                    "username": username,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from django.db import connection

            with transaction.atomic():
                from superadmin.models import UserSession
                sessoes_count = UserSession.objects.filter(user_id=user_id).count()
                UserSession.objects.filter(user_id=user_id).delete()
                if sessoes_count:
                    logger.info(f"   ✅ {sessoes_count} sessão(ões) removida(s)")

                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL search_path TO public")
                    cursor.execute("DELETE FROM superadmin_historico_acesso_global WHERE user_id = %s", [user_id])
                    cursor.execute("DELETE FROM superadmin_violacoes_seguranca WHERE user_id = %s", [user_id])
                    cursor.execute("DELETE FROM auth_user_groups WHERE user_id = %s", [user_id])
                    cursor.execute("DELETE FROM auth_user_user_permissions WHERE user_id = %s", [user_id])
                    cursor.execute("DELETE FROM superadmin_usuariosistema WHERE user_id = %s", [user_id])
                    cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])

                logger.info(f"✅ Usuário excluído: {username} (ID: {user_id})")

            return Response({
                "message": f'Usuário "{username}" foi completamente removido do sistema',
                "username": username,
                "detalhes": {
                    "user_id": user_id,
                    "sessoes_removidas": sessoes_count,
                    "usuario_sistema_removido": True,
                    "user_django_removido": True,
                },
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Erro ao excluir usuário {username}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Erro ao excluir usuário: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def suporte(self, request):
        """Listar apenas usuários de suporte"""
        suporte = self.get_queryset().filter(tipo="suporte")
        serializer = self.get_serializer(suporte, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def verificar_senha_provisoria(self, request):
        """Verifica se o usuário logado precisa trocar a senha provisória"""
        if not request.user or not request.user.is_authenticated:
            return Response({
                "precisa_trocar_senha": False,
                "mensagem": "Usuário não autenticado",
            })

        try:
            usuario_sistema = UsuarioSistema.objects.get(user=request.user)
            return Response({
                "precisa_trocar_senha": not usuario_sistema.senha_foi_alterada and bool(usuario_sistema.senha_provisoria),
                "usuario_id": usuario_sistema.id,
                "usuario_nome": request.user.username,
                "tipo": usuario_sistema.tipo,
            })
        except UsuarioSistema.DoesNotExist:
            return Response({
                "precisa_trocar_senha": False,
                "mensagem": "Usuário não possui perfil de sistema",
            })

    @action(detail=False, methods=["post"], permission_classes=[IsOwnerOrSuperAdmin])
    def alterar_senha_primeiro_acesso(self, request):
        """Permite ao usuário alterar a senha no primeiro acesso"""
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Autenticação necessária"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            usuario_sistema = UsuarioSistema.objects.get(user=request.user)
        except UsuarioSistema.DoesNotExist:
            return Response(
                {"detail": "Usuário não possui perfil de sistema"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if usuario_sistema.senha_foi_alterada:
            return Response(
                {"detail": "A senha já foi alterada anteriormente"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nova_senha = request.data.get("nova_senha")
        confirmar_senha = request.data.get("confirmar_senha")

        if not nova_senha or not confirmar_senha:
            return Response(
                {"detail": "Nova senha e confirmação são obrigatórias"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if nova_senha != confirmar_senha:
            return Response(
                {"detail": "As senhas não coincidem"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from core.password_validation import password_policy_requirements, validate_password_policy
        ok, msg = validate_password_policy(nova_senha)
        if not ok:
            return Response({
                "detail": msg,
                "requisitos_senha": password_policy_requirements(),
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.set_password(nova_senha)
        user.save()

        usuario_sistema.senha_foi_alterada = True
        usuario_sistema.save()

        return Response({
            "message": "Senha alterada com sucesso!",
            "usuario": user.username,
            "tipo": usuario_sistema.get_tipo_display(),
        })

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[],
        throttle_classes=[PasswordResetThrottle],
    )
    def recuperar_senha(self, request):
        """Recuperar senha de usuário do sistema (público)"""
        email = request.data.get("email")
        tipo = request.data.get("tipo")

        if not email or not tipo:
            return Response(
                {"detail": "Email e tipo são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)

            try:
                usuario_sistema = UsuarioSistema.objects.get(user=user, tipo=tipo)
            except UsuarioSistema.DoesNotExist:
                return Response(
                    {"detail": "Usuário não encontrado ou tipo incorreto"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            from core.password_validation import generate_provisional_password
            nova_senha = generate_provisional_password()

            user.set_password(nova_senha)
            user.save()

            usuario_sistema.senha_provisoria = nova_senha
            usuario_sistema.senha_foi_alterada = False
            usuario_sistema.save()


            from core.email_templates import email_senha_provisoria_html

            from ..services.provisional_password_helpers import sistema_usuario_login_url

            tipo_display = "Super Admin" if tipo == "superadmin" else "Suporte"
            url_login = sistema_usuario_login_url(tipo)

            info_adicional = {
                "Perfil de Acesso": tipo_display,
            }

            html_content, texto_plano = email_senha_provisoria_html(
                nome_destinatario=user.first_name or user.username,
                usuario=user.username,
                senha=nova_senha,
                url_login=url_login,
                titulo_principal="Recuperação de Senha",
                subtitulo="Sua senha foi redefinida com sucesso",
                info_adicional=info_adicional,
                nome_sistema="LWK Sistemas",
            )

            assunto = f"Recuperação de Senha - LWK Sistemas ({tipo_display})"

            from core.email_delivery import create_email_multipart
            email_msg = create_email_multipart(
                assunto,
                texto_plano,
                [email],
                html=html_content,
            )
            email_msg.send(fail_silently=False)

            return Response({
                "message": "Senha provisória enviada para o email cadastrado",
                "email": email,
            })

        except User.DoesNotExist:
            return Response(
                {"detail": "Email não encontrado no sistema"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"detail": f"Erro ao enviar email: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EmailRetryViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar emails com falha de envio"""

    from superadmin.models import EmailRetry
    from superadmin.serializers import EmailRetrySerializer

    serializer_class = EmailRetrySerializer
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):

        from superadmin.models import EmailRetry

        queryset = EmailRetry.objects.select_related("loja").all()

        enviado = self.request.query_params.get("enviado")
        loja_slug = self.request.query_params.get("loja")

        if enviado is not None:
            enviado_bool = enviado.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(enviado=enviado_bool)

        if loja_slug:
            queryset = queryset.filter(loja__slug=loja_slug)

        return queryset.order_by("enviado", "proxima_tentativa", "-created_at")

    @action(detail=False, methods=["get"])
    def pendentes(self, request):
        """Lista apenas emails pendentes"""
        from django.db.models import F

        pendentes = self.get_queryset().filter(
            enviado=False,
            tentativas__lt=F("max_tentativas"),
        )

        serializer = self.get_serializer(pendentes, many=True)
        return Response({
            "count": pendentes.count(),
            "results": serializer.data,
        })

    @action(detail=False, methods=["get"])
    def falhados(self, request):
        """Lista emails que falharam (atingiram max tentativas)"""
        from django.db.models import F

        falhados = self.get_queryset().filter(
            enviado=False,
            tentativas__gte=F("max_tentativas"),
        )

        serializer = self.get_serializer(falhados, many=True)
        return Response({
            "count": falhados.count(),
            "results": serializer.data,
        })

    @action(detail=True, methods=["post"])
    def reprocessar(self, request, pk=None):
        """Força reprocessamento de email falhado"""
        from superadmin.email_service import EmailService

        try:
            email_retry = self.get_object()

            if email_retry.enviado:
                return Response({
                    "success": False,
                    "error": "Email já foi enviado",
                }, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"Reprocessando email {email_retry.id} manualmente (admin: {request.user.username})")

            service = EmailService()
            success = service.reenviar_email(email_retry.id)

            if success:
                logger.info(f"✅ Email {email_retry.id} reenviado com sucesso")
                return Response({
                    "success": True,
                    "message": "Email reenviado com sucesso",
                }, status=status.HTTP_200_OK)
            logger.warning(f"⚠️ Falha ao reenviar email {email_retry.id}")
            return Response({
                "success": False,
                "error": "Falha ao reenviar email. Verifique os logs.",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"Erro ao reprocessar email: {e}")
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def reprocessar_todos_pendentes(self, request):
        """Reprocessa todos os emails pendentes"""
        from django.db.models import F

        from superadmin.email_service import EmailService
        from superadmin.models import EmailRetry

        try:
            pendentes = EmailRetry.objects.filter(
                enviado=False,
                tentativas__lt=F("max_tentativas"),
            )

            total = pendentes.count()
            enviados = 0
            falhados = 0

            logger.info(f"Reprocessando {total} emails pendentes (admin: {request.user.username})")

            service = EmailService()
            for email_retry in pendentes:
                if service.reenviar_email(email_retry.id):
                    enviados += 1
                else:
                    falhados += 1

            logger.info(f"✅ Reprocessamento concluído: {enviados}/{total} enviados, {falhados} falhas")

            return Response({
                "success": True,
                "total": total,
                "enviados": enviados,
                "falhados": falhados,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Erro ao reprocessar emails: {e}")
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Configuração Mercado Pago (boletos)
@api_view(["GET", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def mercadopago_config(request):
    """GET: retorna config (token mascarado). PATCH: atualiza enabled, use_for_boletos e opcionalmente access_token."""
    from ..services.mercadopago_admin_service import MercadoPagoAdminService

    if not request.user.is_superuser:
        return Response({"detail": "Sem permissão."}, status=status.HTTP_403_FORBIDDEN)
    config = MercadoPagoConfig.get_config()
    if request.method == "GET":
        return Response(MercadoPagoAdminService.serialize_config(config))
    MercadoPagoAdminService.apply_patch(config, request.data)
    config.save()
    return Response(MercadoPagoAdminService.serialize_config(config, include_token_mask=False))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def mercadopago_test(request):
    """Testa a conexão com a API do Mercado Pago."""
    from ..services.mercadopago_admin_service import MercadoPagoAdminService

    if not request.user.is_superuser:
        return Response({"detail": "Sem permissão."}, status=status.HTTP_403_FORBIDDEN)
    config = MercadoPagoConfig.get_config()
    result, ok = MercadoPagoAdminService.test_connection(config)
    if ok:
        return Response(result)
    return Response(result, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(["GET", "POST"])
@permission_classes([])
def mercadopago_webhook(request):
    """Webhook do Mercado Pago para notificações de pagamento."""
    from ..services.mercadopago_admin_service import MercadoPagoAdminService

    if request.method == "GET":
        return Response(
            MercadoPagoAdminService.webhook_discovery_payload(request),
            status=status.HTTP_200_OK,
        )

    from core.webhook_security import verify_mercadopago_signature, webhook_auth_failed_response

    if not verify_mercadopago_signature(request):
        return webhook_auth_failed_response()

    try:
        body = MercadoPagoAdminService.parse_webhook_body(request)
        notification_type = body.get("type") or body.get("action")
        data = body.get("data", body) or {}
        payment_id = data.get("id") if isinstance(data, dict) else None
        if not payment_id and isinstance(data, dict) and "id" in data:
            payment_id = data["id"]
        if not notification_type or not payment_id:
            logger.info("Webhook MP ignorado: type=%s, data=%s", notification_type, body)
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)
        if notification_type != "payment":
            return Response({"status": "ignored", "type": notification_type}, status=status.HTTP_200_OK)

        from superadmin.mercadopago_queue_dispatch import (
            enqueue_mercadopago_webhook,
            should_enqueue_mercadopago_webhook,
        )

        payment_id = str(payment_id)
        if should_enqueue_mercadopago_webhook():
            enqueue_mercadopago_webhook(payment_id)
            return Response(
                {"status": "received", "queued": True, "payment_id": payment_id},
                status=status.HTTP_200_OK,
            )

        from ..sync_service import process_mercadopago_webhook_payment

        result = process_mercadopago_webhook_payment(payment_id)
        if result.get("success") and result.get("processed"):
            return Response(
                {"status": "processed", "payment_id": payment_id, "loja_slug": result.get("loja_slug")},
                status=status.HTTP_200_OK,
            )
        return Response({"status": "ok", "processed": result.get("processed", False)}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Erro no webhook Mercado Pago: %s", e)
        return Response({"status": "error"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def sync_mercadopago_loja(request):
    """Sincroniza pagamentos Mercado Pago de uma loja."""
    if not request.user.is_superuser:
        return Response({"detail": "Apenas superadmin."}, status=status.HTTP_403_FORBIDDEN)
    loja_slug = (request.data.get("loja_slug") or "").strip()
    if not loja_slug:
        return Response(
            {"error": 'Envie "loja_slug" no body (ex: {"loja_slug": "minha-loja"}).'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        loja = Loja.objects.get(slug=loja_slug, is_active=True)
    except Loja.DoesNotExist:
        return Response(
            {"error": f'Loja com slug "{loja_slug}" não encontrada.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    try:
        from ..sync_service import sync_loja_payments_mercadopago
        resultado = sync_loja_payments_mercadopago(loja)
        processed = resultado.get("processed", 0)
        total_checked = resultado.get("total_checked", 0)
        return Response({
            "success": True,
            "message": f"Loja {loja_slug}: {processed} pagamento(s) atualizado(s) de {total_checked} verificados.",
            "processed": processed,
            "total_checked": total_checked,
            "loja_slug": loja_slug,
        })
    except Exception as e:
        logger.exception("sync_mercadopago_loja: %s", e)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([])
def recuperar_senha_loja(request):
    """Recuperar senha de loja pelo email e slug"""
    from ..services.loja_password_recovery_service import LojaPasswordRecoveryService

    payload, http_status = LojaPasswordRecoveryService().execute(
        request.data.get("email"),
        request.data.get("slug"),
        request=request,
    )
    return Response(payload, status=http_status)
