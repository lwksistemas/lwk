"""
Modelos de Termo de Consentimento Livre e Esclarecido (TCLE) para procedimentos estéticos.

Baseado em boas práticas de documentação em clínicas de estética no Brasil (CFM, vigilância
sanitária e LGPD). Cada clínica deve revisar com seu conselho de classe e assessoria jurídica.

Placeholders suportados: {paciente_nome}, {paciente_cpf}, {profissional_nome},
{profissional_conselho}, {clinica_nome}, {procedimentos}, {procedimento}, {data}.
"""

_DECLARACAO_LGPD = (
    '\n\nAutorizo o tratamento dos meus dados pessoais, inclusive sensíveis de saúde, '
    'nos termos da Lei 13.709/2018 (LGPD), exclusivamente para registro clínico, '
    'prestação do serviço e guarda do prontuário pelo prazo legal.'
)

_DECLARACAO_FINAL = (
    '\n\nDeclaro que tive oportunidade de esclarecer minhas dúvidas, que as respostas '
    'foram satisfatórias, que li e compreendi este termo e concordo voluntariamente com '
    'a realização do procedimento na data {data}. Comprometo-me a seguir as orientações '
    'pré e pós-procedimento informadas e a comunicar imediatamente a clínica sobre '
    'qualquer intercorrência.'
)

