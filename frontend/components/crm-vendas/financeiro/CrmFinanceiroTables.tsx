'use client';

import { Loader2 } from 'lucide-react';
import type { GrupoFinanceiro, LancamentoFinanceiro, TipoFinanceiro } from '@/hooks/crm-vendas/useCrmFinanceiroPage';
import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';

interface Props {
  itens: LancamentoFinanceiro[];
  tipo: TipoFinanceiro;
  onEdit: (item: LancamentoFinanceiro) => void;
  onPagar: (id: number) => void;
  onRemove: (item: LancamentoFinanceiro) => void;
}

export function CrmFinanceiroLancamentosTable({ itens, tipo, onEdit, onPagar, onRemove }: Props) {
  const cor = tipo === 'receita' ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400';

  if (!itens.length) {
    return (
      <p className="text-sm text-gray-500 dark:text-gray-400 py-8 text-center">
        Nenhum lançamento de {tipo === 'receita' ? 'receita' : 'despesa'} encontrado.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 dark:bg-gray-800/80">
          <tr>
            <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Vendedor</th>
            <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Descrição</th>
            <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Grupo</th>
            <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Vencimento</th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Valor</th>
            <th className="text-left py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Status</th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600 dark:text-gray-300">Ações</th>
          </tr>
        </thead>
        <tbody>
          {itens.map((item) => (
            <tr key={item.id} className="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
              <td className="py-2.5 px-3">{item.vendedor_nome}</td>
              <td className="py-2.5 px-3">
                {item.descricao}
                {item.origem === 'comissao_venda' && (
                  <span className="block text-xs text-[#0176d3]">Comissão automática</span>
                )}
              </td>
              <td className="py-2.5 px-3 text-gray-600 dark:text-gray-400">{item.grupo_nome || '—'}</td>
              <td className="py-2.5 px-3">{formatDate(item.data_vencimento)}</td>
              <td className={`py-2.5 px-3 text-right font-semibold ${cor}`}>
                {formatCurrency(item.valor)}
              </td>
              <td className="py-2.5 px-3">
                <span
                  className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                    item.status === 'pago'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300'
                      : item.status === 'cancelado'
                        ? 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                        : 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
                  }`}
                >
                  {item.status_display}
                </span>
              </td>
              <td className="py-2.5 px-3 text-right">
                <div className="flex flex-wrap gap-1 justify-end">
                  {item.status === 'pendente' && (
                    <button
                      type="button"
                      onClick={() => onPagar(item.id)}
                      className="px-2 py-1 text-xs rounded bg-green-600 text-white hover:bg-green-700"
                    >
                      Pagar
                    </button>
                  )}
                  {item.editavel && (
                    <>
                      <button
                        type="button"
                        onClick={() => onEdit(item)}
                        className="px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => onRemove(item)}
                        className="px-2 py-1 text-xs rounded border border-red-300 text-red-600 hover:bg-red-50 dark:border-red-800 dark:hover:bg-red-900/20"
                      >
                        Excluir
                      </button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CrmFinanceiroResumoCards({
  resumo,
  loading,
}: {
  resumo: {
    receitas_pagas: number;
    receitas_pendentes: number;
    despesas_pagas: number;
    despesas_pendentes: number;
    saldo_realizado: number;
    saldo_previsto: number;
    comissao_vendas_total: number;
  } | null;
  loading: boolean;
}) {
  if (loading && !resumo) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="w-8 h-8 animate-spin text-[#0176d3]" />
      </div>
    );
  }
  if (!resumo) return null;

  const cards = [
    { label: 'Receitas pagas', value: resumo.receitas_pagas, color: 'text-green-600' },
    { label: 'Receitas pendentes', value: resumo.receitas_pendentes, color: 'text-green-500' },
    { label: 'Despesas pagas', value: resumo.despesas_pagas, color: 'text-red-600' },
    { label: 'Saldo realizado', value: resumo.saldo_realizado, color: 'text-[#0176d3]' },
    { label: 'Comissão (vendas)', value: resumo.comissao_vendas_total, color: 'text-purple-600' },
    { label: 'Saldo previsto', value: resumo.saldo_previsto, color: 'text-gray-800 dark:text-gray-200' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-3 shadow-sm"
        >
          <p className="text-xs text-gray-500 dark:text-gray-400">{c.label}</p>
          <p className={`text-lg font-bold ${c.color}`}>{formatCurrency(c.value)}</p>
        </div>
      ))}
    </div>
  );
}

export function CrmFinanceiroGruposTable({
  grupos,
  isAdmin,
  onEdit,
  onRemove,
}: {
  grupos: GrupoFinanceiro[];
  isAdmin: boolean;
  onEdit: (g: GrupoFinanceiro) => void;
  onRemove: (g: GrupoFinanceiro) => void;
}) {
  const receitas = grupos.filter((g) => g.tipo === 'receita');
  const despesas = grupos.filter((g) => g.tipo === 'despesa');

  const renderLista = (lista: GrupoFinanceiro[], titulo: string) => (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">{titulo}</h3>
      <ul className="divide-y divide-gray-100 dark:divide-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        {lista.map((g) => (
          <li key={g.id} className="flex items-center justify-between px-3 py-2 text-sm">
            <span>
              {g.nome}
              {!g.is_active && (
                <span className="ml-2 text-xs text-gray-400">(inativo)</span>
              )}
            </span>
            {isAdmin && (
              <div className="flex gap-1">
                <button
                  type="button"
                  onClick={() => onEdit(g)}
                  className="px-2 py-1 text-xs rounded border hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  Editar
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(g)}
                  className="px-2 py-1 text-xs rounded border border-red-300 text-red-600"
                >
                  Excluir
                </button>
              </div>
            )}
          </li>
        ))}
        {!lista.length && (
          <li className="px-3 py-4 text-gray-500 text-sm">Nenhum grupo cadastrado.</li>
        )}
      </ul>
    </div>
  );

  return (
    <>
      {renderLista(receitas, 'Grupos de receitas')}
      {renderLista(despesas, 'Grupos de despesas')}
    </>
  );
}
