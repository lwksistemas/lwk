'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { normalizeListResponse } from '@/lib/crm-utils';
import { authService } from '@/lib/auth';
import { ArrowLeft, Users, Plus, X, Mail, Trash2 } from 'lucide-react';

interface Vendedor {
  id: number;
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  is_admin: boolean;
  is_active: boolean;
  tem_acesso?: boolean;
}

export default function ConfiguracoesFuncionariosPage() {
  const params = useParams();
  const router = useRouter();
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
    criar_acesso: false,
  });
  const [reenviando, setReenviando] = useState<number | null>(null);
  const [excluindo, setExcluindo] = useState<number | null>(null);
  const [confirmarExcluir, setConfirmarExcluir] = useState<Vendedor | null>(null);

  const carregar = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<Vendedor[] | { results: Vendedor[] }>('/crm-vendas/vendedores/');
      setVendedores(normalizeListResponse(res.data));
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
    setForm({ nome: '', email: '', telefone: '', cargo: 'Vendedor', criar_acesso: false });
    setFormErro(null);
    setModalAberto(true);
  };

  const abrirEditar = (v: Vendedor) => {
    // Impedir edição do vendedor admin
    if (v.is_admin) {
      setFormErro('O vendedor administrador não pode ser editado. Para alterar dados do administrador, acesse as configurações da loja.');
      setTimeout(() => setFormErro(null), 5000);
      return;
    }
    
    setEditando(v);
    setForm({
      nome: v.nome,
      email: v.email || '',
      telefone: v.telefone || '',
      cargo: v.cargo || 'Vendedor',
      criar_acesso: false,
    });
    setFormErro(null);
    setModalAberto(true);
  };

  const handleExcluir = async (v: Vendedor) => {
    if (!confirmarExcluir || confirmarExcluir.id !== v.id) return;
    setExcluindo(v.id);
    try {
      await apiClient.delete(`/crm-vendas/vendedores/${v.id}/`);
      setConfirmarExcluir(null);
      carregar();
    } catch {
      setFormErro('Erro ao excluir. Tente novamente.');
      setTimeout(() => setFormErro(null), 5000);
    } finally {
      setExcluindo(null);
    }
  };

  const handleReenviarSenha = async (v: Vendedor) => {
    if (!v.email) return;
    setReenviando(v.id);
    setFormErro(null);
    try {
      await apiClient.post(`/crm-vendas/vendedores/${v.id}/reenviar_senha/`);
      carregar();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Erro ao reenviar senha.';
      setFormErro(msg);
      setTimeout(() => setFormErro(null), 5000);
    } finally {
      setReenviando(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    if (!form.nome.trim()) {
      setFormErro('Informe o nome.');
      return;
    }
    if (form.criar_acesso && !form.email?.trim()) {
      setFormErro('Para criar acesso, informe o e-mail.');
      return;
    }
    setSalvando(true);
    try {
      const payload = { nome: form.nome, email: form.email, telefone: form.telefone, cargo: form.cargo, criar_acesso: form.criar_acesso };
      if (editando) {
        await apiClient.patch(`/crm-vendas/vendedores/${editando.id}/`, payload);
      } else {
        await apiClient.post('/crm-vendas/vendedores/', payload);
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

      {(error || formErro) && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 text-sm">
          {error || formErro}
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
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900 dark:text-white truncate">
                      {v.nome}
                    </p>
                    {v.is_admin && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                        Administrador
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                    {v.email || v.telefone || v.cargo || '—'}
                  </p>
                  {v.tem_acesso && v.email && (
                    <span className="inline-flex items-center gap-1 mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                      <Mail size={12} />
                      Acesso ao sistema
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {v.email && (
                    <button
                      type="button"
                      onClick={() => handleReenviarSenha(v)}
                      disabled={reenviando === v.id}
                      className="px-3 py-1.5 text-sm font-medium text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded transition-colors disabled:opacity-50"
                      title={v.is_admin ? 'Reenviar sua senha (administrador)' : 'Reenviar senha ao vendedor'}
                    >
                      {reenviando === v.id ? 'Enviando...' : 'Reenviar senha'}
                    </button>
                  )}
                  {!v.is_admin && (
                    <>
                      <button
                        type="button"
                        onClick={() => abrirEditar(v)}
                        className="px-3 py-1.5 text-sm font-medium text-[#0176d3] hover:bg-[#0159a8]/10 dark:hover:bg-[#0176d3]/20 rounded transition-colors"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmarExcluir(v)}
                        className="p-1.5 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                        title="Excluir"
                      >
                        <Trash2 size={18} />
                      </button>
                    </>
                  )}
                  {v.is_admin && (
                    <span className="px-3 py-1.5 text-sm text-gray-400 dark:text-gray-500">
                      Não editável
                    </span>
                  )}
                </div>
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
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.criar_acesso}
                    onChange={(e) => setForm((f) => ({ ...f, criar_acesso: e.target.checked }))}
                    className="mt-1 rounded border-gray-300 dark:border-gray-600 text-[#0176d3]"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {editando
                      ? 'Criar ou reenviar acesso ao sistema e enviar senha provisória por e-mail'
                      : 'Criar acesso ao sistema e enviar senha provisória por e-mail'}
                  </span>
                </label>
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

      {confirmarExcluir && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => !excluindo && setConfirmarExcluir(null)}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
              className="bg-white dark:bg-[#16325c] rounded-xl shadow-xl w-full max-w-sm p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Excluir vendedor
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Tem certeza que deseja excluir <strong>{confirmarExcluir.nome}</strong>? Esta ação não pode ser desfeita.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setConfirmarExcluir(null)}
                  disabled={!!excluindo}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#0d1f3c] disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={() => handleExcluir(confirmarExcluir)}
                  disabled={!!excluindo}
                  className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium disabled:opacity-50"
                >
                  {excluindo ? 'Excluindo...' : 'Excluir'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
