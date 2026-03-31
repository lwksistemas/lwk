# Generated manually on 2026-03-31
# ✅ NOVO v1421: Sistema híbrido de acesso às lojas

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0039_loginconfigsistema'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='atalho',
            field=models.SlugField(
                blank=True,
                help_text='Atalho curto para acesso fácil (ex: felix). Gerado automaticamente a partir do nome.',
                max_length=50,
                unique=True
            ),
        ),
        migrations.AddField(
            model_name='loja',
            name='subdomain',
            field=models.SlugField(
                blank=True,
                help_text='Subdomínio personalizado (ex: felix.lwksistemas.com.br). Opcional para planos premium.',
                max_length=50,
                null=True,
                unique=True
            ),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['atalho'], name='loja_atalho_idx'),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['subdomain'], name='loja_subdomain_idx'),
        ),
    ]
