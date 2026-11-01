from django.db import migrations, models


MENSAGEM_SITE = "Olá! Acessei o site da LWK Sistemas e gostaria de conhecer melhor as soluções oferecidas."
MENSAGENS_ANTIGAS = [
    "Olá! Gostaria de saber mais sobre o LWK Sistemas.",
    "Olá! Conheci a LWK Sistemas pelo site e gostaria de falar com o comercial.",
]

PAGINAS = {
    "crm-vendas": "Olá! Gostaria de agendar uma demonstração do LWK Sales Cloud — CRM de Vendas.",
    "clinicas-estetica": "Olá! Gostaria de agendar uma demonstração da Gestão para Clínicas de Estética.",
}


def ajustar(apps, schema_editor):
    EmpresaConfig = apps.get_model("homepage", "EmpresaConfig")
    ItemMenu = apps.get_model("homepage", "ItemMenu")
    PaginaSite = apps.get_model("homepage", "PaginaSite")

    EmpresaConfig.objects.filter(mensagem_whatsapp__in=MENSAGENS_ANTIGAS).update(mensagem_whatsapp=MENSAGEM_SITE)
    ItemMenu.objects.filter(grupo="solucoes", rotulo="CRM de Vendas").update(rotulo="CRM de Vendas — LWK Sales Cloud")
    ItemMenu.objects.filter(grupo="segmentos", rotulo="Equipes Comerciais").update(rotulo="Gestão Comercial e Equipes de Vendas")
    for slug, mensagem in PAGINAS.items():
        PaginaSite.objects.filter(slug=slug).update(mensagem_whatsapp=mensagem)


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0044_site_menu_paginas_contato"),
    ]

    operations = [
        migrations.AlterField(
            model_name="empresaconfig",
            name="mensagem_whatsapp",
            field=models.CharField(
                blank=True,
                default=MENSAGEM_SITE,
                help_text="Mensagem padrão ao clicar no WhatsApp",
                max_length=300,
            ),
        ),
        migrations.RunPython(ajustar, migrations.RunPython.noop),
    ]
