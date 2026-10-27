"""Serviço de Email para Backups - v800

Responsabilidades:
- Enviar backups por email
- Gerenciar templates de email
- Controlar anexos

Boas práticas aplicadas:
- Single Responsibility
- Template Method Pattern
- Error Handling robusto
"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

logger = logging.getLogger(__name__)


def _pessoas_backup_da_loja(loja) -> list[dict]:
    """Administrador do sistema e funcionários com perfil Administrador recebem o backup."""
    from crm_vendas.models import Vendedor
    from crm_vendas.vendedor_permissoes_service import GRUPO_ADMINISTRADOR_CRM, garantir_grupo_administrador

    pessoas: list[dict] = []
    grupo_id = None
    try:
        grupo_id = garantir_grupo_administrador().id
    except Exception:
        logger.exception("Não foi possível garantir o perfil Administrador")

    if not getattr(loja, "database_name", None) or not getattr(loja, "database_created", False):
        return pessoas

    from core.db_config import ensure_loja_database_config

    if not ensure_loja_database_config(loja.database_name):
        return pessoas

    try:
        vendedores = Vendedor.objects.all_without_filter().using(loja.database_name).filter(
            loja_id=loja.id,
            is_active=True,
        )
        for vendedor in vendedores.only("email", "is_admin", "config_acesso"):
            cfg = vendedor.config_acesso or {}
            try:
                grupo_vendedor = int(cfg.get("grupo_id")) if cfg.get("grupo_id") is not None else None
            except (TypeError, ValueError):
                grupo_vendedor = None
            pessoas.append({
                "email": vendedor.email or "",
                "recebe_backup": bool(vendedor.is_admin) or (
                    grupo_id is not None and grupo_vendedor == grupo_id
                ),
            })
    except Exception:
        logger.exception("Não foi possível ler os funcionários da loja %s para o backup", loja.id)

    if grupo_id is None:
        return pessoas

    try:
        from superadmin.models import VendedorUsuario

        usuarios = VendedorUsuario.objects.using("default").filter(
            loja_id=loja.id,
            user__groups__name=GRUPO_ADMINISTRADOR_CRM,
        ).select_related("user")
        for vinculo in usuarios:
            pessoas.append({
                "email": vinculo.user.email or "",
                "recebe_backup": True,
            })
    except Exception:
        logger.exception("Não foi possível ler o perfil Administrador da loja %s", loja.id)
    return pessoas


class BackupEmailService:
    """Serviço para envio de emails com backups.

    Encapsula toda a lógica de envio de emails relacionados a backup.
    """

    def __init__(self):
        from core.email_delivery import get_from_email
        self.from_email = get_from_email()

    def enviar_backup_email(
        self,
        loja_id: int,
        historico_backup_id: int,
    ) -> bool:
        """Envia backup por email para o admin da loja.

        Args:
            loja_id: ID da loja
            historico_backup_id: ID do registro de histórico

        Returns:
            bool: True se enviado com sucesso, False caso contrário

        """
        from .models import HistoricoBackup, Loja

        try:
            # Buscar loja e histórico
            loja = Loja.objects.select_related("owner", "tipo_loja").get(id=loja_id)
            historico = HistoricoBackup.objects.get(id=historico_backup_id)

            if historico.status != "concluido":
                logger.error(f"❌ Backup {historico_backup_id} não está concluído")
                return False

            # Administrador do sistema e funcionários com perfil Administrador.
            # Vendedor comum não entra.
            from .backup_destinatarios import filtrar_emails_backup

            destinatarios = filtrar_emails_backup(
                loja.owner.email or "",
                _pessoas_backup_da_loja(loja),
            )
            if not destinatarios:
                logger.error(
                    "❌ Loja %s (id=%s) não tem administrador para receber o backup",
                    loja.nome,
                    loja.id,
                )
                return False

            # Preparar email
            from .backup_midia_link import url_pagina_backup_midia

            from .backup_helpers import backup_inclui_midia

            inclui_midia = backup_inclui_midia(loja)
            link_midia = "" if inclui_midia else url_pagina_backup_midia(loja)
            assunto = self._criar_assunto(loja, historico)
            corpo_html = self._criar_corpo_html(loja, historico, link_midia, inclui_midia)
            corpo_texto = self._criar_corpo_texto(loja, historico, link_midia, inclui_midia)

            # Multipart texto + HTML (Resend API exige alternatives, não content_subtype)
            from core.email_delivery import create_email_multipart, send_prepared
            from core.email_sync_context import email_sync_only
            email = create_email_multipart(
                subject=assunto,
                body=corpo_texto,
                to=destinatarios,
                html=corpo_html.strip(),
            )

            if historico.arquivo_path:
                try:
                    self._anexar_arquivo(email, historico)
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível anexar arquivo: {e}")

            token = email_sync_only.set(True)
            try:
                send_prepared(email, fail_silently=False)
            finally:
                email_sync_only.reset(token)

            # Marcar como enviado
            historico.marcar_email_enviado(", ".join(destinatarios)[:254])

            from django.utils import timezone

            from .models import ConfiguracaoBackup
            ConfiguracaoBackup.objects.filter(loja=loja).update(
                ultimo_envio_email=timezone.now(),
            )

            logger.info("✅ Backup enviado por email para %s (loja %s)", ", ".join(destinatarios), loja.nome)
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao enviar backup por email: {e}")
            return False


    def _criar_assunto(self, loja, historico) -> str:
        """Cria assunto do email (data em horário local - America/Sao_Paulo)."""
        data_local = timezone.localtime(historico.created_at)
        data = data_local.strftime("%d/%m/%Y")
        return f"Backup Automático - {loja.nome} - {data}"

    def _criar_corpo_html(self, loja, historico, link_midia: str = "", inclui_midia: bool = False) -> str:
        """Cria corpo HTML do email (data/hora em horário local)."""
        data_local = timezone.localtime(historico.created_at)
        context = {
            "loja": loja,
            "historico": historico,
            "owner_nome": loja.owner.first_name or loja.owner.username,
            "data_backup": data_local.strftime("%d/%m/%Y às %H:%M"),
            "tamanho": historico.get_tamanho_formatado(),
            "total_registros": historico.total_registros,
            "tabelas": historico.tabelas_incluidas,
            "tempo_processamento": historico.get_tempo_processamento_formatado(),
            "link_midia": link_midia,
        }

        # Template HTML inline (pode ser movido para arquivo separado)
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #10B981; color: white; padding: 20px; text-align: center; }}
                .content {{ background: #f9f9f9; padding: 20px; }}
                .info-box {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #10B981; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .warning {{ background: #FEF3C7; padding: 15px; border-left: 4px solid #F59E0B; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💾 Backup Automático</h1>
                    <p>{loja.nome}</p>
                </div>

                <div class="content">
                    <p>Olá <strong>{context['owner_nome']}</strong>,</p>

                    {self._paragrafo_conteudo(loja, context, inclui_midia)}

                    <div class="info-box">
                        <h3>📊 Informações do Backup</h3>
                        <ul>
                            <li><strong>Data/Hora:</strong> {context['data_backup']}</li>
                            <li><strong>Total de Registros:</strong> {context['total_registros']:,}</li>
                            <li><strong>Tamanho do Arquivo:</strong> {context['tamanho']}</li>
                            <li><strong>Tempo de Processamento:</strong> {context['tempo_processamento']}</li>
                        </ul>
                    </div>

                    <div class="warning">
                        <h3>⚠️ IMPORTANTE</h3>
                        <ul>
                            <li>Guarde este arquivo em local seguro</li>
                            <li>Use este backup apenas em caso de necessidade</li>
                            <li>Para restaurar, acesse o painel de administração</li>
                            <li>Não compartilhe este arquivo com terceiros</li>
                        </ul>
                    </div>
                </div>

                <div class="footer">
                    <p>Atenciosamente,<br>Equipe {getattr(settings, 'SITE_NAME', 'Sistema')}</p>
                    <p>Este é um email automático, não responda.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _paragrafo_conteudo(self, loja, context, inclui_midia: bool) -> str:
        if inclui_midia:
            return (
                f'<p>Segue em anexo o backup completo da loja <strong>"{loja.nome}"</strong> '
                "(cadastros, fotos, logos e PDFs).</p>"
            )
        link = context.get("link_midia") or ""
        bloco_link = (
            f'<div class="info-box"><p><a href="{link}" style="color:#059669;font-weight:bold;">'
            "Baixar todas as fotos e PDFs (um ZIP)</a></p>"
            f'<p style="font-size:12px;color:#666;word-break:break-all;">{link}</p>'
            '<p style="font-size:12px;">O link vale por 21 dias.</p></div>'
            if link else ""
        )
        return (
            f'<p>Segue em anexo o backup dos <strong>cadastros</strong> da loja '
            f'<strong>"{loja.nome}"</strong> (ZIP com planilhas).</p>'
            "<p>As fotos e PDFs não vão no anexo. O link abaixo baixa tudo de uma vez, "
            "em um único arquivo ZIP.</p>"
            f"{bloco_link}"
        )

    def _criar_corpo_texto(self, loja, historico, link_midia: str = "", inclui_midia: bool = False) -> str:
        """Cria corpo em texto puro do email (data/hora em horário local)."""
        owner_nome = loja.owner.first_name or loja.owner.username
        data_local = timezone.localtime(historico.created_at)
        data_backup = data_local.strftime("%d/%m/%Y às %H:%M")

        texto = f"""
