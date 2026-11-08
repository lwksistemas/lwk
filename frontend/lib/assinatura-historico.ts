import { cobrancaBoletoPixDisponivel } from '@/lib/assinatura-aviso';

/** Número curto da NFS-e. A chave de acesso (50 dígitos) não aparece na tela. */
export function numeroNotaParaExibir(numero?: string | null): string {
  const bruto = (numero || '').trim();
  if (!bruto) return '';
  const digitos = bruto.replace(/\D/g, '');
  if (digitos.length === 50 && digitos === bruto.replace(/\s/g, '')) {
    return digitos.slice(23, 36).replace(/^0+/, '');
  }
  if (digitos.length >= 20 && digitos === bruto.replace(/\s/g, '')) return '';
  return bruto;
}

export function rotuloNotaFiscal(numero?: string | null): string {
  const n = numeroNotaParaExibir(numero);
  return n ? `NF ${n}` : '';
}

type LinhaBoleto = {
  is_paid?: boolean;
  data_vencimento?: string | null;
  pagamento_loja_id?: number;
  id?: number;
  pode_baixar_boleto?: boolean;
  boleto_url?: string;
  asaas_id?: string;
  mercadopago_payment_id?: string;
};

/** Há boleto ou PIX para abrir agora. Mensagem de “ainda não” e traço de pago não contam. */
export function linhaTemBoletoDisponivel(item: LinhaBoleto): boolean {
  if (item.is_paid) return false;
  if (!cobrancaBoletoPixDisponivel(item.data_vencimento).disponivel) return false;
  if (item.pode_baixar_boleto === false) return false;
  const pid = item.pagamento_loja_id || item.id || 0;
  return (
    pid > 0 ||
    Boolean(item.boleto_url) ||
    Boolean(item.asaas_id) ||
    Boolean(item.mercadopago_payment_id)
  );
}

type CobrancaAbertaBoleto = {
  data_vencimento?: string | null;
  boleto_url?: string;
  pagamento_id?: number;
  pix_copy_paste?: string;
};

export function cobrancaAbertaTemBoleto(cobranca: CobrancaAbertaBoleto): boolean {
  if (!cobrancaBoletoPixDisponivel(cobranca.data_vencimento).disponivel) return false;
  return Boolean(cobranca.boleto_url || cobranca.pagamento_id || cobranca.pix_copy_paste);
}

export function deveMostrarProximaMensalidade(
  itens: { is_paid: boolean; data_vencimento?: string | null }[],
  proximaCobranca?: string | null,
  temCobrancaAberta?: boolean,
): boolean {
  if (!proximaCobranca || temCobrancaAberta) return false;
  const vencimento = proximaCobranca.slice(0, 10);
  const jaListado = itens.some(
    (item) => !item.is_paid && (item.data_vencimento || "").slice(0, 10) === vencimento,
  );
  return !jaListado;
}
