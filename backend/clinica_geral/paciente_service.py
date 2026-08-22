"""Filtros e arquivo lógico de pacientes."""
from django.db.models import Q

from .models import Paciente


def listar_pacientes(letra: str = "", busca: str = ""):
    qs = Paciente.objects.filter(is_active=True)
    letra = (letra or "").strip().upper()
    busca = (busca or "").strip()
    if letra and letra != "TODOS" and len(letra) == 1:
        qs = qs.filter(nome__istartswith=letra)
    if busca:
        qs = qs.filter(Q(nome__icontains=busca) | Q(nome_social__icontains=busca) | Q(cpf__icontains=busca))
    return qs.distinct()


def arquivar_paciente(paciente: Paciente) -> Paciente:
    paciente.is_active = False
    paciente.save(update_fields=["is_active", "updated_at"])
    return paciente
