"""Modelos da Homepage - configuração da página inicial do sistema.
Dados editáveis pelo SuperAdmin sem alterar código.
"""
from django.db import models


class HeroSection(models.Model):
    """Seção hero (banner principal) da homepage."""

    titulo = models.CharField(max_length=200)
    subtitulo = models.TextField()
    selo = models.CharField(
        max_length=80,
        blank=True,
        default="Software House",
        help_text="Etiqueta acima do título, ex.: Software House",
    )
    botao_texto = models.CharField(max_length=100, default="Conheça nossas soluções")
    botao_url = models.CharField(
        max_length=300,
        blank=True,
        default="#destaques",
        help_text="Link do botão principal",
    )
    botao_principal_ativo = models.BooleanField(default=True, help_text="Exibir botão principal (ex: Testar grátis)")
    botao_secundario_texto = models.CharField(
        max_length=100,
        blank=True,
        default="Solicite uma demonstração",
    )
    botao_secundario_url = models.CharField(
        max_length=300,
        blank=True,
        default="#contato",
        help_text="Link do segundo botão",
    )
    botao_secundario_ativo = models.BooleanField(default=True)
    intervalo_carrossel = models.PositiveSmallIntegerField(
        default=5,
        help_text="Segundos entre as telas do notebook",
    )
    titulo_destaque = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Segunda linha do título, em azul. Ex.: para sua empresa.",
    )
    fonte_familia = models.CharField(
        max_length=20,
        default="inter",
        choices=[
            ("inter", "Inter"),
            ("poppins", "Poppins"),
            ("montserrat", "Montserrat"),
            ("nunito", "Nunito"),
            ("dm", "DM Sans"),
            ("outfit", "Outfit"),
        ],
    )
    fonte_tamanho = models.CharField(
        max_length=20,
        default="normal",
        choices=[
            ("pequeno", "Pequena"),
            ("normal", "Normal"),
            ("grande", "Grande"),
            ("maior", "Muito grande"),
        ],
    )
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_hero_section"
        ordering = ["ordem", "id"]
        verbose_name = "Hero Section"
        verbose_name_plural = "Hero Sections"

    def __str__(self):
        return self.titulo


class Funcionalidade(models.Model):
    """Funcionalidade/destaque exibido na homepage."""

    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    icone = models.CharField(max_length=50, blank=True, default="", help_text="Nome do ícone (ex: Users, BarChart) ou emoji")
    link = models.CharField(max_length=300, blank=True, default="", help_text="Página aberta ao clicar no cartão")
    imagem = models.URLField(max_length=500, blank=True, null=True, help_text="URL da imagem da funcionalidade (opcional, substitui ícone)")
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_funcionalidade"
        ordering = ["ordem", "id"]
        verbose_name = "Funcionalidade"
        verbose_name_plural = "Funcionalidades"

    def __str__(self):
        return self.titulo


class ModuloSistema(models.Model):
    """Módulo/sistema disponível exibido na homepage."""

    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    slug = models.SlugField(max_length=50, blank=True, help_text="Ex: crm-vendas, clinica-estetica")
    icone = models.CharField(max_length=50, blank=True)
    imagem = models.URLField(max_length=500, blank=True, null=True, help_text="URL da imagem do módulo (opcional, substitui ícone)")
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_modulo_sistema"
        ordering = ["ordem", "id"]
        verbose_name = "Módulo do Sistema"
        verbose_name_plural = "Módulos do Sistema"

    def __str__(self):
        return self.nome


class WhyUsBenefit(models.Model):
    """Benefício exibido na seção 'Por que usar o LWKS?'"""

    titulo = models.CharField(max_length=100, help_text="Ex: Aumente sua produtividade")
    descricao = models.TextField(blank=True, help_text="Descrição detalhada (opcional)")
    icone = models.CharField(max_length=50, blank=True, default="✓", help_text="Emoji ou ícone")
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_whyus_benefit"
        ordering = ["ordem", "id"]
        verbose_name = "Benefício WhyUs"
        verbose_name_plural = "Benefícios WhyUs"

    def __str__(self):
        return self.titulo



