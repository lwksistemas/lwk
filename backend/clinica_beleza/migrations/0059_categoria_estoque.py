# Generated manually — CategoriaEstoque + FK em ProdutoEstoque

import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


CATEGORIAS_PADRAO = [
    ('injetavel', 'Injetável', 1),
    ('soroterapia', 'Soroterapia', 2),
    ('cosmético', 'Cosmético', 3),
    ('medicamentos', 'Medicamentos', 4),
    ('descartavel', 'Descartável', 5),
    ('equipamento', 'Equipamento', 6),
    ('outro', 'Outro', 7),
]

_ALIASES = {
    'cosmetico': 'cosmético',
    'Medicamentos': 'medicamentos',
    'medicamento': 'medicamentos',
}


def forwards_seed_and_map(apps, schema_editor):
    CategoriaEstoque = apps.get_model('clinica_beleza', 'CategoriaEstoque')
    ProdutoEstoque = apps.get_model('clinica_beleza', 'ProdutoEstoque')
    db = schema_editor.connection.alias

    loja_ids = set(
        ProdutoEstoque.objects.using(db).values_list('loja_id', flat=True).distinct()
    )
    # Também criar categorias para lojas sem produtos (via categorias já existentes no schema)
    # Se não houver produtos, ainda assim seed com loja_id dos registros se houver.
    if not loja_ids:
        # Schema tenant: tenta descobrir loja_id do contexto — se vazio, cria com 0 e ensure corrige.
        # Na prática cada schema de loja tem produtos ou ensure cria depois.
        return

    for loja_id in loja_ids:
        if not loja_id:
            continue
        slug_to_id = {}
        for slug, nome, ordem in CATEGORIAS_PADRAO:
            cat, _ = CategoriaEstoque.objects.using(db).get_or_create(
                loja_id=loja_id,
                slug=slug,
                defaults={'nome': nome, 'ordem': ordem, 'cor': '#8B3D52', 'is_active': True},
            )
            slug_to_id[slug] = cat.id

        for p in ProdutoEstoque.objects.using(db).filter(loja_id=loja_id):
            raw = (getattr(p, 'categoria_slug_tmp', None) or '').strip()
            # During migration the old CharField was renamed to categoria_slug_tmp
            raw = _ALIASES.get(raw, raw) or 'outro'
            cat_id = slug_to_id.get(raw) or slug_to_id.get('outro')
            if cat_id:
                ProdutoEstoque.objects.using(db).filter(pk=p.pk).update(categoria_id=cat_id)


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clinica_beleza', '0058_payment_status_draft'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaEstoque',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('loja_id', models.IntegerField(db_index=True, help_text='ID da loja proprietária deste registro')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('slug', models.SlugField(max_length=50, verbose_name='Slug')),
                ('cor', models.CharField(default='#8B3D52', max_length=7, verbose_name='Cor')),
                ('ordem', models.IntegerField(default=0, verbose_name='Ordem')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
            ],
            options={
                'verbose_name': 'Categoria de estoque',
                'verbose_name_plural': 'Categorias de estoque',
                'ordering': ['ordem', 'nome'],
            },
        ),
        migrations.AddConstraint(
            model_name='categoriaestoque',
            constraint=models.UniqueConstraint(
                fields=('loja_id', 'slug'),
                name='cb_estoque_cat_loja_slug_uniq',
            ),
        ),
        # Renomeia CharField antigo para preservar valores durante o map
        migrations.RenameField(
            model_name='produtoestoque',
            old_name='categoria',
            new_name='categoria_slug_tmp',
        ),
        migrations.AddField(
            model_name='produtoestoque',
            name='categoria',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='produtos',
                to='clinica_beleza.categoriaestoque',
                verbose_name='Categoria',
            ),
        ),
        migrations.RunPython(forwards_seed_and_map, backwards_noop),
        migrations.RemoveField(
            model_name='produtoestoque',
            name='categoria_slug_tmp',
        ),
    ]
