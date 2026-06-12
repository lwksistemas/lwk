'use client';

import { useState, useEffect, useCallback } from 'react';
import { clinicaApiClient } from '@/lib/api-client';
import { formatApiError } from '@/lib/api-errors';
import { formatCurrency, formatDate, formatDateTime } from '@/lib/financeiro-helpers';
import { useToast } from '@/components/ui/Toast';
import { formatTelefone } from '@/lib/format-br';
import { logger } from '@/lib/logger';
import type {
  LojaInfo,
  Categoria,
  ItemCardapio,
  Mesa,
  Cliente,
  Pedido,
  Funcionario,
  Fornecedor,
  NotaFiscalEntrada,
  EstoqueItem,
  MovimentoEstoque,
  RegistroPesoBalança,
} from '../types';
import { STATUS_MESA, CARGO_FUNCIONARIO } from '../types';
import { ModalFornecedoresRestaurante } from './ModalFornecedoresRestaurante';

export function ModalNotaFiscal({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([]);
  const [notas, setNotas] = useState<NotaFiscalEntrada[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    numero: '',
    fornecedor_id: '',
    data_emissao: '',
    data_entrada: '',
    valor_total: '',
    observacoes: ''
  });
  const [xmlFile, setXmlFile] = useState<File | null>(null);
  const [showModalFornecedor, setShowModalFornecedor] = useState(false);

  const loadFornecedores = useCallback(async () => {
    try {
      const res = await clinicaApiClient.get<Fornecedor[] | { results?: Fornecedor[] }>('/restaurante/fornecedores/');
      setFornecedores(Array.isArray(res.data) ? res.data : (res.data as { results?: Fornecedor[] })?.results ?? []);
    } catch {
      setFornecedores([]);
    }
  }, []);

  const loadNotas = useCallback(async () => {
    try {
      const res = await clinicaApiClient.get<NotaFiscalEntrada[] | { results?: NotaFiscalEntrada[] }>('/restaurante/notas-fiscais/');
      setNotas(Array.isArray(res.data) ? res.data : (res.data as { results?: NotaFiscalEntrada[] })?.results ?? []);
    } catch {
      setNotas([]);
    }
  }, []);

  const loadAll = useCallback(async () => {
    setLoading(true);
    await Promise.all([loadFornecedores(), loadNotas()]);
    setLoading(false);
  }, [loadFornecedores, loadNotas]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.numero.trim() || !form.fornecedor_id) {
      toast.error('Preencha número da NF e fornecedor');
      return;
    }
    setSaving(true);
    try {
      const payload = new FormData();
      payload.append('numero', form.numero.trim());
      payload.append('fornecedor', form.fornecedor_id);
      if (form.data_emissao) payload.append('data_emissao', form.data_emissao);
      if (form.data_entrada) payload.append('data_entrada', form.data_entrada);
      payload.append('valor_total', form.valor_total || '0');
      if (form.observacoes) payload.append('observacoes', form.observacoes);
      if (xmlFile) payload.append('xml_file', xmlFile);
      await clinicaApiClient.post('/restaurante/notas-fiscais/', payload);
      toast.success('Nota fiscal registrada');
      setForm({ numero: '', fornecedor_id: '', data_emissao: '', data_entrada: '', valor_total: '', observacoes: '' });
      setXmlFile(null);
      setShowForm(false);
      loadNotas();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-2xl w-full shadow-xl my-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>📄 Entrada de Nota Fiscal</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
          Registro de entrada de NF-e de compras: upload de XML, vinculação a fornecedores e estoque.
        </p>

        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : showForm ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número da NF *</label>
              <input type="text" name="numero" value={form.numero} onChange={handleChange} placeholder="Ex: 000.000.000" required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fornecedor *</label>
                <select name="fornecedor_id" value={form.fornecedor_id} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white">
                  <option value="">Selecione...</option>
                  {fornecedores.filter(f => f).map(f => <option key={f.id} value={f.id}>{f.nome}</option>)}
                </select>
              </div>
              <button type="button" onClick={() => setShowModalFornecedor(true)} className="mt-6 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm" title="Cadastrar fornecedor">+ Fornecedor</button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data emissão</label>
                <input type="date" name="data_emissao" value={form.data_emissao} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data entrada</label>
                <input type="date" name="data_entrada" value={form.data_entrada} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor total (R$)</label>
              <input type="number" name="valor_total" value={form.valor_total} onChange={handleChange} step="0.01" min="0" placeholder="0,00" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Arquivo XML da NF-e (opcional)</label>
              <input type="file" accept=".xml,application/xml" onChange={e => setXmlFile(e.target.files?.[0] || null)} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm" />
              {xmlFile && <p className="text-xs text-green-600 dark:text-green-400 mt-1">📎 {xmlFile.name}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
              <textarea name="observacoes" value={form.observacoes} onChange={handleChange} rows={2} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => { setShowForm(false); setXmlFile(null); }} disabled={saving} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Cancelar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white min-h-[40px] disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Registrar NF'}</button>
            </div>
          </form>
        ) : (
          <>
            <div className="flex justify-end mb-3">
              <button type="button" onClick={() => setShowForm(true)} className="px-4 py-2 rounded-lg text-white text-sm min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Nova Nota Fiscal</button>
            </div>
            {notas.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <p className="mb-2">Nenhuma nota fiscal registrada.</p>
                <p className="text-sm mb-4">Cadastre fornecedores e registre a primeira NF (com ou sem upload de XML).</p>
                <button type="button" onClick={() => setShowForm(true)} className="px-4 py-2 rounded-lg text-white" style={{ backgroundColor: loja.cor_primaria }}>+ Registrar primeira NF</button>
              </div>
            ) : (
              <ul className="space-y-3 max-h-[320px] overflow-y-auto">
                {notas.map(n => (
                  <li key={n.id} className="flex flex-wrap items-center justify-between p-3 border dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700/50 gap-2">
                    <div>
                      <span className="font-semibold text-gray-900 dark:text-white">NF {n.numero}</span>
                      <span className="text-gray-600 dark:text-gray-400 ml-2">— {n.fornecedor_nome || 'Fornecedor'}</span>
                      <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Emissão: {formatDate(n.data_emissao)} · Entrada: {formatDate(n.data_entrada)} · {formatCurrency(n.valor_total)}
                        {n.xml_file && <span className="ml-2">📎 XML</span>}
                        {n.aplicado_estoque && <span className="ml-2 text-green-600 dark:text-green-400">✓ Estoque</span>}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex justify-end gap-2 mt-4 pt-4 border-t dark:border-gray-600">
              <button type="button" onClick={() => setShowModalFornecedor(true)} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm">👥 Fornecedores</button>
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg text-white min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>Fechar</button>
            </div>
          </>
        )}

        {showModalFornecedor && (
          <ModalFornecedoresRestaurante loja={loja} onClose={() => { setShowModalFornecedor(false); loadFornecedores(); }} />
        )}
      </div>
    </div>
  );
}
