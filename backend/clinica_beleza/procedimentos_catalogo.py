"""Catálogo padrão de locais e procedimentos — Clínica da Beleza.
Usado no seed e no comando ensure_procedimentos_catalogo.

Consumidores: `catalogo_service.py` e management commands
(`ensure_procedimentos_catalogo`, `popular_loja_clinica_beleza`).
Este arquivo define apenas dados de seed — não contém lógica de negócio em runtime.
"""
from dataclasses import dataclass
from decimal import Decimal

from clinica_beleza.termos_consentimento_catalogo import resolver_termo_consentimento

LOCAIS_CATALOGO = [
    ("Consultório", Decimal("0.00"), 40),
]

# Convênio padrão (particular) — sempre cadastrado na loja.
CONVENIO_PARTICULAR_CATALOGO = ("Particular", "PARTICULAR")

# Nome de agenda padrão — sempre cadastrado na loja.
NOMES_AGENDA_CATALOGO = [
    "Consulta",
]

# Locais de demonstração antigos — desativados ao reaplicar o catálogo padrão.
LOCAIS_CATALOGO_LEGADO = [
    "Consultório Centro — Av. Paulista",
    "Sala VIP — Unidade Norte",
    "Atendimento Domiciliar — Zona Sul",
    "Unidade Jardins",
    "Teleconsulta",
    "Spa Clínico",
    "Cabine de Estética 2",
    "Unidade Moema",
    "Atendimento Externo — Eventos",
    "Consultório Premium — Alphaville",
]


@dataclass(frozen=True)
class ProcedimentoCatalogoItem:
    nome: str
    categoria: str
    preco: Decimal
    duracao_minutos: int
    descricao: str


