# HeroSection.imagem foi criado só via SQL em 0004 (não no estado das migrações).
# RemoveField falharia com KeyError; usamos SQL idempotente no banco.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0039_heroimagem'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE homepage_hero_section DROP COLUMN IF EXISTS imagem;',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
