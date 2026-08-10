/**
 * Presets de Atividade Municipal (ISSNet Ribeirão Preto / NFS-e Nacional).
 * cTribNac = tributação nacional (6 dígitos); cTribMun = código municipal do contribuinte.
 */

export type NfseAtividadeMunicipal = {
  id: string;
  label: string;
  /** Vazio = usar configuração padrão da loja */
  cnae: string;
  item_lista: string;
  /** cTribNac — 6 dígitos */
  trib_nac: string;
  /** cTribMun — 6 dígitos cadastrados no ISSNet */
  trib_mun: string;
};

export const NFSE_ATIVIDADES_MUNICIPAIS: NfseAtividadeMunicipal[] = [
  {
    id: 'loja',
    label: 'Usar configuração padrão da loja',
    cnae: '',
    item_lista: '',
    trib_nac: '',
    trib_mun: '',
  },
  {
    // cTribMun 170602 = código cadastrado no ISSNet RP para este contribuinte
    // (cTribNac 170601). Mesmo padrão de 14.01 → nac 140101 / mun 140118.
    id: '170601',
    label: '17.06.01 — Promoção de Vendas e Negócios',
    cnae: '7319002',
    item_lista: '17.06',
    trib_nac: '170601',
    trib_mun: '170602',
  },
  {
    id: '140118',
    label: '14.01 — Manutenção de Computadores',
    cnae: '9511800',
    item_lista: '14.01',
    trib_nac: '140101',
    trib_mun: '140118',
  },
  {
    id: '101002',
    label: '46.18 — Representação Comercial',
    cnae: '4618402',
    item_lista: '46.18',
    trib_nac: '461801',
    trib_mun: '101002',
  },
  {
    id: '4751',
    label: '47.51 — Comércio de Informática',
    cnae: '4751201',
    item_lista: '47.51',
    trib_nac: '140101',
    trib_mun: '140118',
  },
];

export function encontrarAtividadeMunicipal(params: {
  cnae?: string;
  codigo_servico?: string;
  item_lista_servico?: string;
  codigo_tributacao_nacional?: string;
}): number {
  const cnae = params.cnae || '';
  const mun = params.codigo_servico || '';
  const item = params.item_lista_servico || '';
  const nac = params.codigo_tributacao_nacional || '';

  if (!cnae && !mun && !item && !nac) {
    return 0;
  }

  const idx = NFSE_ATIVIDADES_MUNICIPAIS.findIndex(
    (a) =>
      a.id !== 'loja' &&
      a.cnae === cnae &&
      a.trib_mun === mun &&
      a.item_lista === item &&
      (nac === '' || a.trib_nac === nac),
  );
  return idx >= 0 ? idx : 0;
}