PROCEDIMENTOS_CATALOGO: list[ProcedimentoCatalogoItem] = [
    ProcedimentoCatalogoItem(
        "Limpeza de Pele Profunda", "facial", Decimal("150.00"), 60,
        "Higienização, emoliência, extração de comedões, tonificação e máscara calmante. "
        "Indicada para oleosidade, poros dilatados e manutenção da saúde da pele.",
    ),
    ProcedimentoCatalogoItem(
        "Peeling Químico Suave", "facial", Decimal("250.00"), 50,
        "Renovação celular com ácidos de baixa/média concentração para uniformizar tom, "
        "textura e tratar manchas superficiais com descamação controlada.",
    ),
    ProcedimentoCatalogoItem(
        "Microagulhamento Facial", "facial", Decimal("300.00"), 60,
        "Indução percutânea de colágeno com microagulhas e ativos específicos. "
        "Melhora cicatrizes de acne, poros, linhas finas e flacidez leve.",
    ),
    ProcedimentoCatalogoItem(
        "Botox — Testa e Glabela", "facial", Decimal("800.00"), 30,
        "Aplicação de toxina botulínica tipo A em rugas dinâmicas de testa e entre as sobrancelhas. "
        "Resultado temporário com reavaliação em 10 a 15 dias.",
    ),
    ProcedimentoCatalogoItem(
        "Preenchimento Labial", "facial", Decimal("1200.00"), 45,
        "Harmonização labial com ácido hialurônico para volume, contorno e hidratação. "
        "Planejamento individualizado conforme anatomia e expectativa.",
    ),
    ProcedimentoCatalogoItem(
        "Harmonização Facial", "facial", Decimal("2500.00"), 90,
        "Planejamento global do terço médio e inferior da face com técnicas combinadas "
        "(toxina, preenchedores e/ou bioestimuladores) conforme avaliação.",
    ),
    ProcedimentoCatalogoItem(
        "Laser CO2 Fracionado", "facial", Decimal("900.00"), 60,
        "Tratamento ablativo fracionado para rejuvenescimento, cicatrizes e textura irregular. "
        "Requer preparo da pele e rigorosa fotoproteção no pós.",
    ),
    ProcedimentoCatalogoItem(
        "Hidratação Facial com Ácido Hialurônico", "facial", Decimal("280.00"), 50,
        "Reposição de água e viço com ativos humectantes e ácido hialurônico de baixo peso molecular. "
        "Ideal para peles desidratadas e ressecadas.",
    ),
    ProcedimentoCatalogoItem(
        "Tratamento para Melasma", "facial", Decimal("350.00"), 55,
        "Protocolo clareador com ativos despigmentantes, proteção solar e orientação domiciliar. "
        "Tratamento contínuo com acompanhamento periódico.",
    ),
    ProcedimentoCatalogoItem(
        "LED Terapia Facial", "facial", Decimal("120.00"), 40,
        "Fotobiomodulação com comprimentos de onda específicos para inflamação, acne e regeneração. "
        "Procedimento não invasivo, sem tempo de recuperação.",
    ),
    ProcedimentoCatalogoItem(
        "Drenagem Linfática Manual", "corporal", Decimal("120.00"), 60,
        "Técnica manual de ritmo lento para redução de edema, detoxificação e bem-estar. "
        "Indicada pós-operatório estético e retenção de líquidos.",
    ),
    ProcedimentoCatalogoItem(
        "Massagem Modeladora", "corporal", Decimal("180.00"), 90,
        "Manobras intensas para modelagem de contornos, ativação circulatória e redução de gordura localizada leve.",
    ),
    ProcedimentoCatalogoItem(
        "Cryolipolysis — Abdômen", "corporal", Decimal("450.00"), 75,
        "Redução de gordura localizada por resfriamento controlado do tecido adiposo. "
        "Resultados progressivos em 60 a 90 dias.",
    ),
    ProcedimentoCatalogoItem(
        "Radiofrequência Corporal", "corporal", Decimal("320.00"), 60,
        "Estímulo de colágeno e melhora da flacidez corporal por aquecimento controlado do tecido dérmico.",
    ),
    ProcedimentoCatalogoItem(
        "Intradermoterapia — Celulite", "corporal", Decimal("280.00"), 45,
        "Aplicação intradérmica de ativos lipolíticos e drenantes para tratamento de celulite e gordura localizada.",
    ),
    ProcedimentoCatalogoItem(
        "Carboxiterapia", "corporal", Decimal("200.00"), 50,
        "Infusão subcutânea de CO₂ medicinal para estímulo circulatório, celulite, estrias e gordura localizada.",
    ),
    ProcedimentoCatalogoItem(
        "Enzimas Corporais", "corporal", Decimal("220.00"), 55,
        "Aplicação de enzimas lipolíticas para redução de volume e melhora de contorno corporal.",
    ),
    ProcedimentoCatalogoItem(
        "Bioestimulador de Colágeno", "estetica", Decimal("1800.00"), 60,
        "Injeção de bioestimuladores (ex.: PLLA, hidroxiapatita de cálcio) para firmeza e sustentação gradual da pele.",
    ),
    ProcedimentoCatalogoItem(
        "Skinbooster", "estetica", Decimal("950.00"), 45,
        "Microinjeções de ácido hialurônico de baixa reticulação para hidratação profunda e qualidade da pele.",
    ),
    ProcedimentoCatalogoItem(
        "Depilação a Laser — Axilas", "depilacao", Decimal("150.00"), 30,
        "Eliminação progressiva dos pelos com laser de diodo ou alexandrite. Sessões seriadas conforme fototipo.",
    ),
    ProcedimentoCatalogoItem(
        "Depilação a Laser — Virilha", "depilacao", Decimal("220.00"), 40,
        "Depilação definitiva da região íntima com parâmetros ajustados ao fototipo e espessura do pelo.",
    ),
    ProcedimentoCatalogoItem(
        "Depilação a Laser — Perna Inteira", "depilacao", Decimal("380.00"), 90,
        "Tratamento completo das pernas com laser. Requer fotoproteção e intervalo entre sessões.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Imunidade", "soroterapia", Decimal("350.00"), 60,
        "Protocolo endovenoso com vitaminas e minerais para suporte imunológico e recuperação. "
        "Avaliação prévia obrigatória.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Energia e Foco", "soroterapia", Decimal("320.00"), 60,
        "Cocktail vitamínico endovenoso para fadiga, estresse e melhora de disposição.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Detox", "soroterapia", Decimal("300.00"), 60,
        "Protocolo detoxificante com antioxidantes e hidratação venosa para bem-estar metabólico.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Hidratação IV", "soroterapia", Decimal("260.00"), 45,
        "Reposição hídrica e eletrolítica endovenosa para desidratação, cansaço e recuperação rápida. "
        "Indicada após viagens, jejum prolongado ou perda de líquidos.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Vitamina C", "soroterapia", Decimal("380.00"), 60,
        "Infusão de vitamina C em dose terapêutica para suporte antioxidante, imunidade e viço. "
        "Avaliação prévia e monitoramento durante a aplicação.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Glutamina e Reposição", "soroterapia", Decimal("400.00"), 60,
        "Protocolo com glutamina, aminoácidos e micronutrientes para recuperação muscular, "
        "integridade intestinal e suporte metabólico pós-esforço ou convalescença.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Recuperação Pós-Exercício", "soroterapia", Decimal("290.00"), 45,
        "Cocktail endovenoso com eletrólitos, vitaminas do complexo B e antioxidantes para "
        "reduzir fadiga e acelerar a recuperação após treinos intensos ou competições.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Repouso e Ressaca", "soroterapia", Decimal("330.00"), 60,
        "Hidratação venosa com vitaminas, minerais e antieméticos conforme indicação clínica. "
        "Auxilia na recuperação de mal-estar pós-evento, privação de sono ou excesso alimentar.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Beleza e Pele", "soroterapia", Decimal("360.00"), 60,
        "Protocolo com biotina, zinco, selênio e antioxidantes para suporte à saúde da pele, "
        "cabelos e unhas. Complementa tratamentos estéticos faciais e capilares.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Sono e Relaxamento", "soroterapia", Decimal("310.00"), 60,
        "Infusão com magnésio, vitaminas do complexo B e aminoácidos calmantes para redução de "
        "estresse, tensão muscular e melhora da qualidade do sono.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Metabolismo e Emagrecimento", "soroterapia", Decimal("340.00"), 60,
        "Protocolo com L-carnitina, vitaminas e minerais para suporte ao metabolismo energético "
        "e complemento a planos de reeducação alimentar e atividade física.",
    ),
    ProcedimentoCatalogoItem(
        "Soroterapia — Anti-Aging", "soroterapia", Decimal("420.00"), 60,
        "Cocktail antioxidante com vitaminas, minerais e ativos de longevidade para vitalidade, "
        "disposição e suporte ao envelhecimento saudável. Não substitui avaliação médica.",
    ),
    ProcedimentoCatalogoItem(
        "Mesoterapia Capilar", "capilar", Decimal("280.00"), 45,
        "Microinjeções no couro cabeludo com ativos para queda, afinamento e fortalecimento dos fios.",
    ),
    ProcedimentoCatalogoItem(
        "Laser Capilar — Queda de Cabelo", "capilar", Decimal("400.00"), 50,
        "Fototerapia de baixa intensidade para estimular folículos e tratar alopecia em estágio inicial.",
    ),
    ProcedimentoCatalogoItem(
        "Design de Sobrancelhas", "estetica", Decimal("80.00"), 30,
        "Mapeamento e definição do formato das sobrancelhas com pinça e/ou henna. Procedimento estético de baixo risco.",
    ),
    ProcedimentoCatalogoItem(
        "Lash Lifting", "estetica", Decimal("150.00"), 60,
        "Curvatura e tintura dos cílios naturais com produtos específicos. Efeito de 6 a 8 semanas.",
    ),
    ProcedimentoCatalogoItem(
        "Micropigmentação Labial", "estetica", Decimal("650.00"), 90,
        "Implante de pigmento semipermanente para definição e cor dos lábios. Retoque recomendado em 30 dias.",
    ),
]

