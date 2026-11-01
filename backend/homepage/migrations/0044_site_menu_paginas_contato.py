from django.db import migrations, models


PAGINAS = [
    {
        "slug": "crm-vendas",
        "titulo": "LWK Sales Cloud — CRM de Vendas",
        "resumo": "Organize leads, funil, propostas, contratos, comissões e relatórios comerciais em um só lugar.",
        "corpo": "O CRM de Vendas acompanha o comercial do primeiro contato até o fechamento. A equipe vê o que está em andamento, o que precisa de retorno e quanto cada venda representa.",
        "itens": "Leads\nFunil de vendas\nOportunidades\nPropostas\nContratos\nComissões\nRelatórios comerciais",
        "mensagem_whatsapp": "Olá! Conheci a LWK Sistemas pelo site e gostaria de agendar uma demonstração do CRM de Vendas.",
    },
    {
        "slug": "clinicas-estetica",
        "titulo": "Gestão para Clínicas de Estética",
        "resumo": "Agenda, clientes, procedimentos, protocolos, estoque, financeiro e relatórios da clínica.",
        "corpo": "O sistema da clínica reúne a operação do dia: quem chega, qual procedimento foi feito, o que saiu do estoque e como está o financeiro.",
        "itens": "Agenda\nClientes\nProcedimentos\nProtocolos\nEstoque\nFinanceiro\nRelatórios",
        "mensagem_whatsapp": "Olá! Conheci a LWK Sistemas pelo site e gostaria de agendar uma demonstração do sistema para Clínicas de Estética.",
    },
    {
        "slug": "personalizados",
        "titulo": "Sistemas personalizados",
        "resumo": "Software sob medida para a operação da sua empresa.",
        "corpo": "Quando o processo não cabe num sistema pronto, a LWK desenvolve a solução em cima da rotina real: telas, regras e relatórios do jeito que a operação precisa.",
        "itens": "Levantamento do processo\nTelas e regras sob medida\nIntegração com a operação atual\nSuporte depois da entrega",
        "mensagem_whatsapp": "Olá! Conheci a LWK Sistemas pelo site e gostaria de conversar sobre um sistema personalizado.",
    },
    {
        "slug": "segmentos",
        "titulo": "Segmentos atendidos",
        "resumo": "A LWK atende empresas de diferentes portes e áreas, com produtos prontos e projetos sob medida.",
        "corpo": "Clínicas de estética e equipes comerciais já têm sistema próprio. Outros segmentos entram como projeto personalizado, desenhado conforme a necessidade.",
        "itens": "Clínicas de estética\nEquipes comerciais\nProjetos para outros segmentos",
        "mensagem_whatsapp": "Olá! Conheci a LWK Sistemas pelo site e gostaria de saber se atendem o meu segmento.",
    },
    {
        "slug": "planos",
        "titulo": "Planos",
        "resumo": "Valores e o que entra em cada módulo, quando estiverem publicados.",
        "corpo": "Escolha o módulo para ver os planos disponíveis. Se o valor ainda não estiver na página, peça uma demonstração e montamos a proposta.",
        "itens": "",
        "mensagem_whatsapp": "Olá! Conheci a LWK Sistemas pelo site e gostaria de conhecer os planos.",
    },
    {
        "slug": "contato",
        "titulo": "Contato",
        "resumo": "Fale com a LWK pelo formulário, telefone ou WhatsApp.",
        "corpo": "Conte o que a empresa precisa. Retornamos pelo WhatsApp informado.",
        "itens": "",
        "mensagem_whatsapp": "Olá! Conheci a LWK Sistemas pelo site e gostaria de falar com o comercial.",
    },
    {
        "slug": "demonstracao",
        "titulo": "Solicitar demonstração",
        "resumo": "Escolha o produto e peça uma apresentação.",
        "corpo": "Diga qual sistema interessa. A mensagem do WhatsApp já cita o produto escolhido.",
        "itens": "",
        "mensagem_whatsapp": "Olá! Conheci a LWK Sistemas pelo site e gostaria de agendar uma demonstração.",
    },
]

MENUS = [
    ("solucoes", "CRM de Vendas", "/solucoes/crm-vendas", 1),
    ("solucoes", "Gestão para Clínicas de Estética", "/solucoes/clinicas-estetica", 2),
    ("solucoes", "Sistemas Personalizados", "/solucoes/personalizados", 3),
    ("segmentos", "Clínicas de Estética", "/solucoes/clinicas-estetica", 1),
    ("segmentos", "Equipes Comerciais", "/solucoes/crm-vendas", 2),
    ("segmentos", "Outros Segmentos", "/segmentos", 3),
]

CARTOES = {
    "Clínicas de Estética": "/solucoes/clinicas-estetica",
    "CRM de Vendas": "/solucoes/crm-vendas",
    "Sistemas Personalizados": "/solucoes/personalizados",
    "Todos os Segmentos": "/segmentos",
}


