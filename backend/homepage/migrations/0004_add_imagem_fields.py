# Generated manually

from django.db import migrations, models


def add_imagem_if_not_exists(apps, schema_editor):
    """Adiciona campos imagem apenas se não existirem"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Verificar e adicionar imagem em funcionalidade
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='homepage_funcionalidade' AND column_name='imagem'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE homepage_funcionalidade 
                ADD COLUMN imagem VARCHAR(500) NULL
            """)
        
        # Verificar e adicionar imagem em herosection
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='homepage_hero_section' AND column_name='imagem'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE homepage_hero_section 
                ADD COLUMN imagem VARCHAR(500) NULL
            """)
        
        # Verificar e adicionar imagem em modulosistema
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='homepage_modulo_sistema' AND column_name='imagem'
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE homepage_modulo_sistema 
                ADD COLUMN imagem VARCHAR(500) NULL
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0003_herosection_botao_principal_ativo'),
    ]

    operations = [
        migrations.RunPython(add_imagem_if_not_exists, migrations.RunPython.noop),
    ]
