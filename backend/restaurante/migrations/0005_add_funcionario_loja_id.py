# Generated manually - adiciona loja_id a Funcionario (isolamento por loja)

from django.db import migrations, models


def criar_admin_restaurante_existentes(apps, schema_editor):
    """Cria funcionário admin para cada loja Restaurante que ainda não tem."""
    Loja = apps.get_model('superadmin', 'Loja')
    TipoLoja = apps.get_model('superadmin', 'TipoLoja')
    Funcionario = apps.get_model('restaurante', 'Funcionario')

    try:
        tipo_restaurante = TipoLoja.objects.filter(nome='Restaurante').first()
        if not tipo_restaurante:
            return
        lojas = Loja.objects.filter(tipo_loja=tipo_restaurante, is_active=True)
        for loja in lojas:
            owner = loja.owner
            if not owner:
                continue
            if Funcionario.objects.filter(loja_id=loja.id, email=owner.email).exists():
                continue
            Funcionario.objects.create(
                nome=owner.get_full_name() or owner.username,
                email=owner.email,
                telefone='',
                cargo='gerente',
                is_admin=True,
                loja_id=loja.id,
            )
    except Exception:
        pass  # Tabela pode não existir ainda em outros ambientes


def preencher_loja_id_existentes(apps, schema_editor):
    """Preenche loja_id em funcionários existentes (primeira loja Restaurante)."""
    Funcionario = apps.get_model('restaurante', 'Funcionario')
    Loja = apps.get_model('superadmin', 'Loja')
    TipoLoja = apps.get_model('superadmin', 'TipoLoja')
    try:
        tipo_restaurante = TipoLoja.objects.filter(nome='Restaurante').first()
        if not tipo_restaurante:
            return
        primeira_loja = Loja.objects.filter(tipo_loja=tipo_restaurante).order_by('id').first()
        if primeira_loja:
            Funcionario.objects.filter(loja_id__isnull=True).update(loja_id=primeira_loja.id)
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('restaurante', '0004_remove_funcionario_user_funcionario_is_admin'),
        ('superadmin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='funcionario',
            name='loja_id',
            field=models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro', null=True),
        ),
        migrations.RunPython(preencher_loja_id_existentes, migrations.RunPython.noop),
        migrations.RunPython(criar_admin_restaurante_existentes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='funcionario',
            name='loja_id',
            field=models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro'),
        ),
    ]
