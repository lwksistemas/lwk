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
