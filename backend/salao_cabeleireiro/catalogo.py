"""Serviços iniciais para o salão começar com a agenda utilizável."""
from decimal import Decimal

from .models import Servico

CATALOGO_INICIAL = (
    ("Corte feminino", "Corte", 60, "70.00"),
    ("Corte masculino", "Corte", 40, "50.00"),
    ("Escova e finalização", "Finalização", 45, "80.00"),
    ("Coloração", "Cor", 120, "180.00"),
    ("Hidratação", "Tratamento", 50, "90.00"),
    ("Mechas / luzes", "Cor", 150, "220.00"),
    ("Barba", "Barba", 30, "40.00"),
)


def garantir_catalogo_inicial():
    if Servico.objects.exists():
        return
    for nome, categoria, duracao, preco in CATALOGO_INICIAL:
        Servico.objects.create(
            nome=nome,
            categoria=categoria,
            duracao_minutos=duracao,
            preco=Decimal(preco),
            descricao="",
        )
