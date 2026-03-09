# Generated manually - VendedorUsuario para CRM Vendas

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0033_googlecalendarconnection'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VendedorUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vendedor_id', models.PositiveIntegerField(help_text='ID do Vendedor no schema da loja (crm_vendas)')),
                ('precisa_trocar_senha', models.BooleanField(default=True, help_text='Obrigar troca de senha no primeiro acesso')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('loja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendedores_usuarios', to='superadmin.loja')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendedor_lojas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vendedor (acesso)',
                'verbose_name_plural': 'Vendedores (acesso)',
            },
        ),
        migrations.AlterUniqueTogether(
            name='vendedorusuario',
            unique_together={('user', 'loja')},
        ),
        migrations.AddIndex(
            model_name='vendedorusuario',
            index=models.Index(fields=['user', 'loja'], name='vend_usuario_loja_idx'),
        ),
    ]
