"""
Catálogo padrão de locais e procedimentos — Clínica da Beleza.
Usado no seed e no comando ensure_procedimentos_catalogo.
"""
from decimal import Decimal

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

# (nome, categoria, preço, duração minutos)
PROCEDIMENTOS_CATALOGO = [
    ('Limpeza de Pele Profunda', 'Facial', Decimal('150.00'), 60),
    ('Peeling Químico Suave', 'Facial', Decimal('250.00'), 50),
    ('Microagulhamento Facial', 'Facial', Decimal('300.00'), 60),
    ('Botox — Testa e Glabela', 'Facial', Decimal('800.00'), 30),
    ('Preenchimento Labial', 'Facial', Decimal('1200.00'), 45),
    ('Harmonização Facial', 'Facial', Decimal('2500.00'), 90),
    ('Laser CO2 Fracionado', 'Facial', Decimal('900.00'), 60),
    ('Hidratação Facial com Ácido Hialurônico', 'Facial', Decimal('280.00'), 50),
    ('Tratamento para Melasma', 'Facial', Decimal('350.00'), 55),
    ('LED Terapia Facial', 'Facial', Decimal('120.00'), 40),
    ('Drenagem Linfática Manual', 'Corporal', Decimal('120.00'), 60),
    ('Massagem Modeladora', 'Corporal', Decimal('180.00'), 90),
    ('Cryolipolysis — Abdômen', 'Corporal', Decimal('450.00'), 75),
    ('Radiofrequência Corporal', 'Corporal', Decimal('320.00'), 60),
    ('Intradermoterapia — Celulite', 'Corporal', Decimal('280.00'), 45),
    ('Carboxiterapia', 'Corporal', Decimal('200.00'), 50),
    ('Enzimas Corporais', 'Corporal', Decimal('220.00'), 55),
    ('Bioestimulador de Colágeno', 'Estética', Decimal('1800.00'), 60),
    ('Skinbooster', 'Estética', Decimal('950.00'), 45),
    ('Depilação a Laser — Axilas', 'Depilação', Decimal('150.00'), 30),
    ('Depilação a Laser — Virilha', 'Depilação', Decimal('220.00'), 40),
    ('Depilação a Laser — Perna Inteira', 'Depilação', Decimal('380.00'), 90),
    ('Soroterapia — Imunidade', 'Soroterapia', Decimal('350.00'), 60),
    ('Soroterapia — Energia e Foco', 'Soroterapia', Decimal('320.00'), 60),
    ('Soroterapia — Detox', 'Soroterapia', Decimal('300.00'), 60),
    ('Mesoterapia Capilar', 'Capilar', Decimal('280.00'), 45),
    ('Laser Capilar — Queda de Cabelo', 'Capilar', Decimal('400.00'), 50),
    ('Design de Sobrancelhas', 'Estética', Decimal('80.00'), 30),
    ('Lash Lifting', 'Estética', Decimal('150.00'), 60),
    ('Micropigmentação Labial', 'Estética', Decimal('650.00'), 90),
]

LOCAIS_CATALOGO_NOMES = {nome for nome, _ in LOCAIS_CATALOGO}
PROCEDIMENTOS_CATALOGO_NOMES = {nome for nome, *_ in PROCEDIMENTOS_CATALOGO}
