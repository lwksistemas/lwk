from django.utils.timezone import now

from .valores import _consulta_defaults_from_appointment


def sync_consulta_from_appointment_status(appointment, new_status, old_status=None):
    """
    Cria ou atualiza Consulta conforme o novo status do agendamento.
    Retorna a Consulta afetada ou None.
    """
    from clinica_beleza import consulta_service

    if new_status == old_status:
        return getattr(appointment, 'consulta', None)

    ts = now()

    if new_status == 'CONFIRMED':
        consulta, created = consulta_service.Consulta.objects.get_or_create(
            appointment=appointment,
            defaults=_consulta_defaults_from_appointment(appointment, status='SCHEDULED'),
        )
        if not created and consulta.status not in ('IN_PROGRESS', 'COMPLETED'):
            consulta.status = 'SCHEDULED'
            consulta.save(update_fields=['status', 'updated_at'])
        return consulta

    if new_status in ('CLIENT_CONFIRMED', 'PHONE_CONFIRMED'):
        return None

    if new_status == 'IN_PROGRESS':
        consulta, created = consulta_service.Consulta.objects.get_or_create(
            appointment=appointment,
            defaults=_consulta_defaults_from_appointment(
                appointment, status='IN_PROGRESS', data_inicio=ts,
            ),
        )
        if not created:
            consulta.status = 'IN_PROGRESS'
            if not consulta.data_inicio:
                consulta.data_inicio = ts
            consulta.save(update_fields=['status', 'data_inicio', 'updated_at'])
        return consulta

    if new_status == 'COMPLETED':
        try:
            consulta = appointment.consulta
        except consulta_service.Consulta.DoesNotExist:
            consulta = consulta_service.Consulta.objects.create(
                appointment=appointment,
                **_consulta_defaults_from_appointment(
                    appointment, status='COMPLETED', data_inicio=ts, data_fim=ts,
                ),
            )
            return consulta
        consulta.status = 'COMPLETED'
        if not consulta.data_inicio:
            consulta.data_inicio = ts
        consulta.data_fim = ts
        consulta.save(update_fields=['status', 'data_inicio', 'data_fim', 'updated_at'])
        return consulta

    if new_status in ('CANCELLED', 'NO_SHOW'):
        try:
            consulta = appointment.consulta
        except consulta_service.Consulta.DoesNotExist:
            consulta = consulta_service.Consulta.objects.create(
                appointment=appointment,
                **_consulta_defaults_from_appointment(appointment, status='CANCELLED'),
            )
            return consulta
        if consulta.status not in ('IN_PROGRESS', 'COMPLETED'):
            consulta.status = 'CANCELLED'
            consulta.save(update_fields=['status', 'updated_at'])
        return consulta

    return None
