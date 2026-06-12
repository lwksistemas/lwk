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
import { formatCnpjDisplay } from './formatCnpjDisplay';

export function ModalFornecedoresRestaurante({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [lista, setLista] = useState<Fornecedor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nome: '', cnpj: '', email: '', telefone: '', endereco: '' });
  const [saving, setSaving] = useState(false);
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await clinicaApiClient.get<Fornecedor[] | { results?: Fornecedor[] }>('/restaurante/fornecedores/');
      setLista(Array.isArray(res.data) ? res.data : (res.data as { results?: Fornecedor[] })?.results ?? []);
    } catch {
      setLista([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  /** Consulta CNPJ na BrasilAPI e preenche nome e endereço automaticamente */
  const buscarCnpj = async () => {
    const cnpj = form.cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) {
      toast.error('Informe um CNPJ válido com 14 dígitos para buscar.');
      return;
    }
    setBuscarCnpjLoading(true);
    try {
      const res = await fetch(`https://brasilapi.com.br/api/cnpj/v1/${cnpj}`);
      if (!res.ok) {
        toast.error('CNPJ não encontrado ou serviço indisponível.');
        return;
      }
      const data = await res.json();
      const partes: string[] = [];
      if (data.logradouro) partes.push(data.logradouro);
      if (data.numero) partes.push(data.numero);
      if (data.complemento) partes.push(data.complemento);
      if (data.bairro) partes.push(data.bairro);
      if (data.municipio) partes.push(data.municipio);
      if (data.uf) partes.push(data.uf);
      if (data.cep) partes.push(`CEP ${(data.cep || '').replace(/\D/g, '').slice(0, 5)}-${(data.cep || '').replace(/\D/g, '').slice(5, 8)}`);
      const endereco = partes.join(', ');
      setForm(prev => ({
        ...prev,
        nome: data.razao_social || data.nome_fantasia || prev.nome,
        endereco: endereco || prev.endereco,
      }));
      toast.success('Dados do CNPJ preenchidos.');
    } catch {
      toast.error('Erro ao consultar CNPJ. Tente novamente.');
    } finally {
      setBuscarCnpjLoading(false);
    }
  };

  const handleCnpjChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 14);
    setForm(f => ({ ...f, cnpj: formatCnpjDisplay(digits) }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.nome.trim()) { toast.error('Nome obrigatório'); return; }
    setSaving(true);
    try {
      await clinicaApiClient.post('/restaurante/fornecedores/', form);
      toast.success('Fornecedor cadastrado');
      setForm({ nome: '', cnpj: '', email: '', telefone: '', endereco: '' });
      setShowForm(false);
      load();
    } catch (err: unknown) {
      toast.error(formatApiError(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[60] p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-lg w-full shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👥 Fornecedores</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">✕</button>
        </div>
        {loading ? <div className="text-center py-6 text-gray-500">Carregando...</div> : showForm ? (
          <form onSubmit={handleSubmit} className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome/Razão Social *</label><input type="text" value={form.nome} onChange={e => setForm(f => ({ ...f, nome: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Nome do fornecedor" /></div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CNPJ</label>
              <div className="flex gap-2">
                <input type="text" value={form.cnpj} onChange={e => handleCnpjChange(e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="00.000.000/0000-00" maxLength={18} />
                <button type="button" onClick={buscarCnpj} disabled={buscarCnpjLoading || form.cnpj.replace(/\D/g, '').length !== 14} className="px-3 py-2 rounded-lg text-white text-sm whitespace-nowrap disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }} title="Buscar dados na Receita Federal">{buscarCnpjLoading ? 'Buscando...' : 'Buscar CNPJ'}</button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Digite o CNPJ e clique em Buscar para preencher nome e endereço automaticamente.</p>
            </div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label><input type="tel" value={form.telefone} onChange={e => setForm(f => ({ ...f, telefone: formatTelefone(e.target.value) }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" /></div>
            <div><label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço</label><input type="text" value={form.endereco} onChange={e => setForm(f => ({ ...f, endereco: e.target.value }))} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white" placeholder="Preenchido automaticamente ao buscar CNPJ" /></div>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowForm(false)} disabled={saving} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50">Voltar</button>
              <button type="submit" disabled={saving} className="px-4 py-2 rounded-lg text-white disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{saving ? 'Salvando...' : 'Cadastrar'}</button>
            </div>
          </form>
        ) : (
          <>
            {lista.length === 0 ? <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Nenhum fornecedor. Cadastre o primeiro.</p> : <ul className="space-y-2 max-h-48 overflow-y-auto mb-4">{lista.map(f => <li key={f.id} className="text-sm text-gray-900 dark:text-white">{f.nome}{f.cnpj ? ` · ${f.cnpj}` : ''}</li>)}</ul>}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(true)} className="px-4 py-2 rounded-lg text-white text-sm" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Fornecedor</button>
              <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700">Fechar</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
