'use client';

import { useState } from 'react';
import { formatCurrency } from '@/lib/financeiro-helpers';
import { LojaInfo } from '@/types/dashboard';

export function ModalPipeline({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [etapas] = useState([
    { id: 1, nome: 'Prospecção', leads: 12, valor: 45000, cor: '#3B82F6' },
    { id: 2, nome: 'Qualificação', leads: 8, valor: 32000, cor: '#8B5CF6' },
    { id: 3, nome: 'Proposta', leads: 5, valor: 25000, cor: '#F59E0B' },
    { id: 4, nome: 'Negociação', leads: 3, valor: 18000, cor: '#10B981' },
    { id: 5, nome: 'Fechamento', leads: 2, valor: 12000, cor: '#059669' }
  ]);

  const totalLeads = etapas.reduce((sum, e) => sum + e.leads, 0);
  const totalValor = etapas.reduce((sum, e) => sum + e.valor, 0);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-5xl w-full max-h-[80vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6 dark:text-white" style={{ color: loja.cor_primaria }}>
          🔄 Pipeline de Vendas
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total de Leads</p>
            <p className="text-2xl font-bold dark:text-white">{totalLeads}</p>
          </div>
          <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Valor Total</p>
            <p className="text-2xl font-bold dark:text-white">{formatCurrency(totalValor)}</p>
          </div>
          <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Taxa Conversão</p>
            <p className="text-2xl font-bold dark:text-white">16.7%</p>
          </div>
          <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Ticket Médio</p>
            <p className="text-2xl font-bold dark:text-white">{formatCurrency(Math.round(totalValor / totalLeads))}</p>
          </div>
        </div>

        <div className="space-y-4">
          {etapas.map((etapa) => (
            <div key={etapa.id} className="border dark:border-gray-600 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: etapa.cor }}></div>
                  <h4 className="font-semibold text-lg dark:text-white">{etapa.nome}</h4>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600 dark:text-gray-400">{etapa.leads} leads</p>
                  <p className="font-bold dark:text-white">{formatCurrency(etapa.valor)}</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="h-2 rounded-full transition-all" 
                  style={{ width: `${(etapa.leads / totalLeads) * 100}%`, backgroundColor: etapa.cor }}></div>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3 pt-6 border-t dark:border-gray-600 mt-6">
          <button onClick={onClose} className="px-6 py-2 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white">
            Fechar
          </button>
          <button className="px-6 py-2 text-white rounded-lg" style={{ backgroundColor: loja.cor_primaria }}>
            📊 Relatório Completo
          </button>
        </div>
      </div>
    </div>
  );
}
