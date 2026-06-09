"""
Catálogo padrão de locais e procedimentos — Clínica da Beleza.
Usado no seed e no comando ensure_procedimentos_catalogo.
"""
from dataclasses import dataclass
from decimal import Decimal

from clinica_beleza.termos_consentimento_catalogo import resolver_termo_consentimento

LOCAIS_CATALOGO = [
    ('Consultório Centro — Av. Paulista', Decimal('90.00')),
    ('Sala VIP — Unidade Norte', Decimal('150.00')),
    ('Atendimento Domiciliar — Zona Sul', Decimal('120.00')),
    ('Unidade Jardins', Decimal('200.00')),
    ('Teleconsulta', Decimal('70.00')),
    ('Spa Clínico', Decimal('110.00')),
    ('Cabine de Estética 2', Decimal('95.00')),
    ('Unidade Moema', Decimal('130.00')),
    ('Atendimento Externo — Eventos', Decimal('140.00')),
    ('Consultório Premium — Alphaville', Decimal('180.00')),
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
        'Limpeza de Pele Profunda', 'Facial', Decimal('150.00'), 60,
        'Higienização, emoliência, extração de comedões, tonificação e máscara calmante. '
        'Indicada para oleosidade, poros dilatados e manutenção da saúde da pele.',
    ),
    ProcedimentoCatalogoItem(
        'Peeling Químico Suave', 'Facial', Decimal('250.00'), 50,
        'Renovação celular com ácidos de baixa/média concentração para uniformizar tom, '
        'textura e tratar manchas superficiais com descamação controlada.',
    ),
    ProcedimentoCatalogoItem(
        'Microagulhamento Facial', 'Facial', Decimal('300.00'), 60,
        'Indução percutânea de colágeno com microagulhas e ativos específicos. '
        'Melhora cicatrizes de acne, poros, linhas finas e flacidez leve.',
    ),
    ProcedimentoCatalogoItem(
        'Botox — Testa e Glabela', 'Facial', Decimal('800.00'), 30,
        'Aplicação de toxina botulínica tipo A em rugas dinâmicas de testa e entre as sobrancelhas. '
        'Resultado temporário com reavaliação em 10 a 15 dias.',
    ),
    ProcedimentoCatalogoItem(
        'Preenchimento Labial', 'Facial', Decimal('1200.00'), 45,
        'Harmonização labial com ácido hialurônico para volume, contorno e hidratação. '
        'Planejamento individualizado conforme anatomia e expectativa.',
    ),
    ProcedimentoCatalogoItem(
        'Harmonização Facial', 'Facial', Decimal('2500.00'), 90,
        'Planejamento global do terço médio e inferior da face com técnicas combinadas '
        '(toxina, preenchedores e/ou bioestimuladores) conforme avaliação.',
    ),
    ProcedimentoCatalogoItem(
        'Laser CO2 Fracionado', 'Facial', Decimal('900.00'), 60,
        'Tratamento ablativo fracionado para rejuvenescimento, cicatrizes e textura irregular. '
        'Requer preparo da pele e rigorosa fotoproteção no pós.',
    ),
    ProcedimentoCatalogoItem(
        'Hidratação Facial com Ácido Hialurônico', 'Facial', Decimal('280.00'), 50,
        'Reposição de água e viço com ativos humectantes e ácido hialurônico de baixo peso molecular. '
        'Ideal para peles desidratadas e ressecadas.',
    ),
    ProcedimentoCatalogoItem(
        'Tratamento para Melasma', 'Facial', Decimal('350.00'), 55,
        'Protocolo clareador com ativos despigmentantes, proteção solar e orientação domiciliar. '
        'Tratamento contínuo com acompanhamento periódico.',
    ),
    ProcedimentoCatalogoItem(
        'LED Terapia Facial', 'Facial', Decimal('120.00'), 40,
        'Fotobiomodulação com comprimentos de onda específicos para inflamação, acne e regeneração. '
        'Procedimento não invasivo, sem tempo de recuperação.',
    ),
    ProcedimentoCatalogoItem(
        'Drenagem Linfática Manual', 'Corporal', Decimal('120.00'), 60,
        'Técnica manual de ritmo lento para redução de edema, detoxificação e bem-estar. '
        'Indicada pós-operatório estético e retenção de líquidos.',
    ),
    ProcedimentoCatalogoItem(
        'Massagem Modeladora', 'Corporal', Decimal('180.00'), 90,
        'Manobras intensas para modelagem de contornos, ativação circulatória e redução de gordura localizada leve.',
    ),
    ProcedimentoCatalogoItem(
        'Cryolipolysis — Abdômen', 'Corporal', Decimal('450.00'), 75,
        'Redução de gordura localizada por resfriamento controlado do tecido adiposo. '
        'Resultados progressivos em 60 a 90 dias.',
    ),
    ProcedimentoCatalogoItem(
        'Radiofrequência Corporal', 'Corporal', Decimal('320.00'), 60,
        'Estímulo de colágeno e melhora da flacidez corporal por aquecimento controlado do tecido dérmico.',
    ),
    ProcedimentoCatalogoItem(
        'Intradermoterapia — Celulite', 'Corporal', Decimal('280.00'), 45,
        'Aplicação intradérmica de ativos lipolíticos e drenantes para tratamento de celulite e gordura localizada.',
    ),
    ProcedimentoCatalogoItem(
        'Carboxiterapia', 'Corporal', Decimal('200.00'), 50,
        'Infusão subcutânea de CO₂ medicinal para estímulo circulatório, celulite, estrias e gordura localizada.',
    ),
    ProcedimentoCatalogoItem(
        'Enzimas Corporais', 'Corporal', Decimal('220.00'), 55,
        'Aplicação de enzimas lipolíticas para redução de volume e melhora de contorno corporal.',
    ),
    ProcedimentoCatalogoItem(
        'Bioestimulador de Colágeno', 'Estética', Decimal('1800.00'), 60,
        'Injeção de bioestimuladores (ex.: PLLA, hidroxiapatita de cálcio) para firmeza e sustentação gradual da pele.',
    ),
    ProcedimentoCatalogoItem(
        'Skinbooster', 'Estética', Decimal('950.00'), 45,
        'Microinjeções de ácido hialurônico de baixa reticulação para hidratação profunda e qualidade da pele.',
    ),
    ProcedimentoCatalogoItem(
        'Depilação a Laser — Axilas', 'Depilação', Decimal('150.00'), 30,
        'Eliminação progressiva dos pelos com laser de diodo ou alexandrite. Sessões seriadas conforme fototipo.',
    ),
    ProcedimentoCatalogoItem(
        'Depilação a Laser — Virilha', 'Depilação', Decimal('220.00'), 40,
        'Depilação definitiva da região íntima com parâmetros ajustados ao fototipo e espessura do pelo.',
    ),
    ProcedimentoCatalogoItem(
        'Depilação a Laser — Perna Inteira', 'Depilação', Decimal('380.00'), 90,
        'Tratamento completo das pernas com laser. Requer fotoproteção e intervalo entre sessões.',
    ),
    ProcedimentoCatalogoItem(
        'Soroterapia — Imunidade', 'Soroterapia', Decimal('350.00'), 60,
        'Protocolo endovenoso com vitaminas e minerais para suporte imunológico e recuperação. '
        'Avaliação prévia obrigatória.',
    ),
    ProcedimentoCatalogoItem(
        'Soroterapia — Energia e Foco', 'Soroterapia', Decimal('320.00'), 60,
        'Cocktail vitamínico endovenoso para fadiga, estresse e melhora de disposição.',
    ),
    ProcedimentoCatalogoItem(
        'Soroterapia — Detox', 'Soroterapia', Decimal('300.00'), 60,
        'Protocolo detoxificante com antioxidantes e hidratação venosa para bem-estar metabólico.',
    ),
    ProcedimentoCatalogoItem(
        'Mesoterapia Capilar', 'Capilar', Decimal('280.00'), 45,
        'Microinjeções no couro cabeludo com ativos para queda, afinamento e fortalecimento dos fios.',
    ),
    ProcedimentoCatalogoItem(
        'Laser Capilar — Queda de Cabelo', 'Capilar', Decimal('400.00'), 50,
        'Fototerapia de baixa intensidade para estimular folículos e tratar alopecia em estágio inicial.',
    ),
    ProcedimentoCatalogoItem(
        'Design de Sobrancelhas', 'Estética', Decimal('80.00'), 30,
        'Mapeamento e definição do formato das sobrancelhas com pinça e/ou henna. Procedimento estético de baixo risco.',
    ),
    ProcedimentoCatalogoItem(
        'Lash Lifting', 'Estética', Decimal('150.00'), 60,
        'Curvatura e tintura dos cílios naturais com produtos específicos. Efeito de 6 a 8 semanas.',
    ),
    ProcedimentoCatalogoItem(
        'Micropigmentação Labial', 'Estética', Decimal('650.00'), 90,
        'Implante de pigmento semipermanente para definição e cor dos lábios. Retoque recomendado em 30 dias.',
    ),
]

