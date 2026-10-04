import { CLINICA_BELEZA_NAV_ITEMS } from '@/components/clinica-beleza/clinica-beleza-nav';

/** Telas ligadas no hub de relatórios, fora do item único do menu. */
export const ROTAS_RELATORIOS_CLINICA = [
  'relatorios/comissoes',
  'relatorios/repasse-consultas',
  'relatorios/faturamento',
  'relatorios/lancamentos',
  'relatorios/descontos',
  'relatorios/venda-prazo',
  'relatorios/inadimplentes',
] as const;

/** Telas reais que não aparecem como item próprio do menu. */
const ROTAS_EXTRAS = [
  'clinica-beleza/consultas/nova',
  'clinica-beleza/procedimentos-realizados',
  'clinica-beleza/profissionais',
  'clinica-beleza/convenios',
  ...ROTAS_RELATORIOS_CLINICA,
] as const;

function caminhoMenu(path: string): string {
  return path.replace(/\/$/, '').split('?')[0];
}

const rotasMenu = CLINICA_BELEZA_NAV_ITEMS.flatMap((item) => {
  const caminhos: string[] = [];
  if (item.path) caminhos.push(caminhoMenu(item.path));
  for (const filho of item.children ?? []) caminhos.push(caminhoMenu(filho.path));
  return caminhos;
});

/** Segmento depois de `/loja/[slug]/`. O menu entra primeiro; o restante só se ainda não estiver. */
export const ROTAS_CLINICA_E2E = [
  ...rotasMenu,
  ...ROTAS_EXTRAS.filter((rota) => !rotasMenu.includes(rota)),
] as const;

export type RotaClinicaE2E = (typeof ROTAS_CLINICA_E2E)[number];
