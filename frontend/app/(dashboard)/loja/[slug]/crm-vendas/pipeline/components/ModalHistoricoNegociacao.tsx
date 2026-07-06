'use client';

import { Pencil, X } from 'lucide-react';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import HistoricoNegociacaoSection from '@/components/crm-vendas/HistoricoNegociacaoSection';
import { formatCrmBrl, rotuloExibicaoOportunidade, subtituloModalOportunidade } from '@/lib/crm-utils';

interface Props {
  oportunidade: Oportunidade;
  etapas: { key: string; label: string }[];
  onClose: () => void;
  onEditar: () => void;
}

export default function ModalHistoricoNegociacao({ oportunidade, etapas, onClose, onEditar }: Props) {
  const resumoSubtitulo = subtituloModalOportunidade(oportunidade);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl max-h-[95vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="min-w-0 pr-2">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Histórico de negociação
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
              {rotuloExibicaoOportunidade(oportunidade)}
              {resumoSubtitulo ? ` · ${resumoSubtitulo}` : ''}
            </p>
            <p className="text-sm font-semibold text-green-600 dark:text-green-400 mt-0.5">
              {formatCrmBrl(oportunidade.valor)}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 flex-shrink-0"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-4">
          <HistoricoNegociacaoSection
            oportunidade={oportunidade}
            etapas={etapas}
            motivoPerda={oportunidade.motivo_perda || undefined}
            feedbackPosVenda={oportunidade.feedback_pos_venda || undefined}
            variant="modal"
          />
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0 flex gap-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Fechar
          </button>
          <button
            type="button"
            onClick={onEditar}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium"
          >
            <Pencil size={16} />
            Editar oportunidade
          </button>
        </div>
      </div>
    </div>
  );
}