LOCAIS_CATALOGO_NOMES = {nome for nome, _ in LOCAIS_CATALOGO}
PROCEDIMENTOS_CATALOGO_NOMES = {item.nome for item in PROCEDIMENTOS_CATALOGO}

# (nome, telefone, cpf) — pacientes de demonstração (CPFs válidos, fictícios)
PACIENTES_CATALOGO = [
    ('Ana Carolina Mendes', '(11) 98112-3401', '616.517.286-58'),
    ('Bruno Ferreira Santos', '(11) 98223-4502', '031.862.659-40'),
    ('Camila Rodrigues Lima', '(11) 98334-5603', '896.322.472-48'),
    ('Daniel Oliveira Costa', '(11) 98445-6704', '785.377.876-71'),
    ('Eduarda Martins Souza', '(11) 98556-7805', '619.883.350-00'),
    ('Felipe Almeida Ribeiro', '(11) 98667-8906', '768.694.582-00'),
    ('Gabriela Nunes Pereira', '(11) 98778-9017', '503.703.950-93'),
    ('Henrique Barbosa Dias', '(11) 98889-0128', '092.423.803-85'),
    ('Isabela Castro Vieira', '(11) 98990-1239', '875.110.291-91'),
    ('João Pedro Teixeira', '(11) 99001-2340', '207.187.283-51'),
    ('Larissa Gomes Araújo', '(11) 99112-3451', '938.166.622-93'),
    ('Marcos Henrique Silva', '(11) 99223-4562', '540.627.678-64'),
]

# (nome, especialidade, email_base) — profissionais de demonstração (email recebe sufixo do seed)
PROFISSIONAIS_SEED_DATA = [
    ('Dra. Fernanda Oliveira', 'Estética', 'prof.fixa'),
    ('Dr. Ricardo Almeida', 'Dermatologia', 'prof.pct'),
    ('Dra. Patrícia Nogueira', 'Biomédica', 'prof.mista'),
]


def procedimento_catalogo_defaults(item: ProcedimentoCatalogoItem) -> dict:
    """Campos para update_or_create de Procedure a partir do catálogo."""
    termo_ativo, termo_texto = resolver_termo_consentimento(item.nome)
    return {
        'preco': item.preco,
        'duracao_minutos': item.duracao_minutos,
        'categoria': item.categoria,
        'is_active': True,
        'descricao': item.descricao,
        'termo_consentimento_ativo': termo_ativo,
        'termo_consentimento': termo_texto,
    }
