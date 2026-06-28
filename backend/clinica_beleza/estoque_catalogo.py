"""
Catálogo padrão de produtos do estoque — Clínica da Beleza (estética + soroterapia).

Nomes comerciais usados em clínicas de estética e IV therapy no Brasil.

Consumidores: `estoque_catalogo_service.py` e management commands
(`ensure_estoque_catalogo`, `popular_loja_clinica_beleza`).
Este arquivo define apenas dados de seed — não contém lógica de negócio em runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EstoqueCatalogoItem:
    nome: str
    categoria: str
    marca: str = ''
    unidade_medida: str = 'unidade'
    quantidade_minima: Decimal = Decimal('1')
    observacoes: str = ''


def estoque_catalogo_defaults(item: EstoqueCatalogoItem) -> dict:
    return {
        'categoria': item.categoria,
        'marca': item.marca,
        'unidade_medida': item.unidade_medida,
        'quantidade_atual': Decimal('0'),
        'quantidade_minima': item.quantidade_minima,
        'preco_custo': Decimal('0'),
        'preco_venda': Decimal('0'),
        'observacoes': item.observacoes,
        'is_active': True,
    }


# Protocolos comerciais de soroterapia (alinhados ao catálogo de procedimentos)
_SORO = 'soroterapia'
_INJ = 'injetavel'
_DESC = 'descartavel'
_COSM = 'cosmético'
_MED = 'medicamentos'

ESTOQUE_CATALOGO: list[EstoqueCatalogoItem] = [
    # —— Soroterapia: protocolos comerciais ——
    EstoqueCatalogoItem(
        'Immunity Boost IV — Kit Imunidade',
        _SORO, 'Genérico', 'kit', Decimal('2'),
        'Vitamina C + Zinco + Selênio. Protocolo comercial de imunidade.',
    ),
    EstoqueCatalogoItem(
        'Energy & Focus IV — Kit Energia e Foco',
        _SORO, 'Genérico', 'kit', Decimal('2'),
        'Complexo B + Carnitina + Taurina.',
    ),
    EstoqueCatalogoItem(
        'Detox Metabolic IV — Kit Detox',
        _SORO, 'Genérico', 'kit', Decimal('2'),
    ),
    EstoqueCatalogoItem(
        'Hydration Balance IV — Kit Hidratação',
        _SORO, 'Genérico', 'kit', Decimal('3'),
        'Soro fisiológico + eletrólitos.',
    ),
    EstoqueCatalogoItem(
        'High Dose Vitamina C EV — 500mg/5ml',
        _SORO, 'Hypofarma', 'ampola', Decimal('10'),
    ),
    EstoqueCatalogoItem(
        'Glutamina Recovery IV — 200mg/ml',
        _SORO, 'Genérico', 'ampola', Decimal('10'),
    ),
    EstoqueCatalogoItem(
        'NAD+ Longevity EV — 250mg',
        _SORO, 'Genérico', 'frasco', Decimal('2'),
    ),
    EstoqueCatalogoItem(
        'Myers Cocktail Original — Kit Completo',
        _SORO, 'Genérico', 'kit', Decimal('2'),
        'Magnésio + B6 + B12 + Vit C + Cálcio.',
    ),
    EstoqueCatalogoItem(
        'Beauty Glow IV — Kit Beleza e Pele',
        _SORO, 'Genérico', 'kit', Decimal('2'),
        'Biotina + Vitamina C + Zinco.',
    ),
    EstoqueCatalogoItem(
        'Sleep & Calm IV — Kit Sono e Relaxamento',
        _SORO, 'Genérico', 'kit', Decimal('2'),
        'Magnésio + Glicina.',
    ),
    EstoqueCatalogoItem(
        'Slim Metabolism IV — Kit Emagrecimento',
        _SORO, 'Genérico', 'kit', Decimal('2'),
        'MIC (Metionina + Inositol + Colina) + L-Carnitina.',
    ),
    EstoqueCatalogoItem(
        'Anti-Aging Premium IV — Kit Anti-Aging',
        _SORO, 'Genérico', 'kit', Decimal('2'),
        'NAD+ + Glutationa.',
    ),
    EstoqueCatalogoItem(
        'Post-Workout Recovery IV — Kit Pós-Treino',
        _SORO, 'Genérico', 'kit', Decimal('2'),
    ),
    EstoqueCatalogoItem(
        'Hangover Relief IV — Kit Repouso e Ressaca',
        _SORO, 'Genérico', 'kit', Decimal('2'),
    ),
    # —— Soroterapia: insumos base ——
    EstoqueCatalogoItem('Soro Fisiológico 0,9% — 500ml', _SORO, 'Baxter', 'frasco', Decimal('10')),
    EstoqueCatalogoItem('Soro Glicosado 5% — 500ml', _SORO, 'Baxter', 'frasco', Decimal('5')),
    EstoqueCatalogoItem('Água para Injeção — 10ml', _SORO, 'Halex Istar', 'ampola', Decimal('20')),
    EstoqueCatalogoItem('Complexo B EV (B1+B6+B12)', _SORO, 'Hypofarma', 'ampola', Decimal('10')),
    EstoqueCatalogoItem('Vitamina B12 Cianocobalamina EV', _SORO, 'Hypofarma', 'ampola', Decimal('10')),
    EstoqueCatalogoItem('Magnésio Sulfato EV 50%', _SORO, 'Hypofarma', 'ampola', Decimal('10')),
    EstoqueCatalogoItem('Zinco EV', _SORO, 'Hypofarma', 'ampola', Decimal('10')),
    EstoqueCatalogoItem('Selênio EV', _SORO, 'Genérico', 'ampola', Decimal('5')),
    EstoqueCatalogoItem('L-Carnitina EV 1g', _SORO, 'Genérico', 'ampola', Decimal('10')),
    EstoqueCatalogoItem('Taurina EV', _SORO, 'Genérico', 'ampola', Decimal('10')),
    EstoqueCatalogoItem('Glicina EV', _SORO, 'Genérico', 'ampola', Decimal('10')),
    EstoqueCatalogoItem('Glutationa (Glutathione) EV', _SORO, 'Genérico', 'ampola', Decimal('5')),
    EstoqueCatalogoItem('Coenzima Q10 EV', _SORO, 'Genérico', 'ampola', Decimal('5')),
    EstoqueCatalogoItem('Equipo Macrogotas Soroterapia', _SORO, 'Descarpack', 'unidade', Decimal('20')),
    # —— Injetáveis estética ——
    EstoqueCatalogoItem('Dysport 500U — Toxina Botulínica', _INJ, 'Ipsen', 'frasco', Decimal('1')),
    EstoqueCatalogoItem('Botox 100U — Toxina Botulínica', _INJ, 'Allergan', 'frasco', Decimal('1')),
    EstoqueCatalogoItem('Juvederm Ultra XC 1ml', _INJ, 'Allergan', 'seringa', Decimal('2')),
    EstoqueCatalogoItem('Restylane Kysse 1ml', _INJ, 'Galderma', 'seringa', Decimal('2')),
    EstoqueCatalogoItem('Belotero Balance 1ml', _INJ, 'Merz', 'seringa', Decimal('2')),
    EstoqueCatalogoItem('Sculptra — Bioestimulador', _INJ, 'Galderma', 'frasco', Decimal('1')),
    EstoqueCatalogoItem('Radiesse 1,5ml — Bioestimulador', _INJ, 'Merz', 'seringa', Decimal('1')),
    EstoqueCatalogoItem('Profhilo — Skinbooster', _INJ, 'IBSA', 'seringa', Decimal('2')),
    EstoqueCatalogoItem('Ácido Glicólico 70% — Peeling', _INJ, 'Mesoestetic', 'frasco', Decimal('1')),
    EstoqueCatalogoItem('DMAE Ampolas — Flacidez', _INJ, 'Mesoestetic', 'ampola', Decimal('5')),
    # —— Descartáveis ——
    EstoqueCatalogoItem('Agulha Hipodérmica 30x7mm — Caixa 100un', _DESC, 'Descarpack', 'caixa', Decimal('2')),
    EstoqueCatalogoItem('Seringa Descartável 3ml — Caixa 100un', _DESC, 'Descarpack', 'caixa', Decimal('2')),
    EstoqueCatalogoItem('Seringa Descartável 10ml — Caixa 50un', _DESC, 'Descarpack', 'caixa', Decimal('2')),
    EstoqueCatalogoItem('Luva Procedimento M — Caixa', _DESC, 'Supermax', 'caixa', Decimal('2')),
    EstoqueCatalogoItem('Gazes Estéreis 7,5x7,5 — Pacote', _DESC, 'Cremer', 'pacote', Decimal('5')),
    EstoqueCatalogoItem('Álcool 70% — 1L', _DESC, 'Rioquímica', 'frasco', Decimal('2')),
    # —— Cosméticos cabine ——
    EstoqueCatalogoItem('Ácido Hialurônico Sérum 30ml — Cabine', _COSM, 'Mesoestetic', 'frasco', Decimal('2')),
    EstoqueCatalogoItem('Máscara Facial Pós-Procedimento', _COSM, 'Genérico', 'unidade', Decimal('10')),
    # —— Medicamentos apoio ——
    EstoqueCatalogoItem('Lidocaína 2% sem Vasoconstrictor', _MED, 'Hypofarma', 'tubete', Decimal('2')),
    EstoqueCatalogoItem('Epinefrina 1mg/ml — Ampola', _MED, 'Hypofarma', 'ampola', Decimal('2')),
]

ESTOQUE_CATALOGO_NOMES = {item.nome for item in ESTOQUE_CATALOGO}
