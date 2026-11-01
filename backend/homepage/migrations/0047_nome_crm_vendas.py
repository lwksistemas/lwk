from django.db import migrations


TROCAS = (
    ("LWK Sales Cloud — CRM de Vendas", "CRM Vendas"),
    ("CRM de Vendas — LWK Sales Cloud", "CRM Vendas"),
    ("LWK Sales Cloud", "CRM Vendas"),
    ("CRM de Vendas", "CRM Vendas"),
)


def trocar(texto):
    if not texto:
        return texto
    for antigo, novo in TROCAS:
        texto = texto.replace(antigo, novo)
    return texto


def renomear(apps, schema_editor):
    Pagina = apps.get_model("homepage", "PaginaSite")
    Menu = apps.get_model("homepage", "ItemMenu")
    Funcionalidade = apps.get_model("homepage", "Funcionalidade")
    Imagem = apps.get_model("homepage", "HeroImagem")
    Hero = apps.get_model("homepage", "HeroSection")
    Beneficio = apps.get_model("homepage", "WhyUsBenefit")

    for pagina in Pagina.objects.all():
        pagina.titulo = trocar(pagina.titulo)
        pagina.resumo = trocar(pagina.resumo)
        pagina.corpo = trocar(pagina.corpo)
        pagina.itens = trocar(pagina.itens)
        pagina.mensagem_whatsapp = trocar(pagina.mensagem_whatsapp)
        pagina.save(update_fields=["titulo", "resumo", "corpo", "itens", "mensagem_whatsapp"])

    for item in Menu.objects.all():
        novo = trocar(item.rotulo)
        if novo != item.rotulo:
            item.rotulo = novo
            item.save(update_fields=["rotulo"])

    for item in Funcionalidade.objects.all():
        item.titulo = trocar(item.titulo)
        item.descricao = trocar(item.descricao)
        item.save(update_fields=["titulo", "descricao"])

    for item in Imagem.objects.all():
        novo = trocar(item.titulo)
        if novo != item.titulo:
            item.titulo = novo
            item.save(update_fields=["titulo"])

    for item in Hero.objects.all():
        item.titulo = trocar(item.titulo)
        item.subtitulo = trocar(item.subtitulo)
        item.botao_texto = trocar(item.botao_texto)
        item.botao_secundario_texto = trocar(item.botao_secundario_texto)
        item.save(update_fields=["titulo", "subtitulo", "botao_texto", "botao_secundario_texto"])

    for item in Beneficio.objects.all():
        item.titulo = trocar(item.titulo)
        item.descricao = trocar(item.descricao)
        item.save(update_fields=["titulo", "descricao"])


class Migration(migrations.Migration):
    dependencies = [
        ("homepage", "0046_textos_home"),
    ]

    operations = [
        migrations.RunPython(renomear, migrations.RunPython.noop),
    ]
