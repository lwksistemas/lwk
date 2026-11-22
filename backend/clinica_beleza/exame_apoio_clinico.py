"""Apoio educativo para marcadores fora da referência (sintomas e recomendações).

Textos curtos para a profissional — não são diagnóstico nem prescrição.
Não sugerem dose de medicamento, hormônio ou suplemento.
"""
from __future__ import annotations

# codigo -> status (alto|baixo) -> sintomas_possiveis / recomendacoes
CATALOGO_APOIO: dict[str, dict[str, dict[str, list[str]]]] = {
    "glicose": {
        "alto": {
            "sintomas_possiveis": [
                "Sede aumentada e urinar com mais frequência",
                "Cansaço ou visão turva em alguns casos",
                "Maior risco metabólico a médio prazo se persistir",
            ],
            "recomendacoes": [
                "Reduzir açúcares simples e ultraprocessados",
                "Priorizar fibras, proteínas e refeições regulares",
                "Atividade física regular e reavaliar com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Tremor, sudorese fria ou tontura",
                "Fome intensa, irritabilidade ou fraqueza",
                "Em casos intensos, confusão ou mal-estar",
            ],
            "recomendacoes": [
                "Não pular refeições; incluir carboidrato de boa qualidade",
                "Evitar jejum prolongado sem orientação",
                "Discutir com o profissional causas e reavaliação",
            ],
        },
    },
    "hba1c": {
        "alto": {
            "sintomas_possiveis": [
                "Pode indicar glicemia média elevada nas últimas semanas",
                "Fadiga, sede ou alterações no peso em alguns pacientes",
                "Maior risco de complicações se mantida alta",
            ],
            "recomendacoes": [
                "Revisar alimentação e atividade física com o profissional",
                "Monitorar glicemia conforme orientação clínica",
                "Reavaliar HbA1c no prazo indicado pelo profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Em geral assintomático quando levemente abaixo",
                "Se muito baixa, pode haver episódios de hipoglicemia",
            ],
            "recomendacoes": [
                "Confirmar contexto clínico (dieta, medicamentos em uso)",
                "Discutir com o profissional se há sintomas de hipoglicemia",
            ],
        },
    },
    "colesterol_total": {
        "alto": {
            "sintomas_possiveis": [
                "Frequentemente sem sintomas no dia a dia",
                "Associado a maior risco cardiovascular a longo prazo",
            ],
            "recomendacoes": [
                "Reduzir gorduras saturadas e ultraprocessados",
                "Aumentar fibras e atividade física aeróbica",
                "Reavaliar lipidograma e plano alimentar com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Em geral assintomático",
                "Em contextos específicos, pode merecer investigação",
            ],
            "recomendacoes": [
                "Avaliar dieta e contexto clínico com o profissional",
                "Não suplementar lipídios por conta própria",
            ],
        },
    },
    "hdl": {
        "baixo": {
            "sintomas_possiveis": [
                "Em geral sem sintomas imediatos",
                "Menor proteção cardiovascular a longo prazo",
                "Pode acompanhar sedentarismo ou excesso de peso",
            ],
            "recomendacoes": [
                "Atividade física regular (caminhada, musculação conforme orientação)",
                "Reduzir ultraprocessados e melhorar qualidade do sono",
                "Discutir plano alimentar e reavaliação com o profissional",
            ],
        },
        "alto": {
            "sintomas_possiveis": [
                "Em geral favorável; valores muito altos raramente têm sintomas",
            ],
            "recomendacoes": [
                "Manter hábitos saudáveis",
                "Confirmar com o profissional se há necessidade de investigação adicional",
            ],
        },
    },
    "ldl": {
        "alto": {
            "sintomas_possiveis": [
                "Frequentemente assintomático",
                "Maior risco de eventos cardiovasculares a longo prazo",
            ],
            "recomendacoes": [
                "Reduzir gorduras saturadas e frituras",
                "Aumentar fibras solúveis e atividade física",
                "Reavaliar com o profissional o risco cardiovascular global",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Em geral assintomático",
            ],
            "recomendacoes": [
                "Manter hábitos saudáveis",
                "Avaliar contexto clínico se estiver muito baixo",
            ],
        },
    },
    "vldl": {
        "alto": {
            "sintomas_possiveis": [
                "Pode acompanhar triglicerídeos elevados",
                "Em geral sem sintomas imediatos",
            ],
            "recomendacoes": [
                "Reduzir açúcar, álcool e ultraprocessados",
                "Atividade física e refeição com menos carboidrato refinado",
                "Reavaliar com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral assintomático"],
            "recomendacoes": ["Manter hábitos saudáveis e acompanhar o lipidograma"],
        },
    },
    "triglicerides": {
        "alto": {
            "sintomas_possiveis": [
                "Frequentemente assintomático",
                "Em níveis muito altos, risco pancreático e metabólico",
            ],
            "recomendacoes": [
                "Reduzir açúcar, álcool e carboidratos refinados",
                "Controlar peso e aumentar atividade física",
                "Reavaliar com o profissional; jejum adequado no próximo exame",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral assintomático"],
            "recomendacoes": ["Manter alimentação equilibrada"],
        },
    },
    "hemoglobina": {
        "baixo": {
            "sintomas_possiveis": [
                "Cansaço, palidez ou falta de ar aos esforços",
                "Tontura, unhas frágeis ou queda de desempenho",
            ],
            "recomendacoes": [
                "Avaliar alimentação rica em ferro e vitamina C com o profissional",
                "Investigar causas (perda, absorção, inflamação) na consulta",
                "Não iniciar suplemento de ferro sem orientação",
            ],
        },
        "alto": {
            "sintomas_possiveis": [
                "Cefaleia, vermelhidão ou prurido em alguns casos",
                "Pode relacionar-se a tabagismo, desidratação ou outras causas",
            ],
            "recomendacoes": [
                "Hidratação adequada e evitar tabagismo",
                "Discutir investigação com o profissional",
            ],
        },
    },
    "hematocrito": {
        "baixo": {
            "sintomas_possiveis": [
                "Cansaço, palidez ou intolerância ao esforço",
            ],
            "recomendacoes": [
                "Avaliar junto com hemoglobina e ferro no contexto clínico",
                "Discutir causas e reavaliação com o profissional",
            ],
        },
        "alto": {
            "sintomas_possiveis": [
                "Pode acompanhar desidratação ou outras condições",
            ],
            "recomendacoes": [
                "Hidratação adequada",
                "Reavaliar com o profissional o hemograma completo",
            ],
        },
    },
    "eritrocitos": {
        "baixo": {
            "sintomas_possiveis": ["Cansaço e menor disposição"],
            "recomendacoes": [
                "Interpretar junto ao restante do eritrograma",
                "Discutir investigação com o profissional",
            ],
        },
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar tabagismo ou desidratação"],
            "recomendacoes": ["Hidratação e avaliação clínica conjunta"],
        },
    },
    "vcm": {
        "baixo": {
            "sintomas_possiveis": ["Pode sugerir anemia por deficiência de ferro (contexto clínico)"],
            "recomendacoes": [
                "Avaliar ferro, ferritina e alimentação com o profissional",
                "Não suplementar sem orientação",
            ],
        },
        "alto": {
            "sintomas_possiveis": ["Pode sugerir deficiência de B12/folato ou outras causas"],
            "recomendacoes": [
                "Avaliar vitamina B12, folato e contexto clínico",
                "Discutir investigação com o profissional",
            ],
        },
    },
    "hcm": {
        "baixo": {
            "sintomas_possiveis": ["Pode acompanhar anemia microcítica"],
            "recomendacoes": ["Interpretar com VCM/hemoglobina e avaliar ferro"],
        },
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar anemias macrocíticas"],
            "recomendacoes": ["Avaliar B12/folato no contexto clínico"],
        },
    },
    "chcm": {
        "baixo": {
            "sintomas_possiveis": ["Pode acompanhar anemias hipocrômicas"],
            "recomendacoes": ["Interpretar com o hemograma completo"],
        },
        "alto": {
            "sintomas_possiveis": ["Pode relacionar-se a artefato laboratorial ou esferocitose (raro)"],
            "recomendacoes": ["Confirmar com o profissional e repetir se necessário"],
        },
    },
    "rdw": {
        "alto": {
            "sintomas_possiveis": ["Sugere variação no tamanho das hemácias"],
            "recomendacoes": [
                "Interpretar com VCM e ferro/B12",
                "Discutir causas com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral pouco sintomático isoladamente"],
            "recomendacoes": ["Manter acompanhamento do hemograma"],
        },
    },
    "leucocitos": {
        "alto": {
            "sintomas_possiveis": [
                "Pode acompanhar infecção, inflamação ou estresse",
                "Febre, dor ou mal-estar conforme a causa",
            ],
            "recomendacoes": [
                "Avaliar sintomas infecciosos/inflamatórios na consulta",
                "Repetir ou aprofundar exames conforme orientação profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Maior vulnerabilidade a infecções em alguns casos",
                "Cansaço ou úlceras orais ocasionais",
            ],
            "recomendacoes": [
                "Evitar automedicação e comunicar febre ao profissional",
                "Investigar causas com o profissional",
            ],
        },
    },
    "plaquetas": {
        "alto": {
            "sintomas_possiveis": [
                "Risco trombótico aumentado em alguns contextos",
                "Pode ser reativo a inflamação ou ferro baixo",
            ],
            "recomendacoes": [
                "Avaliar causas reativas vs primárias com o profissional",
                "Não usar antiagregante por conta própria",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Sangramentos fáceis, petéquias ou hematomas",
                "Sangramento gengival ou nasal em alguns casos",
            ],
            "recomendacoes": [
                "Evitar trauma e automedicação com AAS/anti-inflamatórios sem orientação",
                "Avaliar urgência e causas com o profissional",
            ],
        },
    },
    "segmentados": {
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar infecção bacteriana ou estresse"],
            "recomendacoes": ["Correlacionar com quadro clínico e leucócitos totais"],
        },
        "baixo": {
            "sintomas_possiveis": ["Maior risco infeccioso em alguns contextos"],
            "recomendacoes": ["Avaliar com o profissional se há sintomas infecciosos"],
        },
    },
    "linfocitos": {
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar infecção viral ou outras causas"],
            "recomendacoes": ["Interpretar no contexto clínico completo"],
        },
        "baixo": {
            "sintomas_possiveis": ["Pode acompanhar estresse, corticoides ou infecção"],
            "recomendacoes": ["Discutir causas com o profissional"],
        },
    },
    "monocitos": {
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar inflamação crônica ou recuperação de infecção"],
            "recomendacoes": ["Avaliar no conjunto do leucograma"],
        },
        "baixo": {
            "sintomas_possiveis": ["Pouco sintomático isoladamente"],
            "recomendacoes": ["Acompanhar hemograma conforme orientação"],
        },
    },
    "eosinofilos": {
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar alergia, asma ou parasitose"],
            "recomendacoes": [
                "Investigar alergias e sintomas digestivos/respiratórios",
                "Discutir com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral assintomático"],
            "recomendacoes": ["Acompanhar conforme contexto clínico"],
        },
    },
    "basofilos": {
        "alto": {
            "sintomas_possiveis": ["Raro; pode acompanhar processos alérgicos ou outras causas"],
            "recomendacoes": ["Interpretar com o profissional no leucograma"],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral sem relevância isolada"],
            "recomendacoes": ["Manter acompanhamento habitual"],
        },
    },
    "vitamina_d": {
        "baixo": {
            "sintomas_possiveis": [
                "Cansaço, dores musculares ou ósseas",
                "Baixa imunidade relatada por alguns pacientes",
                "Humor baixo ou menor disposição",
            ],
            "recomendacoes": [
                "Exposição solar segura conforme orientação profissional",
                "Alimentação com fontes de vitamina D e gorduras saudáveis",
                "Discutir reposição e reavaliação com o profissional (sem automedicação)",
            ],
        },
        "alto": {
            "sintomas_possiveis": [
                "Náusea, sede excessiva ou mal-estar em intoxicação",
                "Risco de hipercalcemia se muito elevada",
            ],
            "recomendacoes": [
                "Suspender suplementação por conta própria",
                "Avaliar com o profissional e repetir dosagem se indicado",
            ],
        },
    },
    "vitamina_b12": {
        "baixo": {
            "sintomas_possiveis": [
                "Cansaço, formigamento ou alteração de memória",
                "Palidez ou língua dolorida em alguns casos",
            ],
            "recomendacoes": [
                "Avaliar dieta (origem animal) e absorção com o profissional",
                "Não iniciar reposição sem orientação",
                "Reavaliar hemograma e B12 conforme plano clínico",
            ],
        },
        "alto": {
            "sintomas_possiveis": ["Em geral assintomático; pode refletir suplementação"],
            "recomendacoes": [
                "Revisar suplementos em uso com o profissional",
                "Manter acompanhamento se indicado",
            ],
        },
    },
    "ferritina": {
        "baixo": {
            "sintomas_possiveis": [
                "Cansaço, queda de cabelo ou unhas frágeis",
                "Falta de ar aos esforços e palidez",
            ],
            "recomendacoes": [
                "Avaliar ferro sérico e alimentação com o profissional",
                "Não tomar ferro sem orientação (risco de excesso)",
                "Investigar perdas ou má absorção se persistir",
            ],
        },
        "alto": {
            "sintomas_possiveis": [
                "Pode ser inflamação, infecção ou sobrecarga de ferro",
                "Em geral sem sintomas específicos isolados",
            ],
            "recomendacoes": [
                "Interpretar com PCR/hemograma e contexto clínico",
                "Evitar suplemento de ferro; discutir com o profissional",
            ],
        },
    },
    "psa_total": {
        "alto": {
            "sintomas_possiveis": [
                "Pode haver sintomas urinários (jato fraco, noctúria) ou nenhum sintoma",
                "Não diferencia sozinho hiperplasia, inflamação ou neoplasia",
            ],
            "recomendacoes": [
                "Avaliação urológica / com o profissional responsável",
                "Evitar ejaculação e exercício intenso antes de nova coleta, se orientado",
                "Não interpretar isoladamente — correlacionar PSA livre e exame clínico",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral favorável / esperado"],
            "recomendacoes": ["Manter rastreamento conforme idade e orientação profissional"],
        },
    },
    "psa_livre": {
        "baixo": {
            "sintomas_possiveis": ["Interpretar sempre em relação ao PSA total"],
            "recomendacoes": [
                "Calcular relação livre/total com o profissional",
                "Seguir avaliação urológica se indicada",
            ],
        },
        "alto": {
            "sintomas_possiveis": ["Depende da relação com o PSA total"],
            "recomendacoes": ["Discutir o conjunto PSA total + livre com o profissional"],
        },
    },
    "testosterona_total": {
        "baixo": {
            "sintomas_possiveis": [
                "Queda de libido, energia ou massa muscular",
                "Alteração de humor ou dificuldade de concentração",
            ],
            "recomendacoes": [
                "Sono, peso, estresse e atividade física influenciam o eixo hormonal",
                "Não usar hormônio sem indicação e acompanhamento profissional",
                "Reavaliar com testosterona livre/SHBG conforme orientação",
            ],
        },
        "alto": {
            "sintomas_possiveis": [
                "Acne, irritabilidade ou alterações do humor em alguns casos",
                "Pode refletir uso de hormônio ou outras causas",
            ],
            "recomendacoes": [
                "Revisar medicamentos/suplementos com o profissional",
                "Não ajustar hormônio por conta própria",
            ],
        },
    },
    "testosterona_livre": {
        "baixo": {
            "sintomas_possiveis": [
                "Fadiga, libido reduzida ou menor desempenho físico",
            ],
            "recomendacoes": [
                "Interpretar com testosterona total e SHBG",
                "Discutir sono, composição corporal e plano com o profissional",
            ],
        },
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar uso de hormônio ou variação laboratorial"],
            "recomendacoes": ["Confirmar com o profissional e evitar automedicação"],
        },
    },
    "shbg": {
        "alto": {
            "sintomas_possiveis": [
                "Pode reduzir a fração livre de hormônios sexuais",
                "Sintomas dependem do contexto (energia, libido)",
            ],
            "recomendacoes": [
                "Interpretar junto à testosterona total/livre",
                "Avaliar tireoide, fígado e medicações com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Pode acompanhar resistência à insulina ou excesso androgênico",
            ],
            "recomendacoes": [
                "Avaliar metabolismo e composição corporal com o profissional",
                "Reavaliar o painel hormonal completo",
            ],
        },
    },
    "tsh": {
        "alto": {
            "sintomas_possiveis": [
                "Cansaço, ganho de peso, pele seca ou intolerância ao frio",
                "Constipação ou humor deprimido em alguns casos",
            ],
            "recomendacoes": [
                "Avaliar T4 livre e sintomas com o profissional",
                "Não iniciar hormônio tireoidiano sem orientação",
            ],
        },
        "baixo": {
            "sintomas_possiveis": [
                "Palpitações, ansiedade, suor excessivo ou perda de peso",
                "Insônia ou intolerância ao calor",
            ],
            "recomendacoes": [
                "Avaliar T4 livre e quadro clínico",
                "Evitar automedicação tireoidiana",
            ],
        },
    },
    "t4_livre": {
        "alto": {
            "sintomas_possiveis": ["Sinais de hipertireoidismo (taquicardia, tremor, ansiedade)"],
            "recomendacoes": ["Avaliação conjunta com TSH pelo profissional"],
        },
        "baixo": {
            "sintomas_possiveis": ["Sinais de hipotireoidismo (cansaço, pele seca, edema)"],
            "recomendacoes": ["Avaliação conjunta com TSH; sem automedicação"],
        },
    },
    "creatinina": {
        "alto": {
            "sintomas_possiveis": [
                "Pode indicar redução da função renal ou desidratação",
                "Inchaço, náusea ou redução do volume urinário em casos avançados",
            ],
            "recomendacoes": [
                "Hidratação adequada (salvo restrição médica)",
                "Revisar anti-inflamatórios e outros medicamentos com o profissional",
                "Reavaliar função renal conforme orientação",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Pode refletir baixa massa muscular"],
            "recomendacoes": ["Interpretar com massa muscular e contexto clínico"],
        },
    },
    "ureia": {
        "alto": {
            "sintomas_possiveis": ["Pode acompanhar desidratação ou dieta rica em proteína"],
            "recomendacoes": [
                "Hidratação e revisão da dieta com o profissional",
                "Correlacionar com creatinina",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Pouco sintomático isoladamente"],
            "recomendacoes": ["Avaliar ingestão proteica e contexto clínico"],
        },
    },
    "tgo": {
        "alto": {
            "sintomas_possiveis": [
                "Pode ser assintomático ou haver desconforto abdominal",
                "Fadiga ou urina escura em lesões mais importantes",
            ],
            "recomendacoes": [
                "Evitar álcool e automedicação hepatotóxica",
                "Reavaliar enzimas e causas com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral sem significado clínico isolado"],
            "recomendacoes": ["Acompanhar se outros exames estiverem alterados"],
        },
    },
    "tgp": {
        "alto": {
            "sintomas_possiveis": [
                "Frequentemente assintomático",
                "Pode relacionar-se a esteatose, medicamentos ou álcool",
            ],
            "recomendacoes": [
                "Reduzir álcool e ultraprocessados; manter peso saudável",
                "Discutir investigação hepática com o profissional",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Em geral sem relevância isolada"],
            "recomendacoes": ["Manter hábitos saudáveis"],
        },
    },
    "pcr": {
        "alto": {
            "sintomas_possiveis": [
                "Marca inflamação; sintomas dependem da causa (dor, febre)",
            ],
            "recomendacoes": [
                "Investigar foco inflamatório/infeccioso com o profissional",
                "Reavaliar após tratamento da causa",
            ],
        },
        "baixo": {
            "sintomas_possiveis": ["Favorável / baixa inflamação sistêmica detectável"],
            "recomendacoes": ["Manter hábitos anti-inflamatórios (sono, atividade, alimentação)"],
        },
    },
}


def apoio_para_marcador(codigo: str | None, status: str | None) -> dict:
    """Retorna sintomas e recomendações para marcador fora da faixa; vazio se dentro/sem ref."""
    if not codigo or status not in ("alto", "baixo"):
        return {
            "sintomas_possiveis": [],
            "recomendacoes": [],
            "origem_apoio": "",
        }
    bloco = (CATALOGO_APOIO.get(codigo) or {}).get(status) or {}
    sintomas = list(bloco.get("sintomas_possiveis") or [])
    recomendacoes = list(bloco.get("recomendacoes") or [])
    if not sintomas and not recomendacoes:
        return {
            "sintomas_possiveis": [],
            "recomendacoes": [],
            "origem_apoio": "",
        }
    return {
        "sintomas_possiveis": sintomas,
        "recomendacoes": recomendacoes,
        "origem_apoio": "catalogo",
    }
