from django.test import SimpleTestCase

from core.migration_guard import _should_skip_check, CRITICAL_APPS


class MigrationGuardTests(SimpleTestCase):
    def test_critical_apps_include_superadmin(self):
        self.assertIn('superadmin', CRITICAL_APPS)

    def test_skip_on_migrate_command(self):
        import sys
        old = sys.argv
        try:
            sys.argv = ['manage.py', 'migrate']
            self.assertTrue(_should_skip_check())
        finally:
            sys.argv = old