Backup Automático - {loja.nome}

Olá {owner_nome},

{self._texto_conteudo(loja, link_midia, inclui_midia)}

📊 INFORMAÇÕES DO BACKUP:
- Data/Hora: {data_backup}
- Total de Registros: {historico.total_registros:,}
- Tamanho do Arquivo: {historico.get_tamanho_formatado()}
- Tempo de Processamento: {historico.get_tempo_processamento_formatado()}

⚠️ IMPORTANTE:
- Guarde este arquivo em local seguro
- Use este backup apenas em caso de necessidade
- Para restaurar, acesse o painel de administração
- Não compartilhe este arquivo com terceiros

Atenciosamente,
Equipe {getattr(settings, 'SITE_NAME', 'Sistema')}

---
Este é um email automático, não responda.
        """

        return texto.strip()

    def _texto_conteudo(self, loja, link_midia: str, inclui_midia: bool) -> str:
        if inclui_midia:
            return f'Segue em anexo o backup completo da loja "{loja.nome}" (cadastros, fotos, logos e PDFs).'
        return (
            f'Segue em anexo o backup dos cadastros da loja "{loja.nome}" (ZIP com planilhas).\n'
            "As fotos e PDFs não vão no anexo. O link baixa tudo de uma vez, em um único ZIP "
            "(válido por 21 dias):\n"
            f"{link_midia or '(sem link de mídia)'}"
        )

    def _anexar_arquivo(self, email: EmailMessage, historico):
        """Anexa arquivo de backup ao email.

        Tenta ler do filesystem. Se o arquivo não existir (container
        recriado no deploy), loga um aviso e retorna sem anexo
        — o email ainda é enviado com as informações do backup no corpo.
        """
        import os

        if not historico.arquivo_path:
            logger.warning(
                "⚠️ Backup %s (loja=%s) não tem arquivo_path — email enviado sem anexo",
                historico.id, historico.loja_id,
            )
            return

        if not os.path.exists(historico.arquivo_path):
            logger.warning(
                "⚠️ Arquivo de backup não encontrado no disco (%s) — "
                "container pode ter sido reiniciado após o backup. "
                "Email enviado sem anexo.",
                historico.arquivo_path,
            )
            return

        with open(historico.arquivo_path, "rb") as f:
            arquivo_bytes = f.read()

        email.attach(historico.arquivo_nome, arquivo_bytes, "application/zip")
        logger.info("📎 Arquivo %s anexado ao email (%s bytes)", historico.arquivo_nome, len(arquivo_bytes))
