"""
Notifica usuários sobre tarefas (atividades) do CRM que estão próximas ou vencendo.
Cria notificações in-app para o owner da loja e envia resumo por WhatsApp quando configurado.

Uso:
  python manage.py notificar_tarefas_crm
  heroku run "cd backend && python manage.py notificar_tarefas_crm" -a lwksistemas

Agende no Heroku Scheduler para rodar a cada hora.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import dj_database_url
import os


class Command(BaseCommand):
    help = 'Cria notificações para tarefas do CRM que estão próximas ou vencendo'

    def _enviar_whatsapp_resumo(self, loja, atividades, config):
        """Envia resumo das tarefas por WhatsApp para o número configurado."""
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp

        if not getattr(config, 'enviar_lembrete_tarefas', True):
            return False
        if not getattr(config, 'whatsapp_ativo', False):
            return False
        telefone = (config.whatsapp_numero or '').strip()
        if not telefone:
            telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        if not telefone:
            return False

        linhas = [f"📋 *Lembretes CRM — {loja.nome}*\n"]
        linhas.append(f"Você tem {len(atividades)} tarefa(s) nas próximas 24h:\n")
        for at in atividades[:10]:
            data_str = at.data.strftime('%d/%m %H:%M') if at.data else ''
            linhas.append(f"• {at.get_tipo_display()}: {at.titulo} — {data_str}")
        if len(atividades) > 10:
            linhas.append(f"… e mais {len(atividades) - 10} tarefa(s)")
        mensagem = '\n'.join(linhas)

        ok, _ = send_whatsapp(telefone=telefone, mensagem=mensagem, user=None, config=config)
        return ok

    def handle(self, *args, **options):
        from superadmin.models import Loja
        from crm_vendas.models import Atividade
        from notificacoes.services import notify
        from notificacoes.models import Notification

        lojas_crm = Loja.objects.filter(
            tipo_loja__slug='crm-vendas',
            is_active=True
        ).select_related('owner', 'tipo_loja')

        if not lojas_crm.exists():
            self.stdout.write('Nenhuma loja CRM ativa.')
            return

        agora = timezone.now()
        daqui_24h = agora + timedelta(hours=24)
        criadas = 0
        whatsapp_enviados = 0

        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            self.stdout.write(self.style.ERROR('DATABASE_URL não configurada'))
            return

        for loja in lojas_crm:
            if not loja.owner_id:
                continue

            schema_name = loja.database_name.replace('-', '_')
            db_name = loja.database_name

            if db_name not in settings.DATABASES:
                default_db = dj_database_url.config(default=DATABASE_URL, conn_max_age=0)
                settings.DATABASES[db_name] = {
                    **default_db,
                    'OPTIONS': {'options': f'-c search_path={schema_name},public'},
                    'ATOMIC_REQUESTS': False,
                    'AUTOCOMMIT': True,
                    'CONN_MAX_AGE': 0,
                }

            try:
                atividades = list(
                    Atividade.objects.using(db_name)
                    .filter(
                        data__gte=agora,
                        data__lte=daqui_24h,
                        concluido=False
                    )
                    .order_by('data')[:20]
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Loja {loja.slug}: {e}'))
                continue

            # WhatsApp: envio de resumo (uma vez por dia, entre 7h e 9h, se configurado)
            try:
                from whatsapp.models import WhatsAppConfig, WhatsAppLog
                hora = agora.hour
                enviar_hoje = 7 <= hora <= 9
                if enviar_hoje and atividades:
                    config = WhatsAppConfig.objects.filter(loja=loja).first()
                    if config:
                        # Evitar envio duplicado no mesmo dia
                        ja_enviou = WhatsAppLog.objects.filter(
                            loja=loja,
                            created_at__date=agora.date(),
                            mensagem__icontains='Lembretes CRM',
                        ).exists()
                        if not ja_enviou and self._enviar_whatsapp_resumo(loja, atividades, config):
                            whatsapp_enviados += 1
                            self.stdout.write(f'  📱 {loja.slug}: resumo enviado por WhatsApp')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  Loja {loja.slug} WhatsApp: {e}'))

            for at in atividades:
                data_str = at.data.strftime('%d/%m/%Y %H:%M') if at.data else ''
                titulo = f'Tarefa: {at.titulo[:50]}{"..." if len(at.titulo) > 50 else ""}'
                mensagem = f'{at.get_tipo_display()}: {at.titulo} — {data_str}'

                notificadas_hoje = Notification.objects.filter(
                    user=loja.owner,
                    tipo='tarefa',
                    created_at__date=agora.date(),
                    metadata__atividade_id=at.id
                ).exists()

                if notificadas_hoje:
                    continue

                try:
                    notify(
                        user=loja.owner,
                        titulo=titulo,
                        mensagem=mensagem,
                        tipo='tarefa',
                        canal='in_app',
                        metadata={
                            'url': f'/loja/{loja.slug}/crm-vendas/calendario',
                            'atividade_id': at.id,
                            'loja_id': loja.id,
                        },
                    )
                    criadas += 1
                    self.stdout.write(f'  ✅ {loja.slug}: {at.titulo[:40]}...')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Erro ao notificar: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ {criadas} notificação(ões) criada(s)'))
        if whatsapp_enviados:
            self.stdout.write(self.style.SUCCESS(f'📱 {whatsapp_enviados} resumo(s) enviado(s) por WhatsApp'))
