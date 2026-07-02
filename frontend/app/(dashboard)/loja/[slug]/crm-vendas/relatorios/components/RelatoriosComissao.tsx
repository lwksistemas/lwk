'use client';

import { FileCheck, Download, ExternalLink, RefreshCw, Plus, Trash2, CheckCircle2, X } from 'lucide-react';
import { CRM_PERIODO_COMISSAO } from '@/lib/crm-periodos';
import { CRM_RELATORIO_COMISSAO_STATUS_COLORS } from '@/lib/crm-relatorios';
import type { CrmRelatorioEmpresaPrestadora, CrmRelatorioVendedor } from '@/lib/crm-relatorios';
import { useCrmRelatoriosComissao } from '@/hooks/crm-vendas/useCrmRelatoriosComissao';

interface Props {
  empresasPrestadoras: CrmRelatorioEmpresaPrestadora[];
  vendedores: CrmRelatorioVendedor[];
  isVendedor: boolean;
}

export function RelatoriosComissao({ empresasPrestadoras, vendedores, isVendedor }: Props) {
  const {
    relatorios,
    loading,
    showForm,
    setShowForm,
    criando,
    confirmAction,
    setConfirmAction,
    confirmando,
    confirmCopy,
    executeConfirm,
    formEmpresa,
    setFormEmpresa,
    formVendedor,
    setFormVendedor,
    formPeriodo,
    setFormPeriodo,
    formDataInicio,
    setFormDataInicio,
    formDataFim,
    setFormDataFim,
    formObs,
    setFormObs,
    loadRelatorios,
    handlePreview,
    handleCriarEEnviar,
    handleDownloadPdf,
    resetForm,
    canCreate,
  } = useCrmRelatoriosComissao(isVendedor);

  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <FileCheck size={20} className="text-[#0176d3]" />
          Relatórios de Comissão
        </h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={loadRelatorios}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400"
            title="Atualizar lista"
          >
            <RefreshCw size={16} />
          </button>
          {canCreate && (
            <button
              type="button"
              onClick={() => setShowForm(!showForm)}
              className="flex items-center gap-1 px-3 py-1.5 bg-[#0176d3] text-white rounded-lg text-sm font-medium hover:bg-[#0159a8]"
            >
              <Plus size={14} /> Novo
            </button>
          )}
        </div>
      </div>

      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Gerar Relatório de Comissão</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Empresa Prestadora *</label>
              <select
                value={formEmpresa}
                onChange={(e) => setFormEmpresa(e.target.value)}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
              >
                <option value="">Selecione...</option>
                {empresasPrestadoras.map((ep) => (
                  <option key={ep.id} value={ep.id}>
                    {ep.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Vendedor (opcional)</label>
              <select
                value={formVendedor}
                onChange={(e) => setFormVendedor(e.target.value)}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                {vendedores.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Período</label>
              <select
                value={formPeriodo}
                onChange={(e) => setFormPeriodo(e.target.value)}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
              >
                {CRM_PERIODO_COMISSAO.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
            {formPeriodo === 'personalizado' && (
              <>
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Data Início</label>
                  <input
                    type="date"
                    value={formDataInicio}
                    onChange={(e) => setFormDataInicio(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Data Fim</label>
                  <input
                    type="date"
                    value={formDataFim}
                    onChange={(e) => setFormDataFim(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
                  />
                </div>
              </>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Observações</label>
            <textarea
              value={formObs}
              onChange={(e) => setFormObs(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handlePreview}
              disabled={criando}
              className="px-4 py-2 bg-gray-600 text-white rounded text-sm font-medium hover:bg-gray-700 disabled:opacity-50"
            >
              {criando ? 'Gerando...' : 'Visualizar PDF'}
            </button>
            <button
              type="button"
              onClick={handleCriarEEnviar}
              disabled={criando}
              className="px-4 py-2 bg-[#0176d3] text-white rounded text-sm font-medium hover:bg-[#0159a8] disabled:opacity-50"
            >
              {criando ? 'Enviando...' : 'Criar e Enviar para Aprovação'}
            </button>
            <button type="button" onClick={resetForm} className="px-4 py-2 text-gray-600 dark:text-gray-400 text-sm">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">Carregando...</p>
      ) : relatorios.length === 0 ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">Nenhum relatório de comissão gerado ainda.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-2 px-2 text-gray-600 dark:text-gray-400 font-medium">Nº</th>
                <th className="text-left py-2 px-2 text-gray-600 dark:text-gray-400 font-medium">Empresa</th>
                <th className="text-left py-2 px-2 text-gray-600 dark:text-gray-400 font-medium">Período</th>
                <th className="text-right py-2 px-2 text-gray-600 dark:text-gray-400 font-medium">Comissão</th>
                <th className="text-center py-2 px-2 text-gray-600 dark:text-gray-400 font-medium">Status</th>
                <th className="text-center py-2 px-2 text-gray-600 dark:text-gray-400 font-medium">Ações</th>
              </tr>
            </thead>
            <tbody>
              {relatorios.map((r) => (
                <tr key={r.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]">
                  <td className="py-2 px-2 font-mono text-xs">{r.numero}</td>
                  <td className="py-2 px-2">{r.empresa_prestadora_nome}</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400">{r.periodo_descricao}</td>
                  <td className="py-2 px-2 text-right font-medium text-green-700 dark:text-green-400">
                    R$ {parseFloat(r.valor_total_comissao).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        CRM_RELATORIO_COMISSAO_STATUS_COLORS[r.status] || 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {r.status_display}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <button
                        type="button"
                        onClick={() => handleDownloadPdf(r.id)}
                        title="Baixar PDF"
                        className="p-1 text-gray-500 hover:text-[#0176d3]"
                      >
                        <Download size={14} />
                      </button>
                      {r.boleto_url && (
                        <a
                          href={r.boleto_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          title="Ver Boleto"
                          className="p-1 text-gray-500 hover:text-orange-600"
                        >
                          <ExternalLink size={14} />
                        </a>
                      )}
                      {r.status === 'aguardando_pagamento' && (
                        <button
                          type="button"
                          onClick={() => setConfirmAction({ type: 'pagamento', id: r.id, numero: r.numero })}
                          title="Confirmar Pagamento"
                          className="p-1 text-gray-500 hover:text-green-600"
                        >
                          <CheckCircle2 size={14} />
                        </button>
                      )}
                      {r.status === 'pago' && (
                        <button
                          type="button"
                          onClick={() => setConfirmAction({ type: 'reemitir', id: r.id, numero: r.numero })}
                          title="Emitir NFS-e"
                          className="p-1 text-gray-500 hover:text-blue-600"
                        >
                          <FileCheck size={14} />
                        </button>
                      )}
                      {!['concluido', 'nfse_emitida'].includes(r.status) && (
                        <button
                          type="button"
                          onClick={() => setConfirmAction({ type: 'excluir', id: r.id, numero: r.numero })}
                          title="Excluir"
                          className="p-1 text-gray-500 hover:text-red-600"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {confirmAction && confirmCopy && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-[80]"
            onClick={() => !confirmando && setConfirmAction(null)}
          />
          <div className="fixed inset-0 z-[81] flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{confirmCopy.title}</h2>
                <button
                  type="button"
                  onClick={() => !confirmando && setConfirmAction(null)}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <X size={20} />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <p className="text-gray-600 dark:text-gray-400">{confirmCopy.message(confirmAction.numero)}</p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setConfirmAction(null)}
                    disabled={confirmando}
                    className="flex-1 px-4 py-2 border rounded-lg disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={executeConfirm}
                    disabled={confirmando}
                    className={`flex-1 px-4 py-2 text-white rounded-lg disabled:opacity-50 ${
                      confirmCopy.variant === 'danger'
                        ? 'bg-red-600 hover:bg-red-700'
                        : 'bg-[#0176d3] hover:bg-[#0159a8]'
                    }`}
                  >
                    {confirmando ? 'Processando...' : confirmCopy.confirmLabel}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