TERMO_BOTOX = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — TOXINA BOTULÍNICA

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) de forma clara e adequada pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre:
• Objetivo: suavização de rugas de expressão e linhas dinâmicas por bloqueio neuromuscular temporário.
• Benefícios esperados, caráter temporário do efeito e necessidade de retoques periódicos.
• Riscos e efeitos adversos: dor local, edema, equimose, assimetria temporária, ptose palpebral, cefaleia, reação alérgica e outros descritos na literatura.
• Contraindicações: gravidez, amamentação, doenças neuromusculares, infecção local, hipersensibilidade ao produto, entre outras avaliadas na anamnese.
• Alternativas terapêuticas e cuidados pré/pós-procedimento (evitar manipulação, decúbito, exercícios intensos nas primeiras horas).{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_PREENCHIMENTO = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — PREENCHIMENTO FACIAL

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre indicação estética, produto (ácido hialurônico ou material informado), volume aplicado, duração esperada do resultado, riscos (edema, hematoma, assimetria, nódulos, reação alérgica, comprometimento vascular em casos raros), contraindicações, possibilidade de reversão com hialuronidase quando aplicável e cuidados pós-procedimento.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_HARMONIZACAO = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — HARMONIZAÇÃO FACIAL

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o planejamento e execução do procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre técnicas combinadas (toxina, preenchedores, bioestimuladores ou outras indicadas), objetivos, limitações individuais, riscos de cada técnica empregada, necessidade de sessões complementares, contraindicações e expectativas realistas de resultado (obrigação de meio, não de resultado).{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_PEELING = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — PEELING QUÍMICO

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre tipo de ácido/peeling, profundidade do tratamento, sensações esperadas, descamação pós-procedimento, riscos (eritema, ardência, hiper/hipopigmentação, cicatrizes em casos de não adesão aos cuidados), contraindicações (gestação, herpes ativo, isotretinoína recente, fototipo inadequado) e uso obrigatório de fotoproteção.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_MICROAGULHAMENTO = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — MICROAGULHAMENTO

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre indicação, profundidade de perfuração, ativos associados, número de sessões, riscos (eritema, edema, petéquias, infecção secundária, reativação de herpes), contraindicações e cuidados pós-procedimento (higiene, fotoproteção, suspensão de maquiagem e ativos irritantes).{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_LASER = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — LASER

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre tecnologia utilizada, parâmetros, número de sessões, riscos (eritema, edema, queimadura, hiper/hipopigmentação, cicatrizes, infecção), contraindicações (bronzeamento recente, isotretinoína, gestação, fotossensibilidade) e cuidados pré/pós (fotoproteção, evitar sol e calor).{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_DEPILACAO_LASER = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — DEPILAÇÃO A LASER

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre área tratada, número de sessões estimadas, intervalos, riscos (eritema, edema folicular, queimadura, hiper/hipopigmentação, foliculite), contraindicações (pele bronzeada, gestação, tatuagem na área, uso de isotretinoína) e necessidade de evitar exposição solar.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_CRIOLIPOLISE = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — CRIOLIPÓLISE

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre objetivos, número de sessões, resultados graduais, riscos (equimose, edema, dormência temporária, assimetria, hiperplasia adiposa paradoxal em casos raros), contraindicações (crioglobulinemia, hérnia local, gestação) e cuidados pós-procedimento.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_RADIOFREQUENCIA = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — RADIOFREQUÊNCIA

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre finalidade (estímulo de colágeno/flacidez), sensações durante a sessão, riscos (eritema, edema, queimadura superficial, desconforto), contraindicações (marcapasso, próteses metálicas na área, gestação, infecção ativa) e número de sessões recomendadas.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_CARBOXITERAPIA = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — CARBOXITERAPIA

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre finalidade, técnica de infusão de CO₂ medicinal, sensações durante a aplicação, riscos (dor local, equimose, crepitação subcutânea), contraindicações (insuficiência cardíaca grave, gestação, infecção local) e número de sessões.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_INTRADERMOTERAPIA = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — INTRADERMOTERAPIA / MESOTERAPIA

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre ativos utilizados, via de aplicação, indicação, riscos (dor, hematomas, nódulos, reação alérgica, infecção), contraindicações e cuidados pós-sessão.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_BIOESTIMULADOR = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — BIOESTIMULADOR DE COLÁGENO

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre produto empregado, estímulo biológico progressivo, riscos (edema, nódulos, assimetria, reação inflamatória), contraindicações, necessidade de múltiplas sessões e prazo para resultado final.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_SOROTERAPIA = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — SOROTERAPIA

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre composição do protocolo endovenoso, objetivos, riscos (dor no acesso venoso, hematoma, reação alérgica, náusea, tontura), contraindicações (gestação, alergias conhecidas, doenças cardíacas descompensadas) e que o tratamento não substitui avaliação médica quando indicada.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_MICROPIGMENTACAO = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — MICROPIGMENTAÇÃO

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre técnica, pigmentos, caráter semipermanente, riscos (alergia, infecção, assimetria, alteração de cor), contraindicações (gestação, herpes labial ativo, queloide) e cuidados de cicatrização.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_LIMPEZA_PELE = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — LIMPEZA DE PELE

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre etapas (higienização, emoliência, extração, alta frequência ou máscara conforme indicação), riscos (eritema, sensibilidade, marcas temporárias de extração), contraindicações (acne inflamada grave, herpes ativo, uso recente de isotretinoína) e cuidados pós-procedimento.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_DRENAGEM = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — DRENAGEM / MASSAGEM TERAPÊUTICA

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre finalidade, técnica manual, contraindicações (trombose, infecção cutânea, febre, gestação de risco, pós-operatório recente sem liberação) e que o procedimento não substitui tratamento médico de edema ou linfedema.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""

TERMO_GENERICO = f"""TERMO DE CONSENTIMENTO ESCLARECIDO — {{procedimento}}

Eu, {{paciente_nome}}, portador(a) do CPF {{paciente_cpf}}, declaro ter sido informado(a) de forma clara e adequada pela profissional {{profissional_nome}} ({{profissional_conselho}}), na clínica {{clinica_nome}}, sobre o procedimento: {{procedimentos}}.

Fui esclarecido(a) sobre objetivos, benefícios, riscos, efeitos adversos, contraindicações, alternativas terapêuticas e cuidados necessários.{_DECLARACAO_FINAL}{_DECLARACAO_LGPD}"""


def resolver_termo_consentimento(nome: str) -> tuple[bool, str]:
    """
    Retorna (exigir_termo, texto) para o nome do procedimento do catálogo.
    Procedimentos de baixo risco podem retornar termo inativo.
    """
    n = (nome or '').lower()

    if 'design de sobrancelha' in n:
        return False, ''

    if 'botox' in n or 'botul' in n:
        return True, TERMO_BOTOX
    if 'harmoniza' in n:
        return True, TERMO_HARMONIZACAO
    if 'preench' in n or 'skinbooster' in n:
        return True, TERMO_PREENCHIMENTO
    if 'peeling' in n:
        return True, TERMO_PEELING
    if 'microagulh' in n:
        return True, TERMO_MICROAGULHAMENTO
    if 'depilação a laser' in n or 'depilacao a laser' in n:
        return True, TERMO_DEPILACAO_LASER
    if 'laser' in n:
        return True, TERMO_LASER
    if 'criolip' in n or 'cryolip' in n:
        return True, TERMO_CRIOLIPOLISE
    if 'radiofrequ' in n:
        return True, TERMO_RADIOFREQUENCIA
    if 'carbox' in n:
        return True, TERMO_CARBOXITERAPIA
    if 'intradermo' in n or 'mesoterapia' in n or 'enzimas' in n:
        return True, TERMO_INTRADERMOTERAPIA
    if 'bioestimul' in n:
        return True, TERMO_BIOESTIMULADOR
    if 'soroterapia' in n:
        return True, TERMO_SOROTERAPIA
    if 'micropigment' in n or 'lash lifting' in n:
        return True, TERMO_MICROPIGMENTACAO
    if 'limpeza de pele' in n:
        return True, TERMO_LIMPEZA_PELE
    if 'drenagem' in n or 'massagem modeladora' in n:
        return True, TERMO_DRENAGEM

    return True, TERMO_GENERICO.replace('{procedimento}', nome.upper())
