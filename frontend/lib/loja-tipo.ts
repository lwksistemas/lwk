/**
 * Helpers para tipo de app.
 * Regras centralizadas: valem para todas as lojas criadas no sistema (por tipo_loja_nome da API).
 *
 * Apps ativos: CRM Vendas, Clínica da Beleza, Clínica, Hotel / Pousada, Salão (cabeleireiro), Radiologia.
 * Clínica de Estética (legado) foi unificada em Clínica da Beleza — mesmo produto e rotas.
 */

const normalizarTipo = (tipo: string) =>
  tipo.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

export function isTipoClinicaGeral(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  if (s.includes('beleza') || s.includes('estetica') || s.includes('radiolog')) return false;
  if (s.includes('consultorio')) return true;
  if (s === 'clinica') return true;
  return s.includes('clinica') && (s.includes('geral') || s.includes('medica'));
}

export function isTipoClinicaBeleza(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  if (!s.includes('clinica')) return false;
  if (s.includes('radiolog') || s.includes('geral') || s.includes('consultorio')) return false;
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

export function isTipoRadiologia(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('radiolog') || s.includes('diagnostico por imagem');
}

/** Rota de configurações do app (para voltar da tela de WhatsApp). */
export function configuracoesPathForTipo(slug: string, tipoLojaNome: string): string {
  if (isTipoClinicaBeleza(tipoLojaNome)) return `/loja/${slug}/clinica-beleza/configuracoes`;
  if (isTipoCRMVendas(tipoLojaNome)) return `/loja/${slug}/crm-vendas/configuracoes`;
  if (isTipoHotel(tipoLojaNome)) return `/loja/${slug}/hotel/configuracoes`;
  if (isTipoCabeleireiro(tipoLojaNome)) return `/loja/${slug}/cabeleireiro/configuracoes`;
  if (isTipoRadiologia(tipoLojaNome)) return `/loja/${slug}/radiologia`;
  if (isTipoClinicaGeral(tipoLojaNome)) return `/loja/${slug}/clinica/configuracoes`;
  return `/loja/${slug}/dashboard`;
}

/** Rota principal do app conforme o tipo (voltar de páginas compartilhadas). */
export function homePathForTipo(slug: string, tipoLojaNome: string): string {
  if (isTipoCRMVendas(tipoLojaNome)) return `/loja/${slug}/crm-vendas`;
  if (isTipoClinicaBeleza(tipoLojaNome)) return `/loja/${slug}/clinica-beleza/prontuario`;
  if (isTipoClinicaGeral(tipoLojaNome)) return `/loja/${slug}/clinica/agenda`;
  if (isTipoHotel(tipoLojaNome)) return `/loja/${slug}/hotel/reservas`;
  if (isTipoCabeleireiro(tipoLojaNome)) return `/loja/${slug}/dashboard`;
  if (isTipoRadiologia(tipoLojaNome)) return `/loja/${slug}/radiologia`;
  return `/loja/${slug}/dashboard`;
}
