/**
 * Helpers para tipo de app.
 * Regras centralizadas: valem para todas as lojas criadas no sistema (por tipo_loja_nome da API).
 *
 * Apps ativos: CRM Vendas, Clínica da Beleza, Hotel / Pousada, Salão (cabeleireiro).
 * Clínica de Estética (legado) foi unificada em Clínica da Beleza — mesmo produto e rotas.
 */

const normalizarTipo = (tipo: string) =>
  tipo.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

export function isTipoClinicaBeleza(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  if (!s.includes('clinica')) return false;
  return s.includes('beleza') || s.includes('estetica');
}

/** @deprecated Alias de isTipoClinicaBeleza — stack clinica-estetica removido. */
export function isTipoClinicaEstetica(tipoLojaNome: string): boolean {
  return isTipoClinicaBeleza(tipoLojaNome);
}

/** Várias fontes (tipo da loja, plano, etc.) — qualquer uma basta. */
export function resolveIsClinicaBeleza(...hints: (string | undefined | null)[]): boolean {
  return hints.some((h) => h && isTipoClinicaBeleza(h));
}

export function isTipoCRMVendas(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('crm') || s.includes('vendas');
}

export function isTipoHotel(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('hotel') || s.includes('pousada') || s.includes('hospedagem');
}

export function isTipoCabeleireiro(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('cabeleireiro') || s.includes('salao') || s.includes('salon');
}

/** Rota de configurações do app (para voltar da tela de WhatsApp). */
export function configuracoesPathForTipo(slug: string, tipoLojaNome: string): string {
  if (isTipoClinicaBeleza(tipoLojaNome)) return `/loja/${slug}/clinica-beleza/configuracoes`;
  if (isTipoCRMVendas(tipoLojaNome)) return `/loja/${slug}/crm-vendas/configuracoes`;
  if (isTipoHotel(tipoLojaNome)) return `/loja/${slug}/hotel/configuracoes`;
  if (isTipoCabeleireiro(tipoLojaNome)) return `/loja/${slug}/cabeleireiro/configuracoes`;
  return `/loja/${slug}/dashboard`;
}

/** Rota principal do app conforme o tipo (voltar de páginas compartilhadas). */
export function homePathForTipo(slug: string, tipoLojaNome: string): string {
  if (isTipoCRMVendas(tipoLojaNome)) return `/loja/${slug}/crm-vendas`;
  if (isTipoClinicaBeleza(tipoLojaNome)) return `/loja/${slug}/clinica-beleza/consultas`;
  if (isTipoHotel(tipoLojaNome)) return `/loja/${slug}/hotel/reservas`;
  if (isTipoCabeleireiro(tipoLojaNome)) return `/loja/${slug}/dashboard`;
  return `/loja/${slug}/dashboard`;
}