def semear(apps, schema_editor):
    HeroSection = apps.get_model("homepage", "HeroSection")
    Funcionalidade = apps.get_model("homepage", "Funcionalidade")
    ItemMenu = apps.get_model("homepage", "ItemMenu")
    PaginaSite = apps.get_model("homepage", "PaginaSite")
    EmpresaConfig = apps.get_model("homepage", "EmpresaConfig")

    for hero in HeroSection.objects.all():
        campos = []
        if (hero.botao_url or "") in ("", "#destaques"):
            hero.botao_url = "#solucoes"
            campos.append("botao_url")
        if (hero.botao_secundario_url or "") in ("", "#contato"):
            hero.botao_secundario_url = "/demonstracao"
            campos.append("botao_secundario_url")
        if campos:
            hero.save(update_fields=campos)

    if not Funcionalidade.objects.exists():
        for ordem, (titulo, link) in enumerate(CARTOES.items(), start=1):
            descricoes = {
                "Clínicas de Estética": "Gestão completa da sua clínica",
                "CRM de Vendas": "Organize seus leads, vendas e relacionamento",
                "Sistemas Personalizados": "Soluções sob medida para a sua operação",
                "Todos os Segmentos": "Atendemos empresas de diferentes áreas e portes",
            }
            Funcionalidade.objects.create(
                titulo=titulo,
                descricao=descricoes[titulo],
                link=link,
                ordem=ordem,
                ativo=True,
            )
    else:
        for titulo, link in CARTOES.items():
            Funcionalidade.objects.filter(titulo=titulo, link="").update(link=link)

    if not ItemMenu.objects.exists():
        for grupo, rotulo, url, ordem in MENUS:
            ItemMenu.objects.create(grupo=grupo, rotulo=rotulo, url=url, ordem=ordem, ativo=True)

    for dados in PAGINAS:
        PaginaSite.objects.get_or_create(slug=dados["slug"], defaults=dados)

    mensagem_antiga = "Olá! Gostaria de saber mais sobre o LWK Sistemas."
    mensagem_nova = "Olá! Conheci a LWK Sistemas pelo site e gostaria de falar com o comercial."
    EmpresaConfig.objects.filter(mensagem_whatsapp=mensagem_antiga).update(mensagem_whatsapp=mensagem_nova)


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0043_hero_banner_editavel"),
    ]

    operations = [
        migrations.AddField(
            model_name="herosection",
            name="intervalo_carrossel",
            field=models.PositiveSmallIntegerField(default=5, help_text="Segundos entre as telas do notebook"),
        ),
        migrations.AddField(
            model_name="heroimagem",
            name="link",
            field=models.CharField(blank=True, default="", help_text="Página aberta ao clicar na tela", max_length=300),
        ),
        migrations.AddField(
            model_name="funcionalidade",
            name="link",
            field=models.CharField(blank=True, default="", help_text="Página aberta ao clicar no cartão", max_length=300),
        ),
        migrations.CreateModel(
            name="ItemMenu",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("grupo", models.CharField(choices=[("solucoes", "Soluções"), ("segmentos", "Segmentos")], max_length=20)),
                ("rotulo", models.CharField(max_length=120)),
                ("url", models.CharField(max_length=300)),
                ("ordem", models.PositiveIntegerField(default=0)),
                ("ativo", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Item de menu",
                "verbose_name_plural": "Itens de menu",
                "db_table": "homepage_item_menu",
                "ordering": ["grupo", "ordem", "id"],
            },
        ),
        migrations.CreateModel(
            name="PaginaSite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=60, unique=True)),
                ("titulo", models.CharField(max_length=200)),
                ("resumo", models.TextField(blank=True, default="")),
                ("corpo", models.TextField(blank=True, default="")),
                ("itens", models.TextField(blank=True, default="", help_text="Um destaque por linha")),
                ("mensagem_whatsapp", models.CharField(blank=True, default="", max_length=400)),
                ("ativo", models.BooleanField(default=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Página do site",
                "verbose_name_plural": "Páginas do site",
                "db_table": "homepage_pagina_site",
                "ordering": ["slug"],
            },
        ),
        migrations.CreateModel(
            name="SolicitacaoContato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=120)),
                ("empresa", models.CharField(blank=True, default="", max_length=160)),
                ("whatsapp", models.CharField(max_length=20)),
                ("produto", models.CharField(max_length=40)),
                ("mensagem", models.TextField()),
                ("origem", models.CharField(default="contato", max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Solicitação do site",
                "verbose_name_plural": "Solicitações do site",
                "db_table": "homepage_solicitacao_contato",
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(semear, migrations.RunPython.noop),
    ]
