# Generated manually

from django.db import migrations, models
import core.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_estetica', '0006_remove_funcionario_user_funcionario_is_admin'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoLogin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, verbose_name='ID da Loja')),
                ('usuario', models.CharField(max_length=200, verbose_name='Usuário')),
                ('usuario_nome', models.CharField(max_length=200, verbose_name='Nome do Usuário')),
                ('acao', models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'), ('criar', 'Criar'), ('editar', 'Editar'), ('excluir', 'Excluir'), ('visualizar', 'Visualizar'), ('exportar', 'Exportar'), ('importar', 'Importar')], max_length=20, verbose_name='Ação')),
                ('detalhes', models.TextField(blank=True, null=True, verbose_name='Detalhes')),
                ('ip_address', models.GenericIPAddressField(verbose_name='Endereço IP')),
                ('user_agent', models.TextField(blank=True, null=True, verbose_name='User Agent')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Histórico de Login',
                'verbose_name_plural': 'Histórico de Logins',
                'db_table': 'clinica_historico_login',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['loja_id', '-created_at'], name='clinica_his_loja_id_f8c9a5_idx'),
                    models.Index(fields=['usuario', '-created_at'], name='clinica_his_usuario_a1b2c3_idx'),
                    models.Index(fields=['acao', '-created_at'], name='clinica_his_acao_d4e5f6_idx'),
                ],
            },
            bases=(core.mixins.LojaIsolationMixin, models.Model),
        ),
    ]
