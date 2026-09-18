# Categorias configuráveis de procedimentos (Procedure.categoria continua CharField/slug)

from django.db import migrations, models


CATEGORIAS_PADRAO = [
    ("soroterapia", "Soroterapia", 1),
    ("estetica", "Estética (geral)", 2),
    ("facial", "Facial", 3),
    ("corporal", "Corporal", 4),
    ("capilar", "Capilar", 5),
    ("depilacao", "Depilação", 6),
    ("injetavel", "Injetável", 7),
    ("geral", "Geral", 8),
    ("outro", "Outro", 9),
]


def forwards_seed(apps, schema_editor):
    CategoriaProcedimento = apps.get_model("clinica_beleza", "CategoriaProcedimento")
    Procedure = apps.get_model("clinica_beleza", "Procedure")
    db = schema_editor.connection.alias

    loja_ids = set(
        Procedure.objects.using(db).values_list("loja_id", flat=True).distinct(),
    )
    if not loja_ids:
        return

    for loja_id in loja_ids:
        if not loja_id:
            continue
        for slug, nome, ordem in CATEGORIAS_PADRAO:
            CategoriaProcedimento.objects.using(db).get_or_create(
                loja_id=loja_id,
                slug=slug,
                defaults={"nome": nome, "ordem": ordem, "cor": "#8B3D52", "is_active": True},
            )


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0078_orcamento_item_loja_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoriaProcedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=100, verbose_name="Nome")),
                ("slug", models.SlugField(max_length=50, verbose_name="Slug")),
                ("cor", models.CharField(default="#8B3D52", max_length=7, verbose_name="Cor")),
                ("ordem", models.IntegerField(default=0, verbose_name="Ordem")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativa")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Categoria de procedimento",
                "verbose_name_plural": "Categorias de procedimento",
                "ordering": ["ordem", "nome"],
            },
        ),
        migrations.AddConstraint(
            model_name="categoriaprocedimento",
            constraint=models.UniqueConstraint(
                fields=("loja_id", "slug"),
                name="cb_proc_cat_loja_slug_uniq",
            ),
        ),
        migrations.RunPython(forwards_seed, backwards_noop),
    ]