class EmpresaConfig(models.Model):
    """Dados da empresa exibidos no rodapé e botão WhatsApp da homepage."""

    nome_empresa = models.CharField(max_length=200, default="LWK Sistemas")
    cnpj = models.CharField(max_length=20, blank=True, default="", help_text="CNPJ formatado (ex: 00.000.000/0001-00)")
    endereco = models.CharField(max_length=300, blank=True, default="", help_text="Endereço completo")
    telefone_whatsapp = models.CharField(max_length=20, blank=True, default="", help_text="Número WhatsApp com DDD (ex: 5511999999999)")
    mensagem_whatsapp = models.CharField(
        max_length=300,
        blank=True,
        default="Olá! Acessei o site da LWK Sistemas e gostaria de conhecer melhor as soluções oferecidas.",
        help_text="Mensagem padrão ao clicar no WhatsApp",
    )
    email_contato = models.EmailField(blank=True, default="", help_text="Email de contato da empresa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_empresa_config"
        verbose_name = "Configuração da Empresa"
        verbose_name_plural = "Configurações da Empresa"

    def __str__(self):
        return self.nome_empresa


class HeroImagem(models.Model):
    """Imagens do carrossel do Hero (múltiplas imagens que alternam automaticamente)."""

    imagem = models.URLField(
        max_length=500,
        help_text="Captura anonimizada da tela, sem nomes de clientes ou pacientes",
    )
    titulo = models.CharField(max_length=200, blank=True, help_text="Etiqueta sobre a tela, ex.: CRM Vendas")
    link = models.CharField(max_length=300, blank=True, default="", help_text="Página aberta ao clicar na tela")
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_hero_imagem"
        ordering = ["ordem", "id"]
        verbose_name = "Imagem do Hero"
        verbose_name_plural = "Imagens do Hero"

    def __str__(self):
        return self.titulo or f"Imagem {self.id}"


class ItemMenu(models.Model):
    """Item dos menus Soluções e Segmentos."""

    GRUPO_SOLUCOES = "solucoes"
    GRUPO_SEGMENTOS = "segmentos"
    GRUPOS = [
        (GRUPO_SOLUCOES, "Soluções"),
        (GRUPO_SEGMENTOS, "Segmentos"),
    ]

    grupo = models.CharField(max_length=20, choices=GRUPOS)
    rotulo = models.CharField(max_length=120)
    url = models.CharField(max_length=300)
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)

    class Meta:
        db_table = "homepage_item_menu"
        ordering = ["grupo", "ordem", "id"]
        verbose_name = "Item de menu"
        verbose_name_plural = "Itens de menu"

    def __str__(self):
        return f"{self.grupo}: {self.rotulo}"


class PaginaSite(models.Model):
    """Texto das páginas institucionais (produtos, segmentos, contato, demonstração)."""

    slug = models.SlugField(max_length=60, unique=True)
    titulo = models.CharField(max_length=200)
    resumo = models.TextField(blank=True, default="")
    corpo = models.TextField(blank=True, default="")
    itens = models.TextField(blank=True, default="", help_text="Um destaque por linha")
    mensagem_whatsapp = models.CharField(max_length=400, blank=True, default="")
    imagem = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Foto do cartão na home. Vazio mantém a imagem atual.",
    )
    ativo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "homepage_pagina_site"
        ordering = ["slug"]
        verbose_name = "Página do site"
        verbose_name_plural = "Páginas do site"

    def __str__(self):
        return self.titulo


class SolicitacaoContato(models.Model):
    """Pedido enviado pelo formulário de contato ou demonstração."""

    nome = models.CharField(max_length=120)
    empresa = models.CharField(max_length=160, blank=True, default="")
    whatsapp = models.CharField(max_length=20)
    produto = models.CharField(max_length=40)
    mensagem = models.TextField()
    origem = models.CharField(max_length=40, default="contato")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "homepage_solicitacao_contato"
        ordering = ["-created_at"]
        verbose_name = "Solicitação do site"
        verbose_name_plural = "Solicitações do site"

    def __str__(self):
        return f"{self.nome} — {self.produto}"
