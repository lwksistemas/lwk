export const DAYS_TO_WARN_UI = 5;
export const DAYS_TO_BLOCK = 5;

export type AssinaturaAviso = {
  nivel: 'aviso' | 'urgente' | 'critico';
  mensagem: string;
  dias_restantes?: number;
  dias_atraso?: number;
  dias_ate_bloqueio?: number;
  data_vencimento?: string;
};

function parseDateOnly(iso: string): Date {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
  return new Date(y, m - 1, d);
}

function daysBetween(a: Date, b: Date): number {
  const ms = b.getTime() - a.getTime();
  return Math.round(ms / 86400000);
}

/** Fallback no frontend quando heartbeat ainda não retornou assinatura_aviso. */
export function calcularAvisoAssinaturaLocal(
  dataProximaCobranca: string | null | undefined,
  isBlocked = false,
): AssinaturaAviso | null {
  if (isBlocked || !dataProximaCobranca) return null;

  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  const venc = parseDateOnly(dataProximaCobranca);
  const diasPara = daysBetween(hoje, venc);

  if (diasPara > DAYS_TO_WARN_UI) return null;

  const data_vencimento = dataProximaCobranca.slice(0, 10);

  if (diasPara >= 1) {
    const diaLabel = diasPara === 1 ? 'dia' : 'dias';
    return {
      nivel: 'aviso',
      dias_restantes: diasPara,
      data_vencimento,
      mensagem: `Faltam ${diasPara} ${diaLabel} para vencer a assinatura. Efetue o pagamento para evitar o bloqueio do sistema.`,
    };
  }

  if (diasPara === 0) {
    return {
      nivel: 'urgente',
      dias_restantes: 0,
      data_vencimento,
      mensagem: 'Sua assinatura vence hoje. Efetue o pagamento para evitar o bloqueio do sistema.',
    };
  }

  const diasAtraso = -diasPara;
  if (diasAtraso > 0 && diasAtraso < DAYS_TO_BLOCK) {
    const diasAteBloqueio = DAYS_TO_BLOCK - diasAtraso;
    return {
      nivel: 'critico',
      dias_atraso: diasAtraso,
      dias_ate_bloqueio: diasAteBloqueio,
      data_vencimento,
      mensagem: `Assinatura vencida há ${diasAtraso} ${diasAtraso === 1 ? 'dia' : 'dias'}. O sistema será bloqueado em ${diasAteBloqueio} ${diasAteBloqueio === 1 ? 'dia' : 'dias'} se o pagamento não for efetuado.`,
    };
  }

  return null;
}
