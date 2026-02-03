# Generated migration for cabeleireiro app

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('nome', models.CharField(max_length=200)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('telefone', models.CharField(max_length=20)),
                ('cpf', models.CharField(blank=True, max_length=14, null=True)),
                ('data_nascimento', models.DateField(blank=True, null=True)),
                ('endereco', models.TextField(blank=True, null=True)),
                ('cidade', models.CharField(blank=True, max_length=100, null=True)),
                ('estado', models.CharField(blank=True, max_length=2, null=True)),
                ('observacoes', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'cabeleireiro_clientes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Profissional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('nome', models.CharField(max_length=200)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('telefone', models.CharField(max_length=20)),
                ('especialidade', models.CharField(help_text='Ex: Coloração, Corte Masculino, Penteados', max_length=100)),
                ('comissao_percentual', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Profissional',
                'verbose_name_plural': 'Profissionais',
                'db_table': 'cabeleireiro_profissionais',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Servico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('nome', models.CharField(max_length=200)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('categoria', models.CharField(choices=[('corte', 'Corte'), ('coloracao', 'Coloração'), ('tratamento', 'Tratamento'), ('penteado', 'Penteado'), ('manicure', 'Manicure/Pedicure'), ('barba', 'Barba'), ('depilacao', 'Depilação'), ('maquiagem', 'Maquiagem'), ('outros', 'Outros')], max_length=20)),
                ('duracao', models.IntegerField(help_text='Duração em minutos')),
                ('preco', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Serviço',
                'verbose_name_plural': 'Serviços',
                'db_table': 'cabeleireiro_servicos',
                'ordering': ['categoria', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='Produto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('nome', models.CharField(max_length=200)),
                ('descricao', models.TextField(blank=True, null=True)),
                ('categoria', models.CharField(choices=[('shampoo', 'Shampoo'), ('condicionador', 'Condicionador'), ('mascara', 'Máscara'), ('finalizador', 'Finalizador'), ('coloracao', 'Coloração'), ('tratamento', 'Tratamento'), ('acessorio', 'Acessório'), ('outros', 'Outros')], max_length=20)),
                ('marca', models.CharField(blank=True, max_length=100, null=True)),
                ('preco_custo', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('preco_venda', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('estoque_atual', models.IntegerField(default=0)),
                ('estoque_minimo', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Produto',
                'verbose_name_plural': 'Produtos',
                'db_table': 'cabeleireiro_produtos',
                'ordering': ['categoria', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='Funcionario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('nome', models.CharField(max_length=200)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('telefone', models.CharField(max_length=20)),
                ('cpf', models.CharField(blank=True, max_length=14, null=True)),
                ('cargo', models.CharField(max_length=100)),
                ('salario', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('data_admissao', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Funcionário',
                'verbose_name_plural': 'Funcionários',
                'db_table': 'cabeleireiro_funcionarios',
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='HorarioFuncionamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('dia_semana', models.IntegerField(choices=[(0, 'Segunda-feira'), (1, 'Terça-feira'), (2, 'Quarta-feira'), (3, 'Quinta-feira'), (4, 'Sexta-feira'), (5, 'Sábado'), (6, 'Domingo')])),
                ('horario_abertura', models.TimeField()),
                ('horario_fechamento', models.TimeField()),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Horário de Funcionamento',
                'verbose_name_plural': 'Horários de Funcionamento',
                'db_table': 'cabeleireiro_horarios',
                'ordering': ['dia_semana'],
            },
        ),
        migrations.CreateModel(
            name='Agendamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('data', models.DateField()),
                ('horario', models.TimeField()),
                ('status', models.CharField(choices=[('agendado', 'Agendado'), ('confirmado', 'Confirmado'), ('em_atendimento', 'Em Atendimento'), ('concluido', 'Concluído'), ('cancelado', 'Cancelado'), ('falta', 'Falta')], default='agendado', max_length=20)),
                ('observacoes', models.TextField(blank=True, null=True)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('valor_pago', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('forma_pagamento', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agendamentos', to='cabeleireiro.cliente')),
                ('profissional', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='agendamentos', to='cabeleireiro.profissional')),
                ('servico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agendamentos', to='cabeleireiro.servico')),
            ],
            options={
                'verbose_name': 'Agendamento',
                'verbose_name_plural': 'Agendamentos',
                'db_table': 'cabeleireiro_agendamentos',
                'ordering': ['-data', '-horario'],
            },
        ),
        migrations.CreateModel(
            name='Venda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('quantidade', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('valor_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('forma_pagamento', models.CharField(choices=[('dinheiro', 'Dinheiro'), ('debito', 'Débito'), ('credito', 'Crédito'), ('pix', 'PIX'), ('outros', 'Outros')], max_length=20)),
                ('data_venda', models.DateTimeField(auto_now_add=True)),
                ('observacoes', models.TextField(blank=True, null=True)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vendas', to='cabeleireiro.cliente')),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vendas', to='cabeleireiro.produto')),
            ],
            options={
                'verbose_name': 'Venda',
                'verbose_name_plural': 'Vendas',
                'db_table': 'cabeleireiro_vendas',
                'ordering': ['-data_venda'],
            },
        ),
        migrations.CreateModel(
            name='BloqueioAgenda',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.CharField(db_index=True, max_length=100)),
                ('data_inicio', models.DateField()),
                ('data_fim', models.DateField()),
                ('motivo', models.CharField(max_length=200)),
                ('observacoes', models.TextField(blank=True, null=True)),
                ('profissional', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bloqueios', to='cabeleireiro.profissional')),
            ],
            options={
                'verbose_name': 'Bloqueio de Agenda',
                'verbose_name_plural': 'Bloqueios de Agenda',
                'db_table': 'cabeleireiro_bloqueios',
                'ordering': ['-data_inicio'],
            },
        ),
    ]
