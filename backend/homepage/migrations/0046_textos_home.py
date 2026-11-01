from django.db import migrations


PAGINAS = [
    {
        "slug": "home-solucoes",
        "titulo": "Nossas soluções",
        "resumo": "Dois sistemas prontos. O detalhe de cada um fica na página do produto.",
        "corpo": "",
        "itens": "",
        "mensagem_whatsapp": "",
    },
    {
        "slug": "home-crm",
        "titulo": "LWK Sales Cloud — CRM de Vendas",
        "resumo": "Para equipes comerciais acompanharem o cliente do primeiro contato ao fechamento.",
        "corpo": "",
        "itens": "Leads e funil no mesmo lugar\nPropostas e contratos em andamento\nRelatórios do comercial",
        "mensagem_whatsapp": "",
    },
    {
        "slug": "home-clinica",
        "titulo": "Gestão para Clínicas de Estética",
        "resumo": "Para a rotina da clínica: quem chega, o que foi feito e como está o dia.",
        "corpo": "",
        "itens": "Agenda do dia\nProcedimentos e protocolos\nEstoque e financeiro da clínica",
        "mensagem_whatsapp": "",
    },
    {
        "slug": "home-personalizados",
        "titulo": "Desenvolvimento de sistemas personalizados",
        "resumo": "Quando a operação não cabe no CRM nem na clínica, a LWK desenvolve o software sob medida. Não há sistema pronto para outros segmentos.",
        "corpo": "Solicitar orçamento|/solucoes/personalizados",
        "itens": "A operação primeiro|O levantamento parte da rotina real da empresa.\nFeito para o processo|Telas e regras do jeito que a equipe trabalha.\nDepois da entrega|Suporte para o sistema continuar em uso.",
        "mensagem_whatsapp": "",
    },
    {
        "slug": "home-beneficios",
        "titulo": "Benefícios e diferenciais",
        "resumo": "",
        "corpo": "",
        "itens": "",
        "mensagem_whatsapp": "",
    },
    {
        "slug": "home-planos",
        "titulo": "Planos e proposta",
        "resumo": "Os valores publicados são os da gestão para clínicas. CRM e sistemas personalizados seguem sob consulta.",
        "corpo": "",
        "itens": "Gestão para clínicas|Planos com valores publicados, a partir de R$ 99,90 por mês.|/planos|Ver planos\nCRM de Vendas|Consulte nossas condições comerciais.|/contato|Solicitar proposta\nSistema personalizado|O valor depende do que a operação precisa.|/solucoes/personalizados|Pedir orçamento",
        "mensagem_whatsapp": "",
    },
    {
        "slug": "home-contato",
        "titulo": "Contato e demonstração",
        "resumo": "Escolha o CRM, a clínica ou um sistema personalizado. A mensagem do WhatsApp já leva o produto, o nome e a empresa.",
        "corpo": "",
        "itens": "",
        "mensagem_whatsapp": "",
    },
]

BENEFICIOS = [
    ("Tecnologia e segurança", "Sistemas feitos para o uso diário, com cuidado sobre os dados."),
    ("Suporte especializado", "Quem atende conhece o produto que a empresa contratou."),
    ("Na nuvem", "A equipe acessa de onde estiver, no computador ou no celular."),
    ("Sob medida quando precisa", "O pronto cobre clínica e comercial. O resto vira projeto."),
]


def semear(apps, schema_editor):
    Pagina = apps.get_model("homepage", "PaginaSite")
    Why = apps.get_model("homepage", "WhyUsBenefit")
    for dados in PAGINAS:
        Pagina.objects.get_or_create(slug=dados["slug"], defaults=dados)
    if not Why.objects.exists():
        for ordem, (titulo, descricao) in enumerate(BENEFICIOS, start=1):
            Why.objects.create(titulo=titulo, descricao=descricao, icone="", ordem=ordem, ativo=True)


class Migration(migrations.Migration):
    dependencies = [
        ("homepage", "0045_menu_mensagem_comercial"),
    ]

    operations = [
        migrations.RunPython(semear, migrations.RunPython.noop),
    ]
