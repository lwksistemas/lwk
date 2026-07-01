'use client';

import type { OportunidadeItem } from '@/components/crm-vendas/modals/ModalPropostaForm';
import { formatCrmBrl } from '@/lib/crm-utils';

const RECORRENCIA_LABEL: Record<string, string> = {
  unico: 'Único',
  mensal: 'Mensal',
  trimestral: 'Trimestral',
  anual: 'Anual',
};

interface Props {
  itens: OportunidadeItem[];
}

export default function CrmOportunidadeItensTabela({ itens }: Props) {
  if (itens.length === 0) {
    return <p className="text-xs text-gray-500">Esta oportunidade não possui produtos ou serviços cadastrados.</p>;
  }

  const valorUnico = itens
    .filter((i) => !i.produto_servico_recorrencia || i.produto_servico_recorrencia === 'unico')
    .reduce((s, i) => s + i.subtotal, 0);
  const valorMensal = itens
    .filter((i) => i.produto_servico_recorrencia === 'mensal')
    .reduce((s, i) => s + i.subtotal, 0);
  const valorTrimestral = itens
    .filter((i) => i.produto_servico_recorrencia === 'trimestral')
    .reduce((s, i) => s + i.subtotal, 0);
  const valorAnual = itens
    .filter((i) => i.produto_servico_recorrencia === 'anual')
    .reduce((s, i) => s + i.subtotal, 0);

  return (
    <>
      <div className="rounded-lg border border-gray-200 dark:border-neutral-600 overflow-x-auto">
        <table className="w-full text-sm min-w-[480px]">
          <thead>
            <tr className="bg-gray-50 dark:bg-[#0d1f3c]/50">
              <th className="text-left py-2 px-3 font-medium">Item</th>
              <th className="text-center py-2 px-3 font-medium">Recorrência</th>
              <th className="text-right py-2 px-3 font-medium">Qtd</th>
              <th className="text-right py-2 px-3 font-medium">Preço Unit.</th>
              <th className="text-right py-2 px-3 font-medium">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((item) => (
              <tr key={item.id} className="border-t border-gray-100 dark:border-[#0d1f3c]">
                <td className="py-2 px-3">
                  <span className="text-xs text-gray-500 dark:text-gray-400 mr-1">
                    {item.produto_servico_tipo === 'produto' ? 'Produto' : 'Serviço'}:
                  </span>
                  {item.produto_servico_nome}
                </td>
                <td className="py-2 px-3 text-center">
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded ${
                      item.produto_servico_recorrencia === 'mensal'
                        ? 'bg-blue-100 text-blue-700'
                        : item.produto_servico_recorrencia === 'anual'
                          ? 'bg-purple-100 text-purple-700'
                          : item.produto_servico_recorrencia === 'trimestral'
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {RECORRENCIA_LABEL[item.produto_servico_recorrencia || 'unico'] || 'Único'}
                  </span>
                </td>
                <td className="py-2 px-3 text-right">{item.quantidade}</td>
                <td className="py-2 px-3 text-right">{formatCrmBrl(item.preco_unitario)}</td>
                <td className="py-2 px-3 text-right font-medium">{formatCrmBrl(item.subtotal)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {(valorMensal > 0 || valorTrimestral > 0 || valorAnual > 0) && (
        <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800 space-y-1">
          {valorUnico > 0 && (
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <span className="font-medium">Adesão/Implantação:</span> {formatCrmBrl(valorUnico)}
            </p>
          )}
          {valorMensal > 0 && (
            <p className="text-sm text-blue-700 dark:text-blue-300 font-semibold">
              Valor Mensal: {formatCrmBrl(valorMensal)}/mês
            </p>
          )}
          {valorTrimestral > 0 && (
            <p className="text-sm text-indigo-700 dark:text-indigo-300 font-semibold">
              Valor Trimestral: {formatCrmBrl(valorTrimestral)}/trimestre
            </p>
          )}
          {valorAnual > 0 && (
            <p className="text-sm text-purple-700 dark:text-purple-300 font-semibold">
              Valor Anual: {formatCrmBrl(valorAnual)}/ano
            </p>
          )}
        </div>
      )}
    </>
  );
}
