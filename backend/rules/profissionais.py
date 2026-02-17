"""
Regras de profissionais: horário, folgas, limite de atendimentos por dia.
Respeitado indiretamente via BloqueioHorario; aqui podem ser adicionadas
regras extras (ex.: limite de N atendimentos/dia por profissional).
"""
# Regras futuras: limite de atendimentos por dia, horário do profissional, etc.
# Por ora mantemos apenas a estrutura; conflitos e bloqueios já estão em agenda.py e nas views.

regras_profissionais = []
