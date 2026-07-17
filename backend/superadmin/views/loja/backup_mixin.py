import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..permissions import IsOwnerOrSuperAdmin, IsSuperAdmin

logger = logging.getLogger(__name__)

class LojaBackupMixin:
    """Actions de backup para LojaViewSet."""

    BACKUP_MAX_UPLOAD_BYTES = 500 * 1024 * 1024

    def _resolver_incluir_imagens(self, loja, request) -> bool:
        """Usa valor explícito do request ou a configuração salva da loja."""
        from ...models import ConfiguracaoBackup

        raw = request.data.get("incluir_imagens", None)
        if raw is not None:
            return bool(raw)
        try:
            return bool(ConfiguracaoBackup.objects.get(loja=loja).incluir_imagens)
        except ConfiguracaoBackup.DoesNotExist:
            return False

    def _ensure_loja_database_available(self, loja):
        """Garante que o banco da loja está em settings.DATABASES."""
        if not loja.database_name or loja.database_name in settings.DATABASES:
            return True, None
        from core.db_config import ensure_loja_database_config
        if ensure_loja_database_config(loja.database_name, conn_max_age=60):
            return True, None
        return False, Response(
            {"success": False, "error": "Não foi possível conectar ao banco de dados da loja."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsOwnerOrSuperAdmin])
    def exportar_backup(self, request, pk=None):
        """Exporta backup manual da loja em formato CSV compactado."""
        from django.http import HttpResponse

        from ...backup_service import BackupService
        from ...models import ConfiguracaoBackup, HistoricoBackup

        loja = self.get_object()
        incluir_imagens = self._resolver_incluir_imagens(loja, request)

        ok, err_response = self._ensure_loja_database_available(loja)
        if not ok:
            return err_response

        logger.info(f"📤 Solicitação de exportação de backup - Loja: {loja.nome} (ID: {loja.id})")

        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo="manual",
            status="processando",
            solicitado_por=request.user,
            arquivo_nome="processando...",
        )

        try:
            service = BackupService()
            result = service.exportar_loja(loja_id=loja.id, incluir_imagens=incluir_imagens)

            if not result.get("success"):
                historico.marcar_como_erro(result.get("erro", "Erro desconhecido"))
                return Response({
                    "success": False,
                    "error": result.get("erro"),
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            historico.arquivo_nome = result["arquivo_nome"]
            historico.marcar_como_concluido(
                tamanho_mb=result["tamanho_mb"],
                total_registros=result["total_registros"],
                tabelas=result["tabelas"],
            )

            try:
                config = ConfiguracaoBackup.objects.get(loja=loja)
                config.incrementar_contador()
            except ConfiguracaoBackup.DoesNotExist:
                pass

            response = HttpResponse(result["arquivo_bytes"], content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="{result["arquivo_nome"]}"'
            response["X-Backup-Id"] = str(historico.id)
            response["X-Total-Registros"] = str(result["total_registros"])
            response["X-Tamanho-MB"] = f"{result['tamanho_mb']:.2f}"
            if result["total_registros"] == 0:
                response["X-Backup-Empty"] = "true"

            logger.info(f"✅ Backup exportado com sucesso - {result['arquivo_nome']}")
            return response

        except Exception as e:
            logger.exception(f"❌ Erro ao exportar backup: {e}")
            historico.marcar_como_erro(str(e))
            return Response({
                "success": False,
                "error": f"Erro ao exportar backup: {e!s}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], permission_classes=[IsOwnerOrSuperAdmin], url_path="enviar_backup_agora")
    def enviar_backup_agora(self, request, pk=None):
        """Gera o backup da loja agora e envia por email para o proprietário."""
        from ...backup_email_service import BackupEmailService
        from ...backup_service import BackupService
        from ...models import ConfiguracaoBackup, HistoricoBackup
        from ...tasks import _salvar_arquivo_backup

        loja = self.get_object()
        ok, err_response = self._ensure_loja_database_available(loja)
        if not ok:
            return err_response

        logger.info(f"📤 Enviar backup agora - Loja: {loja.nome} (ID: {loja.id})")

        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo="manual",
            status="processando",
            solicitado_por=request.user,
            arquivo_nome="processando...",
        )

        try:
            service = BackupService()
            result = service.exportar_loja(
                loja_id=loja.id,
                incluir_imagens=self._resolver_incluir_imagens(loja, request),
            )

            if not result.get("success"):
                historico.marcar_como_erro(result.get("erro", "Erro desconhecido"))
                return Response({
                    "success": False,
                    "error": result.get("erro"),
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            arquivo_path = _salvar_arquivo_backup(
                loja=loja,
                arquivo_nome=result["arquivo_nome"],
                arquivo_bytes=result["arquivo_bytes"],
            )
            historico.arquivo_nome = result["arquivo_nome"]
            historico.arquivo_path = arquivo_path
            historico.marcar_como_concluido(
                tamanho_mb=result["tamanho_mb"],
                total_registros=result["total_registros"],
                tabelas=result["tabelas"],
            )

            try:
                config = ConfiguracaoBackup.objects.get(loja=loja)
                config.incrementar_contador()
            except ConfiguracaoBackup.DoesNotExist:
                pass

            email_service = BackupEmailService()
            if email_service.enviar_backup_email(loja_id=loja.id, historico_backup_id=historico.id):
                logger.info(f"✅ Backup enviado por email - {loja.nome}")
                return Response({
                    "success": True,
                    "message": f"Backup enviado para {loja.owner.email}",
                    "historico_id": historico.id,
                })
            return Response({
                "success": False,
                "error": "Backup gerado, mas falha ao enviar email. Verifique o email do proprietário e os logs.",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception(f"❌ Erro em enviar_backup_agora: {e}")
            historico.marcar_como_erro(str(e))
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["post"], permission_classes=[IsOwnerOrSuperAdmin])
    def importar_backup(self, request, pk=None):
        """Importa backup de um arquivo ZIP. ATENÇÃO: operação destrutiva."""
        from ...backup_service import BackupService
        from ...models import HistoricoBackup

        loja = self.get_object()

        ok, err_response = self._ensure_loja_database_available(loja)
        if not ok:
            return err_response

        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            return Response({"success": False, "error": "Arquivo não fornecido"}, status=status.HTTP_400_BAD_REQUEST)

        if not arquivo.name.endswith(".zip"):
            return Response({"success": False, "error": "Arquivo deve ser um ZIP"}, status=status.HTTP_400_BAD_REQUEST)

        if arquivo.size > self.BACKUP_MAX_UPLOAD_BYTES:
            return Response({
                "success": False,
                "error": f"Arquivo muito grande. Máximo: {self.BACKUP_MAX_UPLOAD_BYTES // (1024*1024)}MB",
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"📥 Solicitação de importação de backup - Loja: {loja.nome} - Arquivo: {arquivo.name}")

        historico = HistoricoBackup.objects.create(
            loja=loja,
            tipo="manual",
            status="processando",
            solicitado_por=request.user,
            arquivo_nome=arquivo.name,
        )

        try:
            arquivo_bytes = arquivo.read()

            service = BackupService()
            result = service.importar_loja(loja_id=loja.id, arquivo_zip=arquivo_bytes)

            if not result.get("success"):
                historico.marcar_como_erro(result.get("erro", "Erro desconhecido"))
                return Response({
                    "success": False,
                    "error": result.get("erro"),
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            historico.marcar_como_concluido(
                tamanho_mb=arquivo.size / (1024 * 1024),
                total_registros=result["total_registros_importados"],
                tabelas=result["tabelas"],
            )

            logger.info(f"✅ Backup importado com sucesso - {arquivo.name}")

            return Response({
                "success": True,
                "message": result["message"],
                "total_registros_importados": result["total_registros_importados"],
                "tabelas": result["tabelas"],
                "historico_id": historico.id,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"❌ Erro ao importar backup: {e}")
            historico.marcar_como_erro(str(e))
            return Response({
                "success": False,
                "error": f"Erro ao importar backup: {e!s}",
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"], permission_classes=[IsOwnerOrSuperAdmin])
    def configuracao_backup(self, request, pk=None):
        """Obtém configuração de backup da loja."""
        from ...models import ConfiguracaoBackup
        from ...serializers import ConfiguracaoBackupSerializer

        from ...models.backup import horario_envio_slot_noturno

        loja = self.get_object()
        config, created = ConfiguracaoBackup.objects.get_or_create(
            loja=loja,
            defaults={
                "frequencia": "diario",
                "horario_envio": horario_envio_slot_noturno(loja.id),
            },
        )
        # Garante slot noturno mesmo em configs antigas (sem migration em massa).
        from django.utils import timezone as dj_tz

        slot = horario_envio_slot_noturno(loja.id)
        if config.horario_envio != slot:
            ConfiguracaoBackup.objects.filter(pk=config.pk).update(
                horario_envio=slot,
                updated_at=dj_tz.now(),
            )
            config.horario_envio = slot
        serializer = ConfiguracaoBackupSerializer(config)

        return Response({"success": True, "config": serializer.data, "created": created})

    @action(detail=True, methods=["put", "patch"], permission_classes=[IsOwnerOrSuperAdmin])
    def atualizar_configuracao_backup(self, request, pk=None):
        """Atualiza configuração de backup da loja."""
        from ...models import ConfiguracaoBackup
        from ...models.backup import horario_envio_slot_noturno
        from ...serializers import ConfiguracaoBackupSerializer

        loja = self.get_object()
        config, _ = ConfiguracaoBackup.objects.get_or_create(
            loja=loja,
            defaults={
                "frequencia": "diario",
                "horario_envio": horario_envio_slot_noturno(loja.id),
            },
        )

        # Cliente não escolhe horário — ignora qualquer horario_envio do payload.
        data = {k: v for k, v in request.data.items() if k != "horario_envio"}
        serializer = ConfiguracaoBackupSerializer(config, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            # save() do model já força o slot; reforça após partial update
            config.refresh_from_db()
            slot = horario_envio_slot_noturno(loja.id)
            if config.horario_envio != slot:
                config.horario_envio = slot
                config.save(update_fields=["horario_envio", "updated_at"])
            logger.info(f"✅ Configuração de backup atualizada - Loja: {loja.nome}")
            return Response({
                "success": True,
                "config": ConfiguracaoBackupSerializer(config).data,
                "message": "Configuração atualizada com sucesso",
            })
        return Response({
            "success": False,
            "errors": serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], permission_classes=[IsOwnerOrSuperAdmin])
    def historico_backups(self, request, pk=None):
        """Lista histórico de backups da loja."""
        from ...models import HistoricoBackup
        from ...serializers import HistoricoBackupListSerializer

        loja = self.get_object()
        queryset = HistoricoBackup.objects.filter(loja=loja)

        tipo = request.query_params.get("tipo")
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        limit = int(request.query_params.get("limit", 20))
        queryset = queryset[:limit]

        serializer = HistoricoBackupListSerializer(queryset, many=True)

        return Response({
            "success": True,
            "count": queryset.count(),
            "historico": serializer.data,
        })

    @action(detail=True, methods=["post"], permission_classes=[IsSuperAdmin])
    def reenviar_backup_email(self, request, pk=None):
        """Reenvia último backup por email."""
        from ...backup_email_service import BackupEmailService
        from ...models import HistoricoBackup

        loja = self.get_object()
        historico_id = request.data.get("historico_id")

        if historico_id:
            try:
                historico = HistoricoBackup.objects.get(id=historico_id, loja=loja)
            except HistoricoBackup.DoesNotExist:
                return Response({
                    "success": False,
                    "error": "Histórico de backup não encontrado",
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            historico = HistoricoBackup.objects.filter(
                loja=loja, status="concluido",
            ).order_by("-created_at").first()

            if not historico:
                return Response({
                    "success": False,
                    "error": "Nenhum backup concluído encontrado",
                }, status=status.HTTP_404_NOT_FOUND)

        service = BackupEmailService()
        success = service.enviar_backup_email(loja_id=loja.id, historico_backup_id=historico.id)

        if success:
            return Response({
                "success": True,
                "message": f"Backup enviado para {loja.owner.email}",
                "historico_id": historico.id,
            })
        return Response({
            "success": False,
            "error": "Erro ao enviar email. Verifique os logs.",
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
