'use client';

import { useState, useEffect } from 'react';
import { FileCheck, Download, ExternalLink, RefreshCw, Plus, Trash2, CheckCircle2, FileText } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { CRM_PERIODO_COMISSAO } from '@/lib/crm-periodos';

interface RelatorioComissao {
  id: number;
  numero: string;
  titulo: string;
  status: string;
  status_display: string;
  empresa_prestadora_nome: string;
  vendedor_nome: string;
  periodo_descricao: string;
  valor_total_vendas: string;
  valor_total_comissao: string;
  quantidade_vendas: number;
  boleto_url: string;
  nfse_numero: string;
  created_at: string | null;
}

interface EmpresaPrestadora { id: number; nome: string; cnpj?: string; }
interface Vendedor { id: number; nome: string; }

interface Props {
  empresasPrestadoras: EmpresaPrestadora[];
  vendedores: Vendedor[];
  isVendedor: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  pendente_aprovacao: 'bg-yellow-100 text-yellow-800',
  reprovado: 'bg-red-100 text-red-800',
  aprovado: 'bg-blue-100 text-blue-800',
  aguardando_pagamento: 'bg-orange-100 text-orange-800',
  pago: 'bg-green-100 text-green-800',
  nfse_emitida: 'bg-emerald-100 text-emerald-800',
  concluido: 'bg-gray-100 text-gray-800',
  cancelado: 'bg-gray-100 text-gray-500',
};

