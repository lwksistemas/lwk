import os
import sys

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()


def _run_startup_ensures():
    """Verificações leves ao subir worker. Schema ensures ficam só no releaseCommand (Railway)."""
    if os.environ.get("LWK_SKIP_STARTUP_ENSURE") == "1":
        return
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    if "production" not in settings_module:
        return
    try:
        from datetime import timedelta

        from django.core.management import call_command
        from django.db.models import Q
        from django.utils import timezone

        from superadmin.models import Loja

        stale_cutoff = timezone.now() - timedelta(hours=6)
        needs_storage_check = Loja.objects.filter(is_active=True).filter(
            Q(storage_ultima_verificacao__isnull=True)
            | Q(storage_ultima_verificacao__lt=stale_cutoff),
        ).exists()
        if needs_storage_check:
            from django.core.management import get_commands
            if "verificar_storage_lojas" in get_commands():
                call_command("verificar_storage_lojas", verbosity=1)
    except Exception as exc:
        print(f"[wsgi] startup ensures falhou: {exc}", file=sys.stderr)


def _start_backup_scheduler():
    """Verifica backups automáticos a cada 5 min (lock por hora no cache).
    Substitui Heroku Scheduler no Railway.
    """
    if os.environ.get("LWK_SKIP_STARTUP_ENSURE") == "1":
        return
    if os.environ.get("LWK_ENABLE_BACKUP_SCHEDULER", "0") != "1":
        return
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    if "production" not in settings_module:
        return

    import threading
    import time

    def _loop():
        time.sleep(90)
        while True:
            try:
                from django.core.cache import cache
                from django.core.management import call_command
                from django.utils import timezone

                hour_key = timezone.localtime(timezone.now()).strftime("%Y%m%d%H")
                if cache.add(f"lwk_backup_cron:{hour_key}", 1, timeout=4000):
                    call_command("executar_backups_automaticos", verbosity=1)
            except Exception as exc:
                print(f"[wsgi] backup scheduler: {exc}", file=sys.stderr)
            time.sleep(300)

    threading.Thread(target=_loop, daemon=True, name="lwk-backup-scheduler").start()


def _start_whatsapp_scheduler():
    """Lembretes WhatsApp 24h (1x/dia ~8h) e 2h (a cada 30 min) + CRM tarefas.
    Substitui django-q/Heroku Scheduler no Railway.
    """
    if os.environ.get("LWK_SKIP_STARTUP_ENSURE") == "1":
        return
    if os.environ.get("LWK_ENABLE_WHATSAPP_SCHEDULER", "0") != "1":
        return
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    if "production" not in settings_module:
        return

    import threading
    import time

    def _loop():
        time.sleep(120)
        while True:
            try:
                from django.core.cache import cache
                from django.core.management import call_command
                from django.utils import timezone

                now = timezone.localtime(timezone.now())
                hour = now.hour
                minute_slot = "00" if now.minute < 30 else "30"
                slot_key = now.strftime(f"%Y%m%d%H{minute_slot}")

                if cache.add(f"lwk_wa_2h:{slot_key}", 1, timeout=2000):
                    from whatsapp.tasks import send_lembretes_2h_whatsapp
                    send_lembretes_2h_whatsapp()
                    from crm_vendas.atividade_lembrete_tasks import send_lembretes_atividade_crm_2h
                    send_lembretes_atividade_crm_2h()
                    from crm_vendas.assinatura_vendedor_retry import processar_envios_vendedor_pendentes
                    processar_envios_vendedor_pendentes()
                    from asaas_integration.nfse_assinatura_retry import processar_nfse_assinatura_pendentes
                    processar_nfse_assinatura_pendentes()

                if cache.add(f"lwk_crm_ativ_24h:{slot_key}", 1, timeout=2000):
                    from crm_vendas.atividade_lembrete_tasks import send_lembretes_atividade_crm_24h
                    send_lembretes_atividade_crm_24h()

                if 7 <= hour <= 9:
                    day_key = now.strftime("%Y%m%d")
                    if cache.add(f"lwk_wa_24h:{day_key}", 1, timeout=90000):
                        from whatsapp.tasks import send_lembretes_24h_whatsapp
                        send_lembretes_24h_whatsapp()
                    if cache.add(f"lwk_crm_tarefas:{day_key}", 1, timeout=90000):
                        call_command("notificar_tarefas_crm", verbosity=1)
                    if cache.add(f"lwk_wa_cobranca:{day_key}", 1, timeout=90000):
                        from whatsapp.tasks import send_cobrancas_pendentes_whatsapp
                        send_cobrancas_pendentes_whatsapp()
            except Exception as exc:
                print(f"[wsgi] whatsapp scheduler: {exc}", file=sys.stderr)
            time.sleep(300)

    threading.Thread(target=_loop, daemon=True, name="lwk-whatsapp-scheduler").start()


def _start_security_scheduler():
    """Detecção de violações de segurança a cada 5 min.
    Substitui django-q no Railway.
    """
    if os.environ.get("LWK_SKIP_STARTUP_ENSURE") == "1":
        return
    if os.environ.get("LWK_ENABLE_SECURITY_SCHEDULER", "0") != "1":
        return
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    if "production" not in settings_module:
        return

    import threading
    import time

    def _loop():
        time.sleep(150)
        while True:
            try:
                from django.core.cache import cache
                from django.utils import timezone

                now = timezone.localtime(timezone.now())
                slot = f"{now.strftime('%Y%m%d%H')}{now.minute // 5}"
                if cache.add(f"lwk_security_detect:{slot}", 1, timeout=400):
                    from superadmin.tasks import detect_security_violations
                    detect_security_violations()
            except Exception as exc:
                print(f"[wsgi] security scheduler: {exc}", file=sys.stderr)
            time.sleep(300)

    threading.Thread(target=_loop, daemon=True, name="lwk-security-scheduler").start()


_run_startup_ensures()
_start_backup_scheduler()
_start_whatsapp_scheduler()
_start_security_scheduler()
