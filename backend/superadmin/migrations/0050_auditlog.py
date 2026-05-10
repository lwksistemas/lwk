import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('superadmin', '0049_alter_nfseemitida_loja_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario_email', models.CharField(blank=True, max_length=200)),
                ('usuario_nome', models.CharField(blank=True, max_length=200)),
                ('acao', models.CharField(db_index=True, max_length=50, choices=[
                    ('nfse_emitir_manual', 'Emissão manual de NFS-e'),
                    ('nfse_emitir_auto', 'Emissão automática de NFS-e'),
                    ('nfse_cancelar', 'Cancelamento de NFS-e'),
                    ('nfse_reenviar', 'Reenvio de NFS-e por email'),
                    ('config_certificado_upload', 'Upload de certificado digital'),
                    ('config_certificado_acesso', 'Acesso a certificado digital'),
                    ('config_alterar', 'Alteração de configuração sensível'),
                    ('config_issnet_test', 'Teste de conexão ISSNet'),
                    ('login_superadmin', 'Login no superadmin'),
                    ('outro', 'Outra ação'),
                ])),
                ('descricao', models.CharField(blank=True, max_length=500)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('sucesso', models.BooleanField(default=True)),
                ('detalhes', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Audit Log',
                'verbose_name_plural': 'Audit Logs',
                'db_table': 'superadmin_audit_log',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['acao', '-created_at'], name='audit_acao_created_idx'),
                    models.Index(fields=['user', '-created_at'], name='audit_user_created_idx'),
                ],
            },
        ),
    ]
