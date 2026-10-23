'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { X } from 'lucide-react';
import { formatCrmBrl, rotuloExibicaoOportunidade, subtituloModalOportunidade } from '@/lib/crm-utils';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import OportunidadeItensEditor from '@/components/crm-vendas/OportunidadeItensEditor';
import CrmEnviarClienteIcones from '@/components/crm-vendas/CrmEnviarClienteIcones';
import { useModalEditarOportunidade } from '@/hooks/crm-vendas/useModalEditarOportunidade';

interface Props {
  oportunidade: Oportunidade;
  onClose: () => void;
  onSuccess: () => void;
  slug: string;
  etapas: { key: string; label: string }[];
}

export default function ModalEditarOportunidade({ oportunidade, onClose, onSuccess, slug, etapas }: Props) {
  const {
    etapaSelecionada,
    setEtapaSelecionada,
    dataFechamentoGanho,
    setDataFechamentoGanho,
    dataFechamentoPerdido,
    setDataFechamentoPerdido,
    motivoPerda,
    setMotivoPerda,
    feedbackPosVenda,
    setFeedbackPosVenda,
    itensEditar,
    setItensEditar,
    produtosServicos,
    propostasOportunidade,
    contratoOportunidade,
    modalExcluir,
    setModalExcluir,
    seletorEditarAberto,
    setSeletorEditarAberto,
    enviando,
    enviandoEnvio,
    formErro,
    empresaPrestadoraId,
    setEmpresaPrestadoraId,
    prestadoras,
    propostaWhatsappHabilitada,
    contratoWhatsappHabilitado,
    updateItemEditar,
    removeItemEditar,
    handleEnviarCliente,
    handleExcluirOportunidade,
    handleSalvarEtapa,
  } = useModalEditarOportunidade(oportunidade, onClose, onSuccess);

  const resumoSubtitulo = subtituloModalOportunidade(oportunidade);
  const mostraFechamento =
    etapaSelecionada === 'closed_won' ||
    etapaSelecionada === 'closed_lost' ||
    oportunidade.etapa === 'closed_won' ||
    oportunidade.etapa === 'closed_lost' ||
    Boolean(oportunidade.data_fechamento_ganho) ||
    Boolean(oportunidade.data_fechamento_perdido);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={() => !enviando && onClose()}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-6xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Editar oportunidade
          </h2>
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <div className="px-5 pt-4 pb-3 flex flex-wrap items-start justify-between gap-x-6 gap-y-1 flex-shrink-0">
          <div className="min-w-0">
            <p className="font-medium text-gray-900 dark:text-white">
              {rotuloExibicaoOportunidade(oportunidade)}
            </p>
            {resumoSubtitulo && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {resumoSubtitulo}
              </p>
            )}
          </div>
          <div className="text-left sm:text-right">
            <p className="text-sm font-semibold text-green-600 dark:text-green-400">
              {formatCrmBrl(oportunidade.valor)}
            </p>
            {oportunidade.minha_comissao != null && (
              <p className="text-sm text-purple-600 dark:text-purple-400">
                Sua comissão: {formatCrmBrl(oportunidade.minha_comissao)}
              </p>
            )}
            {oportunidade.minha_comissao == null && oportunidade.valor_comissao && (
              <p className="text-sm text-purple-600 dark:text-purple-400">
                Pago pela prestadora: {formatCrmBrl(oportunidade.valor_comissao)}
              </p>
            )}
          </div>
        </div>
        <form id="form-editar-oportunidade" onSubmit={handleSalvarEtapa} className="overflow-y-auto flex-1">
          <div className="px-5 pb-4 space-y-4">
          {formErro && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
              {formErro}
            </p>
          )}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Empresa prestadora *
              </label>
              <select
                value={empresaPrestadoraId}
                onChange={(e) => setEmpresaPrestadoraId(e.target.value)}
                required
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Selecione...</option>
                {prestadoras.map((c) => (
                  <option key={c.id} value={c.id}>{c.nome}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Define em qual relatório de comissão esta venda aparece.
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Etapa (mudar para &quot;Fechado ganho&quot; = registrar venda)
              </label>
              <select
                value={etapaSelecionada}
                onChange={(e) => setEtapaSelecionada(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {etapas.map((o) => (
                  <option key={o.key} value={o.key}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          <OportunidadeItensEditor
            slug={slug}
            produtos={produtosServicos}
            itens={itensEditar}
            seletorAberto={seletorEditarAberto}
            onSeletorAbertoChange={setSeletorEditarAberto}
            onUpdateItem={updateItemEditar}
            onRemoveItem={removeItemEditar}
            empresaSelecionada={Boolean(empresaPrestadoraId)}
            onAddProduto={(ps) => {
              setItensEditar((itens) => [
                ...itens,
                { produto_servico_id: ps.id, quantidade: '1', preco_unitario: ps.preco },
              ]);
            }}
            layout="modal"
          />

          {mostraFechamento && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          {(etapaSelecionada === 'closed_lost' || oportunidade.etapa === 'closed_lost') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Motivo da perda / cancelamento <span className="text-red-500">*</span>
              </label>
              <textarea
                value={motivoPerda}
                onChange={(e) => setMotivoPerda(e.target.value)}
                rows={3}
                required
                placeholder="Ex.: Cliente desistiu por preço, escolheu concorrente, adiou a compra..."
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Obrigatório ao fechar como perdido. Fica registrado no histórico e na impressão.
              </p>
            </div>
          )}
          {(etapaSelecionada === 'closed_won' || oportunidade.etapa === 'closed_won') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Opinião do cliente (pós-venda)
              </label>
              <textarea
                value={feedbackPosVenda}
                onChange={(e) => setFeedbackPosVenda(e.target.value)}
                rows={3}
                placeholder="Ex.: Cliente elogiou o atendimento, sugeriu melhoria no prazo de entrega..."
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Registre a percepção do cliente sobre o serviço ou o sistema após a compra finalizada.
              </p>
            </div>
          )}
          {(etapaSelecionada === 'closed_won' || oportunidade.data_fechamento_ganho) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Fechamento Ganho
              </label>
              <input
                type="date"
                value={dataFechamentoGanho}
                onChange={(e) => setDataFechamentoGanho(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          )}
          {(etapaSelecionada === 'closed_lost' || oportunidade.data_fechamento_perdido) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Fechamento Perdido
              </label>
              <input
                type="date"
                value={dataFechamentoPerdido}
                onChange={(e) => setDataFechamentoPerdido(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          )}
          {(etapaSelecionada === 'closed_won' || oportunidade.etapa === 'closed_won') && (
            <div className="border-t border-gray-200 dark:border-gray-600 pt-4 lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Enviar ao cliente
              </label>
              {(propostasOportunidade.length > 0 || contratoOportunidade) ? (
                <div className="space-y-2">
                  {propostasOportunidade.map((p) => (
                    <div key={p.id} className="flex items-center justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="text-sm truncate">Proposta: {p.titulo || `#${p.id}`}</span>
                      <CrmEnviarClienteIcones
                        variant="modal"
                        whatsappHabilitado={propostaWhatsappHabilitada}
                        enviando={enviandoEnvio}
                        onEnviar={(canal) => handleEnviarCliente('proposta', p.id, canal)}
                      />
                    </div>
                  ))}
                  {contratoOportunidade && (
                    <div className="flex items-center justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="text-sm truncate">Contrato: {contratoOportunidade.titulo || `#${contratoOportunidade.id}`}</span>
                      <CrmEnviarClienteIcones
                        variant="modal"
                        whatsappHabilitado={contratoWhatsappHabilitado}
                        enviando={enviandoEnvio}
                        onEnviar={(canal) => handleEnviarCliente('contrato', contratoOportunidade.id, canal)}
                      />
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Crie uma proposta ou contrato em{' '}
                  <Link href={`/loja/${slug}/crm-vendas/propostas`} className="text-[#0176d3] hover:underline">Propostas</Link>
                  {' ou '}
                  <Link href={`/loja/${slug}/crm-vendas/contratos`} className="text-[#0176d3] hover:underline">Contratos</Link>
                  {' para enviar ao cliente.'}
                </p>
              )}
            </div>
          )}
          </div>
          )}
          </div>
        </form>
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          {!modalExcluir ? (
            <div className="flex flex-col items-end gap-2">
              {oportunidade.etapa === 'closed_won' && (
                <p className="text-xs text-amber-700 dark:text-amber-300">
                  Venda ganha não pode ser excluída. Mude a etapa e salve para poder excluir.
                </p>
              )}
              <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => !enviando && onClose()}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => setModalExcluir(true)}
                disabled={enviando || oportunidade.etapa === 'closed_won'}
                title={oportunidade.etapa === 'closed_won' ? 'Mude a etapa e salve para poder excluir.' : undefined}
                className="px-4 py-2 rounded-lg border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
              >
                Excluir
              </button>
              <button
                type="submit"
                form="form-editar-oportunidade"
                disabled={enviando}
                className="px-6 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
              >
                {enviando ? 'Salvando...' : 'Salvar'}
              </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Tem certeza que deseja excluir a oportunidade &quot;{oportunidade.titulo}&quot;? Esta ação não pode ser desfeita.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setModalExcluir(false)}
                  disabled={enviando}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleExcluirOportunidade}
                  disabled={enviando}
                  className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium"
                >
                  {enviando ? 'Excluindo...' : 'Confirmar exclusão'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
