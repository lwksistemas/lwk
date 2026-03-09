'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { ArrowLeft, Users, Plus, X } from 'lucide-react';

interface Vendedor {
  id: number;
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  is_admin: boolean;
  is_active: boolean;
}

export default function ConfiguracoesFuncionariosPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/crm-vendas/configuracoes`;

  const [vendedores, setVendedores] = useState<Vendedor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalAberto, setModalAberto] = useState(false);
  const [editando, setEditando] = useState<Vendedor | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [form, setForm] = useState({
    nome: '',
    email: '',
    telefone: '',
    cargo: 'Vendedor',
  });

  const carregar = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Vendedor[] | { results: Vendedor[] }>('/crm-vendas/vendedores/');
      const data = res.data;
      setVendedores(Array.isArray(data) ? data : (data as { results: Vendedor[] }).results ?? []);
      setError(null);
    } catch (err) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao carregar.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregar();
  }, []);

  const abrirNovo = () => {
    setEditando(null);
    setForm({ nome: '', email: '', telefone: '', cargo: 'Vendedor' });
    setFormErro(null);
    setModalAberto(true);
  };

  const abrirEditar = (v: Vendedor) => {
    setEditando(v);
    setForm({
      nome: v.nome,
      email: v.email || '',
      telefone: v.telefone || '',
      cargo: v.cargo || 'Vendedor',
    });
    setFormErro(null);
    setModalAberto(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    if (!form.nome.trim()) {
      setFormErro('Informe o nome.');
      return;
    }
    setSalvando(true);
    try {
      if (editando) {
        await apiClient.patch(`/crm-vendas/vendedores/${editando.id}/`, form);
      } else {
        await apiClient.post('/crm-vendas/vendedores/', form);
      }
      setModalAberto(false);
      carregar();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { nome?: string[]; detail?: string } } })?.response?.data;
      setFormErro(msg?.nome?.[0] || msg?.detail || 'Erro ao salvar.');
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="space-y-6">
      <Link
        href={base}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3] dark:hover:text-[#0d9dda]"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-[#e3f3ff] dark:bg-[#0176d3]/20 text-[#0176d3]">
            <Users size={24} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Cadastrar funcionários
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Gerencie vendedores e equipe de vendas
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={abrirNovo}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg font-medium text-sm transition-colors"
        >
          <Plus size={18} />
          Novo vendedor
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            Carregando...
          </div>
        ) : vendedores.length === 0 ? (
          <div className="p-8 text-center">
            <Users size={40} className="mx-auto text-gray-400 dark:text-gray-500 mb-3" />
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Nenhum vendedor cadastrado
            </p>
            <button
              type="button"
              onClick={abrirNovo}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg font-medium text-sm"
            >
              <Plus size={18} />
              Cadastrar primeiro vendedor
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-[#0d1f3c]">
            {vendedores.map((v) => (
              <div
                key={v.id}
                className="flex items-center justify-between gap-4 p-4 hover:bg-gray-50 dark:hover:bg-[#0d1f3c]/50 transition-colors"
              >
                <div className="min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white truncate">
                    {v.nome}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                    {v.email || v.telefone || v.cargo || '—'}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => abrirEditar(v)}
                  className="px-3 py-1.5 text-sm font-medium text-[#0176d3] hover:bg-[#0159a8]/10 dark:hover:bg-[#0176d3]/20 rounded transition-colors"
                >
                  Editar
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {modalAberto && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => !salvando && setModalAberto(false)}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="bg-white dark:bg-[#16325c] rounded-xl shadow-xl w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200 dark:border-[#0d1f3c] flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {editando ? 'Editar vendedor' : 'Novo vendedor'}
                </h2>
                <button
                  type="button"
                  onClick={() => !salvando && setModalAberto(false)}
                  className="p-1 rounded hover:bg-gray-100 dark:hover:bg-[#0d1f3c] text-gray-500"
                >
                  <X size={20} />
                </button>
              </div>
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                {formErro && (
                  <p className="text-sm text-red-600 dark:text-red-400">{formErro}</p>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nome *
                  </label>
                  <input
                    type="text"
                    value={form.nome}
                    onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Nome do vendedor"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="email@exemplo.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Telefone
                  </label>
                  <input
                    type="text"
                    value={form.telefone}
                    onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="(11) 99999-9999"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Cargo
                  </label>
                  <input
                    type="text"
                    value={form.cargo}
                    onChange={(e) => setForm((f) => ({ ...f, cargo: e.target.value }))}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder="Vendedor"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setModalAberto(false)}
                    disabled={salvando}
                    className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#0d1f3c] disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    disabled={salvando}
                    className="px-4 py-2 rounded-lg bg-[#0176d3] hover:bg-[#0159a8] text-white font-medium disabled:opacity-50"
                  >
                    {salvando ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
