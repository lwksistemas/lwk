"""
Notifica usuários sobre tarefas (atividades) do CRM que estão próximas ou vencendo.
Cria notificações in-app para o owner da loja.

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
