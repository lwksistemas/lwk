# Generated manually on 2026-03-31
# ✅ NOVO v1421: Adiciona unique constraints após gerar atalhos

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0040_add_atalho_subdomain_fields'),
    ]

    operations = [
        # Adicionar unique constraint ao campo atalho
        migrations.AlterField(
            model_name='loja',
            name='atalho',
            field=models.SlugField(
                blank=True,
                help_text='Atalho curto para acesso fácil (ex: felix). Gerado automaticamente a partir do nome.',
                max_length=50,
                unique=True  # Agora com unique
            ),
        ),
        # Adicionar unique constraint ao campo subdomain
        migrations.AlterField(
            model_name='loja',
            name='subdomain',
            field=models.SlugField(
                blank=True,
                help_text='Subdomínio personalizado (ex: felix.lwksistemas.com.br). Opcional para planos premium.',
                max_length=50,
                null=True,
                unique=True  # Agora com unique
            ),
        ),
    ]
