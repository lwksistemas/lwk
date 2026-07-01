'use client';

import Link from 'next/link';
import { X } from 'lucide-react';
import ProdutoSeletorCategoria from '@/components/crm-vendas/ProdutoSeletorCategoria';
import type { CrmOportunidadeProdutoOption } from '@/lib/crm-oportunidade-form-types';
import type { OportunidadeItemRow } from '@/lib/crm-oportunidade-itens-utils';

interface Props {
  slug: string;
  produtos: CrmOportunidadeProdutoOption[];
  itens: OportunidadeItemRow[];
  seletorAberto: boolean;
  onSeletorAbertoChange: (aberto: boolean) => void;
  onUpdateItem: (
    idx: number,
    field: 'produto_servico_id' | 'quantidade' | 'preco_unitario',
    value: string | number,
  ) => void;
  onRemoveItem: (idx: number) => void;
  onAddProduto: (produto: CrmOportunidadeProdutoOption) => void;
  layout?: 'modal' | 'page';
  showHeader?: boolean;
}

export default function OportunidadeItensEditor({
  slug,
  produtos,
  itens,
  seletorAberto,
  onSeletorAbertoChange,
  onUpdateItem,
  onRemoveItem,
  onAddProduto,
  layout = 'modal',
  showHeader = true,
}: Props) {
  const isPage = layout === 'page';

  return (
    <div>
      {showHeader && (
        <div
          className={`flex items-center justify-between ${isPage ? 'border-b border-gray-100 dark:border-[#0d1f3c] pb-2 mb-0' : 'mb-1'}`}
        >
          <label
            className={
              isPage
                ? 'text-sm font-semibold text-gray-800 dark:text-gray-200'
                : 'block text-sm font-medium text-gray-700 dark:text-gray-300'
            }
          >
            {isPage ? 'Produtos e serviços' : 'Produtos e Serviços'}
          </label>
          <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="text-xs text-[#0176d3] hover:underline">
            Cadastrar
          </Link>
        </div>
      )}
      {itens.map((item, idx) => {
        const ps = produtos.find((p) => p.id === item.produto_servico_id);
        return (
          <div
            key={item.id ?? `new-${idx}`}
            className={`flex gap-2 mb-2 items-center rounded-lg px-2 py-1.5 ${
              isPage ? 'bg-gray-50 dark:bg-[#1e3a5f] px-3 py-2' : 'bg-gray-50 dark:bg-gray-700/50'
            }`}
          >
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                {ps?.codigo ? <span className="text-gray-400">[{ps.codigo}] </span> : null}
                {ps?.nome || 'Produto'}
              </p>
              {ps?.categoria_nome && (
                <p className={`text-[10px] text-gray-500 ${isPage ? 'dark:text-gray-400' : ''}`}>{ps.categoria_nome}</p>
              )}
            </div>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={item.preco_unitario}
              onChange={(e) => onUpdateItem(idx, 'preco_unitario', e.target.value)}
              className={`px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 ${
                isPage ? 'w-24 py-1.5 rounded-lg dark:bg-[#264a73] dark:border-neutral-600' : 'w-20'
              }`}
              placeholder="Preço"
            />
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={item.quantidade}
              onChange={(e) => onUpdateItem(idx, 'quantidade', e.target.value)}
              className={`px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 ${
                isPage ? 'w-16 py-1.5 rounded-lg dark:bg-[#264a73] dark:border-neutral-600' : 'w-14'
              }`}
              placeholder="Qtd"
            />
            <button
              type="button"
              onClick={() => onRemoveItem(idx)}
              className={`rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 ${isPage ? 'p-1.5 transition' : 'p-1'}`}
            >
              <X size={isPage ? 14 : 13} />
            </button>
          </div>
        );
      })}
      {seletorAberto && produtos.length > 0 && (
        <div className={isPage ? '' : 'mb-2'}>
          <ProdutoSeletorCategoria
            produtos={produtos}
            itensSelecionados={itens.map((i) => i.produto_servico_id)}
            onSelecionar={(ps) => {
              onAddProduto(ps);
              onSeletorAbertoChange(false);
            }}
            onFechar={() => onSeletorAbertoChange(false)}
          />
        </div>
      )}
      {produtos.length > 0 && !seletorAberto && (
        <button
          type="button"
          onClick={() => onSeletorAbertoChange(true)}
          className={`text-sm text-[#0176d3] hover:underline ${isPage ? 'font-medium' : ''}`}
        >
          + Adicionar item
        </button>
      )}
      {produtos.length === 0 && (
        <p className="text-xs text-amber-600 dark:text-amber-400">
          Cadastre produtos/serviços em{' '}
          <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="underline font-medium">
            Produtos e Serviços
          </Link>
          .
        </p>
      )}
    </div>
  );
}
