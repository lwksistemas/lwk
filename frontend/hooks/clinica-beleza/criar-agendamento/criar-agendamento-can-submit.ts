/** Regras para habilitar o botão Agendar no modal Novo Agendamento. */

export type CriarAgendamentoCanSubmitInput = {
  createLoading: boolean;
  patientId: number | "";
  professionalId: number | "";
  dateInput: string;
  time: string;
  nomeAgendaId: number | "";
  agendaEhProtocolo: boolean;
  protocoloClienteId: number | "";
  protocoloModeloId: number | "";
  protocolosClienteCarregando?: boolean;
  protocolosCarregando?: boolean;
  disponibilidadeError: string;
};

export function canSubmitCriarAgendamento(input: CriarAgendamentoCanSubmitInput): boolean {
  if (input.createLoading) return false;
  if (!input.patientId) return false;
  if (!input.professionalId) return false;
  if (!input.dateInput?.trim()) return false;
  if (!input.time?.trim()) return false;
  if (!input.nomeAgendaId) return false;
  if (input.disponibilidadeError) return false;

  if (input.agendaEhProtocolo) {
    if (input.protocolosClienteCarregando || input.protocolosCarregando) return false;
    if (!input.protocoloClienteId && !input.protocoloModeloId) return false;
  }

  return true;
}
