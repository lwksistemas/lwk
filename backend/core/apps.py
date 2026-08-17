from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from core.migration_guard import run_migration_guard

        run_migration_guard()
        self._connect_q_tenant_cleanup()

    @staticmethod
    def _connect_q_tenant_cleanup() -> None:
        try:
            from django_q.signals import post_execute
        except ImportError:
            return
        from core.q_signals import close_tenant_after_task

        post_execute.connect(close_tenant_after_task, dispatch_uid="lwk_close_tenant_after_q")
