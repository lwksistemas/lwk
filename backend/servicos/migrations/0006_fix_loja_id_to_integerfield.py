# Generated manually - Fix loja_id from ForeignKey to IntegerField

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicos', '0005_add_loja_isolation'),
    ]

    operations = [
        # Remove ForeignKey loja from all models
        migrations.RemoveField(
            model_name='categoria',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='servico',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='cliente',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='profissional',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='agendamento',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='ordemservico',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='orcamento',
            name='loja',
        ),
        migrations.RemoveField(
            model_name='funcionario',
            name='loja',
        ),
        
        # Add IntegerField loja_id to all models
        migrations.AddField(
            model_name='categoria',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='servico',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cliente',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='profissional',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='agendamento',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ordemservico',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='orcamento',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='funcionario',
            name='loja_id',
            field=models.IntegerField(
                db_index=True,
                default=1,
                help_text='ID da loja proprietária deste registro'
            ),
            preserve_default=False,
        ),
    ]
