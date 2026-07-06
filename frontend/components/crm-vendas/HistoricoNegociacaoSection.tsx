'use client';

import { useRef, useState } from 'react';
import { MessageSquare, Printer } from 'lucide-react';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import {
  formatarDataHoraNegociacao,
  type OportunidadeNota,
  type TipoNotaNegociacao,
  useOportunidadeNotas,
} from '@/hooks/crm-vendas/useOportunidadeNotas';
import { formatCrmBrl, rotuloExibicaoOportunidade, subtituloModalOportunidade } from '@/lib/crm-utils';
import { ETAPAS_PIPELINE_PADRAO } from '@/constants/crm';

interface Props {
  oportunidade: Oportunidade;
  etapas: { key: string; label: string }[];
  motivoPerda?: string;
  feedbackPosVenda?: string;
  /** embedded = dentro do modal Editar; modal = modal dedicado de histórico */
  variant?: 'embedded' | 'modal';
}

function labelEtapa(key: string, etapas: { key: string; label: string }[]): string {
  const found = etapas.find((e) => e.key === key);
  if (found) return found.label;
  const padrao = ETAPAS_PIPELINE_PADRAO.find((e) => e.key === key);
  return padrao?.label || key;
}

function HistoricoNegociacaoPrintContent({
  oportunidade,
  etapas,
  notas,
  motivoPerda,
  feedbackPosVenda,
}: {
  oportunidade: Oportunidade;
  etapas: { key: string; label: string }[];
  notas: OportunidadeNota[];
  motivoPerda?: string;
  feedbackPosVenda?: string;
}) {
  return (
    <div className="print-historico-negociacao p-6 text-black bg-white text-sm leading-relaxed">
      <h1 className="text-xl font-bold mb-1">Histórico de negociação</h1>
      <p className="text-gray-600 mb-4 text-xs">
        Gerado em {new Date().toLocaleString('pt-BR')}
      </p>

      <section className="mb-4 border-b border-gray-300 pb-3">
        <h2 className="font-semibold mb-2">Oportunidade</h2>
        <p><strong>Cliente:</strong> {rotuloExibicaoOportunidade(oportunidade)}</p>
        {subtituloModalOportunidade(oportunidade) && (
          <p><strong>Empresa:</strong> {subtituloModalOportunidade(oportunidade)}</p>
        )}
        <p><strong>Valor:</strong> {formatCrmBrl(oportunidade.valor)}</p>
        <p><strong>Etapa:</strong> {labelEtapa(oportunidade.etapa, etapas)}</p>
        {oportunidade.vendedor_nome && (
          <p><strong>Vendedor:</strong> {oportunidade.vendedor_nome}</p>
        )}
      </section>

      <section className="mb-4">
        <h2 className="font-semibold mb-2">Registros da negociação</h2>
        {notas.length === 0 ? (
          <p className="text-gray-600 italic">Nenhum registro durante a negociação.</p>
        ) : (
          <ul className="space-y-3">
            {notas.map((n) => (
              <li key={n.id} className="border-l-2 border-gray-400 pl-3">
                <p className="text-xs text-gray-600">
                  {formatarDataHoraNegociacao(n.created_at)}
                  {' · '}
                  {n.tipo_label}
                  {n.autor_nome ? ` · ${n.autor_nome}` : ''}
                </p>
                <p className="whitespace-pre-wrap mt-0.5">{n.texto}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      {(motivoPerda || feedbackPosVenda) && (
        <section className="border-t border-gray-300 pt-3">
          <h2 className="font-semibold mb-2">Encerramento</h2>
          {feedbackPosVenda && (
            <div className="mb-2">
              <p className="font-medium text-xs text-gray-600">Opinião do cliente (pós-venda)</p>
              <p className="whitespace-pre-wrap">{feedbackPosVenda}</p>
            </div>
          )}
          {motivoPerda && (
            <div>
              <p className="font-medium text-xs text-gray-600">Motivo da perda / cancelamento</p>
              <p className="whitespace-pre-wrap">{motivoPerda}</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default function HistoricoNegociacaoSection({
  oportunidade,
  etapas,
  motivoPerda,
  feedbackPosVenda,
  variant = 'embedded',
}: Props) {
  const { notas, loading, salvando, erro, adicionarNota } = useOportunidadeNotas(oportunidade.id);
  const [tipoNova, setTipoNova] = useState<TipoNotaNegociacao>('resposta_cliente');
  const [textoNova, setTextoNova] = useState('');
  const [formErro, setFormErro] = useState<string | null>(null);
  const printRef = useRef<HTMLDivElement>(null);

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

  const handleImprimir = () => {
    const el = printRef.current;
    if (!el) return;
    const janela = window.open('', '_blank', 'width=800,height=900');
    if (!janela) {
      alert('Permita pop-ups para imprimir o histórico.');
      return;
    }
    janela.document.write(`
      <!DOCTYPE html>
      <html lang="pt-BR">
        <head>
          <meta charset="utf-8" />
          <title>Histórico de negociação — ${rotuloExibicaoOportunidade(oportunidade)}</title>
          <style>
            body { font-family: system-ui, sans-serif; margin: 0; padding: 24px; color: #111; }
            @media print { body { padding: 12px; } }
          </style>
        </head>
        <body>${el.innerHTML}</body>
      </html>
    `);
    janela.document.close();
    janela.focus();
    setTimeout(() => {
      janela.print();
      janela.close();
    }, 300);
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
            disabled={loading}
            className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 ml-auto"
          >
            <Printer size={13} />
            Imprimir histórico
          </button>
        ) : (
          <button
            type="button"
            onClick={handleImprimir}
            disabled={loading}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 w-full sm:w-auto"
          >
            <Printer size={14} />
            Imprimir histórico
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
                {n.autor_nome ? ` · ${n.autor_nome}` : ''}
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

      <div className="hidden" aria-hidden>
        <div ref={printRef}>
          <HistoricoNegociacaoPrintContent
            oportunidade={oportunidade}
            etapas={etapas}
            notas={notas}
            motivoPerda={motivoPerda}
            feedbackPosVenda={feedbackPosVenda}
          />
        </div>
      </div>
    </div>
  );
}
