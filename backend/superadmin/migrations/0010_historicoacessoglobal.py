# Generated manually on 2026-02-08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('superadmin', '0009_alter_loja_database_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoAcessoGlobal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario_email', models.EmailField(help_text='Email do usuário (backup se user for deletado)', max_length=254)),
                ('usuario_nome', models.CharField(help_text='Nome completo do usuário', max_length=200)),
                ('loja_nome', models.CharField(blank=True, help_text='Nome da loja (backup)', max_length=200)),
                ('loja_slug', models.CharField(blank=True, help_text='Slug da loja', max_length=100)),
                ('acao', models.CharField(choices=[('login', 'Login'), ('logout', 'Logout'), ('criar', 'Criar'), ('editar', 'Editar'), ('excluir', 'Excluir'), ('visualizar', 'Visualizar'), ('exportar', 'Exportar'), ('importar', 'Importar'), ('aprovar', 'Aprovar'), ('rejeitar', 'Rejeitar')], db_index=True, help_text='Tipo de ação realizada', max_length=20)),
                ('recurso', models.CharField(blank=True, help_text='Recurso afetado (ex: Cliente, Produto, Agendamento)', max_length=100)),
                ('recurso_id', models.IntegerField(blank=True, help_text='ID do recurso afetado', null=True)),
                ('detalhes', models.TextField(blank=True, help_text='Detalhes adicionais da ação (JSON ou texto)')),
                ('ip_address', models.GenericIPAddressField(help_text='Endereço IP do usuário')),
                ('user_agent', models.TextField(blank=True, help_text='User Agent do navegador')),
                ('metodo_http', models.CharField(blank=True, help_text='Método HTTP (GET, POST, PUT, DELETE)', max_length=10)),
                ('url', models.CharField(blank=True, help_text='URL da requisição', max_length=500)),
                ('sucesso', models.BooleanField(default=True, help_text='Indica se a ação foi bem-sucedida')),
                ('erro', models.TextField(blank=True, help_text='Mensagem de erro (se houver)')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('loja', models.ForeignKey(blank=True, help_text='Loja onde a ação foi realizada (null para ações do SuperAdmin)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='historico_acoes', to='superadmin.loja')),
                ('user', models.ForeignKey(blank=True, help_text='Usuário que realizou a ação', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='historico_acoes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Histórico de Acesso Global',
                'verbose_name_plural': 'Histórico de Acessos Global',
                'db_table': 'superadmin_historico_acesso_global',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='historicoacessoglobal',
            index=models.Index(fields=['user', '-created_at'], name='hist_user_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historicoacessoglobal',
            index=models.Index(fields=['loja', '-created_at'], name='hist_loja_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historicoacessoglobal',
            index=models.Index(fields=['acao', '-created_at'], name='hist_acao_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historicoacessoglobal',
            index=models.Index(fields=['usuario_email', '-created_at'], name='hist_email_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historicoacessoglobal',
            index=models.Index(fields=['ip_address', '-created_at'], name='hist_ip_date_idx'),
        ),
        migrations.AddIndex(
            model_name='historicoacessoglobal',
            index=models.Index(fields=['sucesso', '-created_at'], name='hist_sucesso_date_idx'),
        ),
    ]
