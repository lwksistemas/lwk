'use client';

import { useState } from 'react';
import { MessageSquare, Printer } from 'lucide-react';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import {
  formatarDataHoraNegociacao,
  type TipoNotaNegociacao,
  useOportunidadeNotas,
} from '@/hooks/crm-vendas/useOportunidadeNotas';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail, rotuloExibicaoOportunidade } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';

interface Props {
  oportunidade: Oportunidade;
  etapas: { key: string; label: string }[];
  motivoPerda?: string;
  feedbackPosVenda?: string;
  /** embedded = dentro do modal Editar; modal = modal dedicado de histórico */
  variant?: 'embedded' | 'modal';
}

export default function HistoricoNegociacaoSection({
  oportunidade,
  variant = 'embedded',
}: Props) {
  const toast = useToast();
  const { notas, loading, salvando, erro, adicionarNota } = useOportunidadeNotas(oportunidade.id);
  const [tipoNova, setTipoNova] = useState<TipoNotaNegociacao>('resposta_cliente');
  const [textoNova, setTextoNova] = useState('');
  const [formErro, setFormErro] = useState<string | null>(null);
  const [imprimindo, setImprimindo] = useState(false);

  const handleAdicionar = async () => {
    if (!textoNova.trim()) {
      setFormErro('Escreva a resposta ou nota antes de salvar.');
      return;
    }
    setFormErro(null);
    try {
      await adicionarNota(tipoNova, textoNova);
      setTextoNova('');
    } catch {
      /* erro já em hook */
    }
  };

  const handleImprimir = async () => {
    setImprimindo(true);
    try {
      const res = await apiClient.get(
        `/crm-vendas/oportunidades/${oportunidade.id}/historico-pdf/`,
        { responseType: 'blob' },
      );
      const blob = res.data instanceof Blob
        ? res.data
        : new Blob([res.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const janela = window.open(url, '_blank', 'noopener');
      if (!janela) {
        const link = document.createElement('a');
        link.href = url;
        link.download = `historico-negociacao-${rotuloExibicaoOportunidade(oportunidade)}.pdf`;
        link.click();
      }
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao gerar o histórico.'));
    } finally {
      setImprimindo(false);
    }
  };

  return (
    <div className={`space-y-3 ${variant === 'embedded' ? 'border-t border-gray-200 dark:border-gray-600 pt-4' : ''}`}>
      <div className="flex items-center justify-between gap-2 flex-wrap">
        {variant === 'embedded' && (
          <div className="flex items-center gap-2">
            <MessageSquare size={16} className="text-blue-600 dark:text-blue-400" />
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Histórico de negociação
            </h3>
          </div>
        )}
        {variant === 'embedded' ? (
          <button
            type="button"
            onClick={handleImprimir}
            disabled={loading || imprimindo}
            className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 ml-auto"
          >
            <Printer size={13} />
            {imprimindo ? 'Gerando...' : 'Imprimir histórico'}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleImprimir}
            disabled={loading || imprimindo}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 w-full sm:w-auto"
          >
            <Printer size={14} />
            {imprimindo ? 'Gerando...' : 'Imprimir histórico'}
          </button>
        )}
      </div>

      <p className="text-xs text-gray-500 dark:text-gray-400">
        Registre o que o cliente respondeu em cada contato (preço, objeções, prazos). As notas ficam salvas com data e não podem ser editadas.
      </p>

      {(erro || formErro) && (
        <p className="text-xs text-red-600 dark:text-red-400">{formErro || erro}</p>
      )}

      <div className={`overflow-y-auto space-y-2 rounded-lg border border-gray-200 dark:border-gray-600 p-2 bg-gray-50/80 dark:bg-gray-900/40 ${
        variant === 'modal' ? 'max-h-[min(50vh,28rem)]' : 'max-h-48'
      }`}>
        {loading ? (
          <p className="text-xs text-gray-500 dark:text-gray-400 p-2">Carregando...</p>
        ) : notas.length === 0 ? (
          <p className="text-xs text-gray-500 dark:text-gray-400 p-2 italic">
            Nenhum registro ainda. Adicione a primeira resposta do cliente abaixo.
          </p>
        ) : (
          notas.map((n) => (
            <div
              key={n.id}
              className={`rounded-lg p-2 text-sm ${
                n.tipo === 'resposta_cliente'
                  ? 'bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/50'
                  : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
              }`}
            >
              <p className="text-[11px] text-gray-500 dark:text-gray-400 mb-1">
                {formatarDataHoraNegociacao(n.created_at)}
                {' · '}
                <span className="font-medium">{n.tipo_label}</span>
                {n.autor_nome ? ` · por ${n.autor_nome}` : ''}
              </p>
              <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{n.texto}</p>
            </div>
          ))
        )}
      </div>

      <div className="space-y-2">
        <div className="flex flex-wrap gap-2">
          <select
            value={tipoNova}
            onChange={(e) => setTipoNova(e.target.value as TipoNotaNegociacao)}
            className="text-sm px-2 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="resposta_cliente">Resposta do cliente</option>
            <option value="nota_interna">Nota interna</option>
          </select>
        </div>
        <textarea
          value={textoNova}
          onChange={(e) => {
            setTextoNova(e.target.value);
            setFormErro(null);
          }}
          rows={3}
          placeholder="Ex.: Cliente pediu desconto de 10%, vai decidir até sexta; pediu mais prazo para pagar..."
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
        />
        <button
          type="button"
          onClick={handleAdicionar}
          disabled={salvando || !textoNova.trim()}
          className="text-sm px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50"
        >
          {salvando ? 'Salvando...' : 'Adicionar ao histórico'}
        </button>
      </div>
    </div>
  );
}
