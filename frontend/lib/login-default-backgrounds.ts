/**
 * Imagens de fundo padrão da tela de login por tipo de loja.
 * Usadas quando a loja não definiu login_background nas configurações.
 */
import {
  isTipoCabeleireiro,
  isTipoClinicaBeleza,
  isTipoClinicaEstetica,
  isTipoCommerce,
  isTipoCRMVendas,
  isTipoHotel,
  isTipoRestaurante,
  isTipoServicos,
} from '@/lib/loja-tipo';

/** Arquivos em /public/login-backgrounds/ (adicione novos JPG por tipo quando quiser) */
const LOCAL = {
  clinicaBeleza: '/login-backgrounds/clinica-beleza.jpg',
  /** Demais tipos: reutilizam a arte de clínica até existir arquivo dedicado */
  clinicaEstetica: '/login-backgrounds/clinica-beleza.jpg',
  cabeleireiro: '/login-backgrounds/clinica-beleza.jpg',
  hotel: '/login-backgrounds/clinica-beleza.jpg',
  restaurante: '/login-backgrounds/clinica-beleza.jpg',
  crm: '/login-backgrounds/clinica-beleza.jpg',
  servicos: '/login-backgrounds/clinica-beleza.jpg',
  commerce: '/login-backgrounds/clinica-beleza.jpg',
  default: '/login-backgrounds/clinica-beleza.jpg',
} as const;

/**
 * Retorna URL do fundo padrão conforme o tipo da loja (nome vindo da API).
 */
export function getDefaultLoginBackground(tipoLojaNome: string): string {
  const tipo = (tipoLojaNome || '').trim();
  if (isTipoClinicaBeleza(tipo)) return LOCAL.clinicaBeleza;
  if (isTipoClinicaEstetica(tipo)) return LOCAL.clinicaEstetica;
  if (isTipoCabeleireiro(tipo)) return LOCAL.cabeleireiro;
  if (isTipoHotel(tipo)) return LOCAL.hotel;
  if (isTipoRestaurante(tipo)) return LOCAL.restaurante;
  if (isTipoCRMVendas(tipo)) return LOCAL.crm;
  if (isTipoServicos(tipo)) return LOCAL.servicos;
  if (isTipoCommerce(tipo)) return LOCAL.commerce;
  return LOCAL.default;
}

export function resolveLoginBackground(
  tipoLojaNome: string,
  loginBackground?: string | null,
): string {
  const custom = (loginBackground ?? '').trim();
  if (custom) return custom;
  return getDefaultLoginBackground(tipoLojaNome);
}
