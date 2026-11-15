/**
 * Helpers para tipo de app.
 * Regras centralizadas: valem para todas as lojas criadas no sistema (por tipo_loja_nome da API).
 *
 * Apps em produção: CRM Vendas e Clínica da Beleza.
 * Salão de Cabeleireiro entra com frontend, container e assetPrefix próprios.
 * Clínica de Estética (legado) foi unificada em Clínica da Beleza — mesmo produto e rotas.
 * Um tipo novo nasce do zero e ganha frontend separado (container, nginx e assetPrefix).
 */

const normalizarTipo = (tipo: string) =>
  tipo.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

export function isTipoClinicaBeleza(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  if (!s.includes('clinica')) return false;
  if (s.includes('radiolog') || s.includes('geral') || s.includes('consultorio')) return false;
  return s.includes('beleza') || s.includes('estetica');
}

/** Várias fontes (tipo da loja, plano, etc.) — qualquer uma basta. */
export function resolveIsClinicaBeleza(...hints: (string | undefined | null)[]): boolean {
  return hints.some((h) => h && isTipoClinicaBeleza(h));
}

export function isTipoCRMVendas(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('crm') || s.includes('vendas');
}

export function isTipoSalaoCabeleireiro(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  if (s.includes('clinica')) return false;
  return s.includes('cabeleireiro') || s.includes('cabelereiro') || s.includes('salao');
}

export function aplicarCookieAppLoja(tipoLojaNome: string): void {
  if (typeof document === 'undefined') return;
  document.cookie = 'loja_usa_crm=; path=/; max-age=0';
  document.cookie = 'loja_usa_salao=; path=/; max-age=0';
  if (isTipoCRMVendas(tipoLojaNome)) {
    document.cookie = 'loja_usa_crm=1; path=/; max-age=86400; SameSite=Lax';
  } else if (isTipoSalaoCabeleireiro(tipoLojaNome)) {
    document.cookie = 'loja_usa_salao=1; path=/; max-age=86400; SameSite=Lax';
  }
}

export function homePathFromAppCookie(slug: string, crm: boolean, salao: boolean): string {
  if (crm) return `/loja/${slug}/crm-vendas`;
  if (salao) return `/loja/${slug}/salao-cabeleireiro`;
  return `/loja/${slug}/dashboard`;
}

/** Rota de configurações do app (para voltar da tela de WhatsApp). */
export function configuracoesPathForTipo(slug: string, tipoLojaNome: string): string {
  if (isTipoClinicaBeleza(tipoLojaNome)) return `/loja/${slug}/clinica-beleza/configuracoes`;
  if (isTipoCRMVendas(tipoLojaNome)) return `/loja/${slug}/crm-vendas/configuracoes`;
  if (isTipoSalaoCabeleireiro(tipoLojaNome)) return `/loja/${slug}/salao-cabeleireiro/configuracoes`;
  return `/loja/${slug}/dashboard`;
}

/** Rota principal do app conforme o tipo (voltar de páginas compartilhadas). */
export function homePathForTipo(slug: string, tipoLojaNome: string): string {
  if (isTipoCRMVendas(tipoLojaNome)) return `/loja/${slug}/crm-vendas`;
  if (isTipoSalaoCabeleireiro(tipoLojaNome)) return `/loja/${slug}/salao-cabeleireiro`;
  if (isTipoClinicaBeleza(tipoLojaNome)) return `/loja/${slug}/dashboard`;
  return `/loja/${slug}/dashboard`;
}