LOCAIS_CATALOGO_NOMES = {nome for nome, *_ in LOCAIS_CATALOGO}
PROCEDIMENTOS_CATALOGO_NOMES = {item.nome for item in PROCEDIMENTOS_CATALOGO}

# (nome, telefone, cpf) — pacientes de demonstração (CPFs válidos, fictícios)
PACIENTES_CATALOGO = [
    ("Ana Carolina Mendes", "(11) 98112-3401", "616.517.286-58"),
    ("Bruno Ferreira Santos", "(11) 98223-4502", "031.862.659-40"),
    ("Camila Rodrigues Lima", "(11) 98334-5603", "896.322.472-48"),
    ("Daniel Oliveira Costa", "(11) 98445-6704", "785.377.876-71"),
    ("Eduarda Martins Souza", "(11) 98556-7805", "619.883.350-00"),
    ("Felipe Almeida Ribeiro", "(11) 98667-8906", "768.694.582-00"),
    ("Gabriela Nunes Pereira", "(11) 98778-9017", "503.703.950-93"),
    ("Henrique Barbosa Dias", "(11) 98889-0128", "092.423.803-85"),
    ("Isabela Castro Vieira", "(11) 98990-1239", "875.110.291-91"),
    ("João Pedro Teixeira", "(11) 99001-2340", "207.187.283-51"),
    ("Larissa Gomes Araújo", "(11) 99112-3451", "938.166.622-93"),
    ("Marcos Henrique Silva", "(11) 99223-4562", "540.627.678-64"),
]

# (nome, especialidade, email_base) — profissionais de demonstração (email recebe sufixo do seed)
PROFISSIONAIS_SEED_DATA = [
    ("Dra. Fernanda Oliveira", "estetica", "prof.fixa"),
    ("Dr. Ricardo Almeida", "Dermatologia", "prof.pct"),
    ("Dra. Patrícia Nogueira", "Biomédica", "prof.mista"),
]


def procedimento_catalogo_defaults(item: ProcedimentoCatalogoItem) -> dict:
    """Campos para update_or_create de Procedure a partir do catálogo."""
    termo_ativo, termo_texto = resolver_termo_consentimento(item.nome)
    return {
        "preco": item.preco,
        "duracao_minutos": item.duracao_minutos,
        "categoria": item.categoria,
        "is_active": True,
        "descricao": item.descricao,
        "termo_consentimento_ativo": termo_ativo,
        "termo_consentimento": termo_texto,
    }
