# Generated manually - Add loja_id to all models for isolation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stores', '0001_initial'),
        ('servicos', '0004_remove_funcionario_user_funcionario_is_admin'),
    ]

    operations = [
        # Add loja_id to Categoria
        migrations.AddField(
            model_name='categoria',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_categorias',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
        # Add loja_id to Servico
        migrations.AddField(
            model_name='servico',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_servicos',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
        # Add loja_id to Cliente
        migrations.AddField(
            model_name='cliente',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_clientes',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
        # Add loja_id to Profissional
        migrations.AddField(
            model_name='profissional',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_profissionais',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
        # Add loja_id to Agendamento
        migrations.AddField(
            model_name='agendamento',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_agendamentos',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
        # Add loja_id to OrdemServico
        migrations.AddField(
            model_name='ordemservico',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_ordens_servico',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
        # Add loja_id to Orcamento
        migrations.AddField(
            model_name='orcamento',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_orcamentos',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
        # Add loja_id to Funcionario
        migrations.AddField(
            model_name='funcionario',
            name='loja',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='servicos_funcionarios',
                to='stores.loja',
                verbose_name='Loja'
            ),
        ),
    ]
