"""
Modelos da Homepage - configuração da página inicial do sistema.
Dados editáveis pelo SuperAdmin sem alterar código.
"""
from django.db import models


class HeroSection(models.Model):
    """Seção hero (banner principal) da homepage."""
    titulo = models.CharField(max_length=200)
    subtitulo = models.TextField()
    botao_texto = models.CharField(max_length=100, default='Testar grátis')
    botao_principal_ativo = models.BooleanField(default=True, help_text='Exibir botão principal (ex: Testar grátis)')
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homepage_hero_section'
        ordering = ['ordem', 'id']
        verbose_name = 'Hero Section'
        verbose_name_plural = 'Hero Sections'

    def __str__(self):
        return self.titulo


class Funcionalidade(models.Model):
    """Funcionalidade/destaque exibido na homepage."""
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    icone = models.CharField(max_length=50, blank=True, default='', help_text='Nome do ícone (ex: Users, BarChart) ou emoji')
    imagem = models.URLField(max_length=500, blank=True, null=True, help_text='URL da imagem da funcionalidade (opcional, substitui ícone)')
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homepage_funcionalidade'
        ordering = ['ordem', 'id']
        verbose_name = 'Funcionalidade'
        verbose_name_plural = 'Funcionalidades'

    def __str__(self):
        return self.titulo


class ModuloSistema(models.Model):
    """Módulo/sistema disponível exibido na homepage."""
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    slug = models.SlugField(max_length=50, blank=True, help_text='Ex: crm-vendas, clinica-estetica')
    icone = models.CharField(max_length=50, blank=True)
    imagem = models.URLField(max_length=500, blank=True, null=True, help_text='URL da imagem do módulo (opcional, substitui ícone)')
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homepage_modulo_sistema'
        ordering = ['ordem', 'id']
        verbose_name = 'Módulo do Sistema'
        verbose_name_plural = 'Módulos do Sistema'

    def __str__(self):
        return self.nome


class WhyUsBenefit(models.Model):
    """Benefício exibido na seção 'Por que usar o LWKS?'"""
    titulo = models.CharField(max_length=100, help_text='Ex: Aumente sua produtividade')
    descricao = models.TextField(blank=True, help_text='Descrição detalhada (opcional)')
    icone = models.CharField(max_length=50, blank=True, default='✓', help_text='Emoji ou ícone')
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homepage_whyus_benefit'
        ordering = ['ordem', 'id']
        verbose_name = 'Benefício WhyUs'
        verbose_name_plural = 'Benefícios WhyUs'

    def __str__(self):
        return self.titulo



class HeroImagem(models.Model):
    """Imagens do carrossel do Hero (múltiplas imagens que alternam automaticamente)."""
    imagem = models.URLField(max_length=500, help_text='URL da imagem de fundo do hero')
    titulo = models.CharField(max_length=200, blank=True, help_text='Título opcional para esta imagem')
    ordem = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'homepage_hero_imagem'
        ordering = ['ordem', 'id']
        verbose_name = 'Imagem do Hero'
        verbose_name_plural = 'Imagens do Hero'

    def __str__(self):
        return self.titulo or f'Imagem {self.id}'
