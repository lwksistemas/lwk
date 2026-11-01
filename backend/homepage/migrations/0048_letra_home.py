from django.db import migrations, models


def ajustar_banner(apps, schema_editor):
    Hero = apps.get_model("homepage", "HeroSection")
    hero = Hero.objects.filter(ativo=True).order_by("ordem", "id").first()
    if hero is None:
        return
    hero.titulo = "Soluções de software"
    hero.titulo_destaque = "para sua empresa."
    hero.botao_texto = "Solicite uma demonstração"
    hero.botao_url = "/demonstracao"
    hero.botao_principal_ativo = True
    hero.botao_secundario_texto = "Conheça nossas soluções"
    hero.botao_secundario_url = "#solucoes"
    hero.botao_secundario_ativo = True
    hero.fonte_familia = "inter"
    hero.fonte_tamanho = "normal"
    hero.save()


class Migration(migrations.Migration):
    dependencies = [
        ("homepage", "0047_nome_crm_vendas"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="titulo_destaque",
            field=models.CharField(blank=True, default="", help_text="Segunda linha do título, em azul. Ex.: para sua empresa.", max_length=120),
        ),
        migrations.AddField(
            model_name="herosection",
            name="fonte_familia",
            field=models.CharField(
                choices=[
                    ("inter", "Inter"),
                    ("poppins", "Poppins"),
                    ("montserrat", "Montserrat"),
                    ("nunito", "Nunito"),
                    ("dm", "DM Sans"),
                    ("outfit", "Outfit"),
                ],
                default="inter",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="herosection",
            name="fonte_tamanho",
            field=models.CharField(
                choices=[
                    ("pequeno", "Pequena"),
                    ("normal", "Normal"),
                    ("grande", "Grande"),
                    ("maior", "Muito grande"),
                ],
                default="normal",
                max_length=20,
            ),
        ),
        migrations.RunPython(ajustar_banner, migrations.RunPython.noop),
    ]