export function RelatoriosComissao({ empresasPrestadoras, vendedores, isVendedor }: Props) {
  const [relatorios, setRelatorios] = useState<RelatorioComissao[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [criando, setCriando] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [relatorioIdCriado, setRelatorioIdCriado] = useState<number | null>(null);

  // Form state
  const [formEmpresa, setFormEmpresa] = useState('');
  const [formVendedor, setFormVendedor] = useState('');
  const [formPeriodo, setFormPeriodo] = useState('mes_atual');
  const [formDataInicio, setFormDataInicio] = useState('');
  const [formDataFim, setFormDataFim] = useState('');
  const [formObs, setFormObs] = useState('');

  const loadRelatorios = async () => {
    try {
      setLoading(true);
      const { data } = await apiClient.get('/crm-vendas/relatorios-comissao/');
      setRelatorios(data.relatorios || []);
    } catch { setRelatorios([]); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadRelatorios(); }, []);

  const _buildPayload = () => {
    const payload: Record<string, unknown> = { empresa_prestadora_id: parseInt(formEmpresa), periodo: formPeriodo, observacoes: formObs };
    if (formVendedor) payload.vendedor_id = parseInt(formVendedor);
    if (formPeriodo === 'personalizado') { payload.data_inicio = formDataInicio; payload.data_fim = formDataFim; }
    return payload;
  };

  const handlePreview = async () => {
    if (!formEmpresa) { setMessage({ type: 'error', text: 'Selecione a empresa prestadora.' }); return; }
    if (formPeriodo === 'personalizado' && (!formDataInicio || !formDataFim)) { setMessage({ type: 'error', text: 'Informe as datas.' }); return; }
    setCriando(true); setMessage(null);
    try {
      const res = await apiClient.post('/crm-vendas/relatorios-comissao/preview/', _buildPayload(), { responseType: 'blob' });
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      setPreviewUrl(url);
      window.open(url, '_blank');
      setMessage({ type: 'success', text: 'PDF aberto em nova aba. Revise e confirme o envio abaixo.' });
    } catch (err: any) {
      const data = err.response?.data;
      let msg = 'Erro ao gerar preview.';
      if (data instanceof Blob) { try { msg = JSON.parse(await data.text()).detail || msg; } catch {} }
      else if (data?.detail) msg = data.detail;
      setMessage({ type: 'error', text: msg });
    } finally { setCriando(false); }
  };

  const handleCriarEEnviar = async () => {
    if (!formEmpresa) { setMessage({ type: 'error', text: 'Selecione a empresa prestadora.' }); return; }
    if (formPeriodo === 'personalizado' && (!formDataInicio || !formDataFim)) { setMessage({ type: 'error', text: 'Informe as datas.' }); return; }
    setCriando(true); setMessage(null);
    try {
      const { data } = await apiClient.post('/crm-vendas/relatorios-comissao/criar/', _buildPayload());
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        setShowForm(false); setPreviewUrl(null); setRelatorioIdCriado(null);
        loadRelatorios();
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro ao criar.' });
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao criar relatório.' });
    } finally { setCriando(false); }
  };

  const handleDownloadPdf = async (id: number, numero: string) => {
    try {
      const res = await apiClient.get(`/crm-vendas/relatorios-comissao/${id}/pdf/`, { responseType: 'blob' });
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => window.URL.revokeObjectURL(url), 10000);
    } catch { setMessage({ type: 'error', text: 'Erro ao baixar PDF.' }); }
  };

  const handleExcluir = async (id: number, numero: string) => {
    if (!confirm(`Excluir relatório ${numero}?`)) return;
    try {
      const { data } = await apiClient.delete(`/crm-vendas/relatorios-comissao/${id}/excluir/`);
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        loadRelatorios();
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro ao excluir.' });
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao excluir.' });
    }
  };

  const handleConfirmarPagamento = async (id: number, numero: string) => {
    if (!confirm(`Confirmar pagamento do relatório ${numero}? Isso vai emitir a NFS-e automaticamente.`)) return;
    try {
      const { data } = await apiClient.post(`/crm-vendas/relatorios-comissao/${id}/confirmar-pagamento/`);
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        loadRelatorios();
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro.' });
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao confirmar pagamento.' });
    }
  };

  const handleReemitirNfse = async (id: number, numero: string) => {
    if (!confirm(`Reemitir NFS-e para o relatório ${numero}?`)) return;
    try {
      const { data } = await apiClient.post(`/crm-vendas/relatorios-comissao/${id}/reemitir-nfse/`);
      if (data.success) {
        setMessage({ type: 'success', text: data.message });
        loadRelatorios();
      } else {
        setMessage({ type: 'error', text: data.detail || 'Erro.' });
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao emitir NFS-e.' });
    }
  };

  return (
    <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <FileCheck size={20} className="text-[#0176d3]" />
          Relatórios de Comissão
        </h2>
        <div className="flex gap-2">
          <button onClick={loadRelatorios} className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400">
            <RefreshCw size={16} />
          </button>
          {!isVendedor && (
            <button onClick={() => setShowForm(!showForm)}
              className="flex items-center gap-1 px-3 py-1.5 bg-[#0176d3] text-white rounded-lg text-sm font-medium hover:bg-[#0159a8]">
              <Plus size={14} /> Novo
            </button>
          )}
        </div>
      </div>

      {message && (
        <div className={`mb-4 p-3 rounded-lg text-sm ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {message.text}
        </div>
      )}

      {/* Formulário de criação */}
      {showForm && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Gerar Relatório de Comissão</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Empresa Prestadora *</label>
              <select value={formEmpresa} onChange={e => setFormEmpresa(e.target.value)}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white">
                <option value="">Selecione...</option>
                {empresasPrestadoras.map(ep => <option key={ep.id} value={ep.id}>{ep.nome}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Vendedor (opcional)</label>
              <select value={formVendedor} onChange={e => setFormVendedor(e.target.value)}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white">
                <option value="">Todos</option>
                {vendedores.map(v => <option key={v.id} value={v.id}>{v.nome}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Período</label>
              <select value={formPeriodo} onChange={e => setFormPeriodo(e.target.value)}
                className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white">
                {CRM_PERIODO_COMISSAO.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </div>
            {formPeriodo === 'personalizado' && (
              <>
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Data Início</label>
                  <input type="date" value={formDataInicio} onChange={e => setFormDataInicio(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Data Fim</label>
                  <input type="date" value={formDataFim} onChange={e => setFormDataFim(e.target.value)}
                    className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
                </div>
              </>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Observações</label>
            <textarea value={formObs} onChange={e => setFormObs(e.target.value)} rows={2}
              className="w-full px-3 py-2 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm text-gray-900 dark:text-white" />
          </div>
          <div className="flex gap-2">
            <button onClick={handlePreview} disabled={criando}
              className="px-4 py-2 bg-gray-600 text-white rounded text-sm font-medium hover:bg-gray-700 disabled:opacity-50">
              {criando ? 'Gerando...' : '👁️ Visualizar PDF'}
            </button>
            <button onClick={handleCriarEEnviar} disabled={criando}
              className="px-4 py-2 bg-[#0176d3] text-white rounded text-sm font-medium hover:bg-[#0159a8] disabled:opacity-50">
              {criando ? 'Enviando...' : '📤 Criar e Enviar para Aprovação'}
            </button>
            <button onClick={() => { setShowForm(false); setPreviewUrl(null); setRelatorioIdCriado(null); }} className="px-4 py-2 text-gray-600 dark:text-gray-400 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      {/* Lista de relatórios */}
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
              {relatorios.map(r => (
                <tr key={r.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]">
                  <td className="py-2 px-2 font-mono text-xs">{r.numero}</td>
                  <td className="py-2 px-2">{r.empresa_prestadora_nome}</td>
                  <td className="py-2 px-2 text-gray-600 dark:text-gray-400">{r.periodo_descricao}</td>
                  <td className="py-2 px-2 text-right font-medium text-green-700 dark:text-green-400">
                    R$ {parseFloat(r.valor_total_comissao).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[r.status] || 'bg-gray-100 text-gray-600'}`}>
                      {r.status_display}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <button onClick={() => handleDownloadPdf(r.id, r.numero)} title="Baixar PDF"
                        className="p-1 text-gray-500 hover:text-[#0176d3]">
                        <Download size={14} />
                      </button>
                      {r.boleto_url && (
                        <a href={r.boleto_url} target="_blank" rel="noopener noreferrer" title="Ver Boleto"
                          className="p-1 text-gray-500 hover:text-orange-600">
                          <ExternalLink size={14} />
                        </a>
                      )}
                      {r.status === 'aguardando_pagamento' && (
                        <button onClick={() => handleConfirmarPagamento(r.id, r.numero)} title="Confirmar Pagamento"
                          className="p-1 text-gray-500 hover:text-green-600">
                          <CheckCircle2 size={14} />
                        </button>
                      )}
                      {r.status === 'pago' && (
                        <button onClick={() => handleReemitirNfse(r.id, r.numero)} title="Emitir NFS-e"
                          className="p-1 text-gray-500 hover:text-blue-600">
                          <FileCheck size={14} />
                        </button>
                      )}
                      {!['concluido', 'nfse_emitida'].includes(r.status) && (
                        <button onClick={() => handleExcluir(r.id, r.numero)} title="Excluir"
                          className="p-1 text-gray-500 hover:text-red-600">
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
    </div>
  );
}
