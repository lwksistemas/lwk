export interface CrmPropostaAssinaturaFields {
  status: string;
  status_assinatura?: string;
}

export function propostaOcultaColunaAssinatura(p: CrmPropostaAssinaturaFields): boolean {
  return (
    p.status === 'cancelada' ||
    p.status === 'pedido' ||
    p.status_assinatura === 'concluido'
  );
}

export type PropostasConfirmAction =
  | { type: 'marcar_assinado'; id: number; titulo: string }
  | { type: 'confirmar_pedido'; id: number; titulo: string }
  | null;

export function propostaConfirmCopy(confirmAction: PropostasConfirmAction) {
  if (!confirmAction) return null;
  if (confirmAction.type === 'marcar_assinado') {
    return {
      title: 'Marcar como assinada',
      message: `Marcar "${confirmAction.titulo}" como assinada manualmente?\n\nUse quando o cliente assinar de outra forma (manual, gov.br, etc).`,
      confirmLabel: 'Marcar assinada',
      variant: 'primary' as const,
    };
  }
  return {
    title: 'Confirmar pedido',
    message: `Confirmar "${confirmAction.titulo}" como pedido?\n\nIsso indica que o cliente confirmou o pedido formal e está pronto para gerar o contrato.`,
    confirmLabel: 'Confirmar pedido',
    variant: 'primary' as const,
  };
}
