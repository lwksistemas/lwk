# Generated migration for CloudinaryConfig model

from django.db import migrations, models, connection


def check_table_exists(table_name):
    """Verifica se a tabela já existe no banco de dados"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [table_name])
        return cursor.fetchone()[0]


def create_cloudinary_config_if_not_exists(apps, schema_editor):
    """Cria a tabela CloudinaryConfig apenas se ela não existir"""
    if not check_table_exists('superadmin_cloudinary_config'):
        # Tabela não existe, criar normalmente
        schema_editor.execute("""
            CREATE TABLE superadmin_cloudinary_config (
                id BIGSERIAL PRIMARY KEY,
                singleton_key VARCHAR(10) NOT NULL UNIQUE DEFAULT 'config',
                cloud_name VARCHAR(100) NOT NULL DEFAULT '',
                api_key VARCHAR(100) NOT NULL DEFAULT '',
                api_secret VARCHAR(100) NOT NULL DEFAULT '',
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ Tabela superadmin_cloudinary_config criada com sucesso")
    else:
        print("⚠️ Tabela superadmin_cloudinary_config já existe, pulando criação")


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0036_fix_financeiro_fk_cascade'),
    ]

    operations = [
        migrations.RunPython(create_cloudinary_config_if_not_exists, migrations.RunPython.noop),
    ]
