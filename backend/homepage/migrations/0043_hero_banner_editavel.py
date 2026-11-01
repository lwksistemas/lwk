from django.db import migrations, models


def alinhar_textos_antigos(apps, schema_editor):
    """Troca o texto padrão antigo pelo banner da página, sem mexer em texto já personalizado."""
    HeroSection = apps.get_model("homepage", "HeroSection")
    titulos_antigos = {
        "",
        "Controle total da sua empresa em um único sistema",
        "Testar Gratuitamente",
    }
    for hero in HeroSection.objects.all():
        mudou = False
        if (hero.titulo or "").strip() in titulos_antigos:
            hero.titulo = "Soluções de software para o seu negócio."
            mudou = True
        subtitulo = (hero.subtitulo or "").strip()
        if subtitulo in {
            "",
            "Gerencie clientes, vendas, financeiro e relatórios em um CRM moderno e fácil de usar.",
        }:
            hero.subtitulo = (
                "Desenvolvemos sistemas e soluções personalizadas para clínicas de estética, "
                "CRM de vendas e diversos outros segmentos, com tecnologia, segurança e suporte especializado."
            )
            mudou = True
        if (hero.botao_texto or "").strip() in {"", "Testar grátis", "Testar Gratuitamente"}:
            hero.botao_texto = "Conheça nossas soluções"
            mudou = True
        if mudou:
            hero.save(update_fields=["titulo", "subtitulo", "botao_texto"])


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0042_empresaconfig"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="selo",
            field=models.CharField(
                blank=True,
                default="Software House",
                help_text="Etiqueta acima do título, ex.: Software House",
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name="herosection",
            name="botao_url",
            field=models.CharField(
                blank=True,
                default="#destaques",
                help_text="Link do botão principal",
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name="herosection",
            name="botao_secundario_texto",
            field=models.CharField(blank=True, default="Solicite uma demonstração", max_length=100),
        ),
        migrations.AddField(
            model_name="herosection",
            name="botao_secundario_url",
            field=models.CharField(
                blank=True,
                default="#contato",
                help_text="Link do segundo botão",
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name="herosection",
            name="botao_secundario_ativo",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="herosection",
            name="botao_texto",
            field=models.CharField(default="Conheça nossas soluções", max_length=100),
        ),
        migrations.RunPython(alinhar_textos_antigos, migrations.RunPython.noop),
    ]
