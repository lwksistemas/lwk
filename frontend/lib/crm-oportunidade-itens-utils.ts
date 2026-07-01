import type { CrmOportunidadeProdutoOption } from '@/lib/crm-oportunidade-form-types';

export interface OportunidadeItemRow {
  id?: number;
  produto_servico_id: number;
  quantidade: string;
  preco_unitario: string;
}

export function calcularTotalOportunidadeItens(itens: OportunidadeItemRow[]): number {
  return itens.reduce(
    (s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0),
    0,
  );
}

export function atualizarOportunidadeItem(
  itens: OportunidadeItemRow[],
  idx: number,
  field: 'produto_servico_id' | 'quantidade' | 'preco_unitario',
  value: string | number,
  produtos: CrmOportunidadeProdutoOption[],
): OportunidadeItemRow[] {
  return itens.map((item, i) => {
    if (i !== idx) return item;
    const updated = {
      ...item,
      [field]: field === 'produto_servico_id' ? Number(value) : String(value),
    };
    if (field === 'produto_servico_id') {
      const ps = produtos.find((p) => p.id === Number(value));
      if (ps) updated.preco_unitario = ps.preco;
    }
    return updated;
  });
}
