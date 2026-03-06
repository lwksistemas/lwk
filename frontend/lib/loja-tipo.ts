/**
 * Helpers para tipo de app.
 * Regras centralizadas: valem para todas as lojas criadas no sistema (por tipo_loja_nome da API).
 */

const normalizarTipo = (tipo: string) =>
  tipo.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

export function isTipoClinicaEstetica(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('clinica') && s.includes('estetica');
}

export function isTipoClinicaBeleza(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('clinica') && s.includes('beleza');
}

export function isTipoRestaurante(tipoLojaNome: string): boolean {
  return normalizarTipo(tipoLojaNome).includes('restaurante');
}

export function isTipoCabeleireiro(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('cabeleireiro') || s.includes('salao') || s.includes('barbearia');
}

export function isTipoCommerce(tipoLojaNome: string): boolean {
  return normalizarTipo(tipoLojaNome).includes('commerce');
}

export function isTipoCRMVendas(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('crm') || s.includes('vendas');
}

export function isTipoServicos(tipoLojaNome: string): boolean {
  const s = normalizarTipo(tipoLojaNome);
  return s.includes('servicos') || s.includes('servico');
}
