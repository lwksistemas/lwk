# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0004_add_imagem_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhyUsBenefit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(help_text='Ex: Aumente sua produtividade', max_length=100)),
                ('descricao', models.TextField(blank=True, help_text='Descrição detalhada (opcional)')),
                ('icone', models.CharField(blank=True, default='✓', help_text='Emoji ou ícone', max_length=50)),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('ativo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Benefício WhyUs',
                'verbose_name_plural': 'Benefícios WhyUs',
                'db_table': 'homepage_whyus_benefit',
                'ordering': ['ordem', 'id'],
            },
        ),
    ]
