# Generated migration for adding funcao, especialidade and comissao_percentual to Funcionario

from django.db import migrations, models
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cabeleireiro', '0002_funcionario_horariofuncionamento_bloqueioagenda'),
    ]

    operations = [
        migrations.AddField(
            model_name='funcionario',
            name='funcao',
            field=models.CharField(
                choices=[
                    ('administrador', 'Administrador'),
                    ('gerente', 'Gerente'),
                    ('atendente', 'Atendente/Recepcionista'),
                    ('profissional', 'Profissional/Cabeleireiro'),
                    ('caixa', 'Caixa'),
                    ('estoquista', 'Estoquista'),
                    ('visualizador', 'Visualizador'),
                ],
                default='atendente',
                help_text='Define as permissões de acesso ao sistema',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='funcionario',
            name='especialidade',
            field=models.CharField(
                blank=True,
                help_text='Ex: Coloração, Corte Masculino, Penteados (para profissionais)',
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='funcionario',
            name='comissao_percentual',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Comissão sobre serviços realizados (para profissionais)',
                max_digits=5,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AlterField(
            model_name='funcionario',
            name='cargo',
            field=models.CharField(
                help_text='Cargo descritivo (ex: Recepcionista, Cabeleireiro)',
                max_length=100,
            ),
        ),
    ]
