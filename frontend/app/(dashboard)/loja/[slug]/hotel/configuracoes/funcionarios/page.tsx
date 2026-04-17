'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import apiClient from '@/lib/api-client';

interface Funcionario {
  id: number;
  nome: string;
  email: string;
  cargo: string;
  telefone: string;
  is_active: boolean;
}

export default function HotelFuncionariosPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';

  const [items, setItems] = useState<Funcionario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Funcionario | null>(null);
  const [form, setForm] = useState({ nome: '', email: '', cargo: '', telefone: '' });

  const resetForm = () => setForm({ nome: '', email: '', cargo: '', telefone: '' });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.get<Funcionario[] | { results?: Funcionario[] }>('/hotel/funcionarios/');
      const data = Array.isArray(r.data) ? r.data : (r.data.results ?? []);
      setItems(data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      // Se endpoint não existe ainda, mostra lista vazia
      if (err?.response?.data?.detail === 'Not found.' || (e as { response?: { status?: number } })?.response?.status === 404) {
        setItems([]);
      } else {
        setError(err?.response?.data?.detail || 'Erro ao carregar funcionários.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openNew = () => { setEditing(null); resetForm(); setModalOpen(true); };
  const openEdit = (f: Funcionario) => {
    setEditing(f);
    setForm({ nome: f.nome || '', email: f.email || '', cargo: f.cargo || '', telefone: f.telefone || '' });
    setModalOpen(true);
  };

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = { nome: form.nome.trim(), email: form.email.trim(), cargo: form.cargo.trim(), telefone: form.telefone.trim() };
      if (editing) {
        await apiClient.put(`/hotel/funcionarios/${editing.id}/`, payload);
      } else {
        await apiClient.post('/hotel/funcionarios/', payload);
      }
      setModalOpen(false);
      setEditing(null);
      resetForm();
      await load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string; [k: string]: unknown } } };
      const detail = err?.response?.data?.detail;
      if (detail) setError(detail);
      else if (err?.response?.data) {
        const firstError = Object.values(err.response.data).flat()[0];
        setError(typeof firstError === 'string' ? firstError : 'Erro ao salvar.');
      } else setError('Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (f: Funcionario) => {
    if (!confirm(`Excluir "${f.nome}"?`)) return;
    try {
      await apiClient.delete(`/hotel/funcionarios/${f.id}/`);
      await load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || 'Erro ao excluir.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg"><svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg></div>
              <div><h1 className="text-2xl font-bold">Funcionários</h1><p className="text-white/80 text-sm">Gerencie a equipe do hotel ({items.length})</p></div>
            </div>
            <div className="flex items-center gap-2">
              <Link href={`/loja/${slug}/hotel/configuracoes`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg> Voltar</Link>
              <button onClick={openNew} className="px-4 py-2 bg-white text-sky-700 font-semibold rounded-md hover:bg-sky-50 transition-colors text-sm flex items-center gap-1 shadow">+ Novo funcionário</button>
            </div>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" /></div>
      ) : error && !modalOpen ? (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">{error}</div>
      ) : items.length === 0 ? (
        <div className="text-center py-20"><svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg><p className="text-lg font-medium text-gray-600 dark:text-gray-400">Nenhum funcionário cadastrado</p></div>
      ) : (
        <>
          {/* Mobile: Cards */}
          <div className="sm:hidden space-y-3">
            {items.map((f) => (
              <div key={f.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 shadow-sm">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="font-semibold text-gray-900 dark:text-white">{f.nome}</p>
                  {f.cargo && <span className="shrink-0 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">{f.cargo}</span>}
                </div>
                <div className="space-y-0.5 text-xs text-gray-500 dark:text-gray-400">
                  {f.email && <p>{f.email}</p>}
                  {f.telefone && <p>{f.telefone}</p>}
                </div>
                <div className="flex items-center gap-2 mt-3">
                  <Button variant="outline" onClick={() => openEdit(f)} className="min-h-[32px] text-xs">Editar</Button>
                  <Button variant="destructive" onClick={() => remove(f)} className="min-h-[32px] text-xs ml-auto">Excluir</Button>
                </div>
              </div>
            ))}
          </div>
          {/* Desktop: Table */}
          <div className="hidden sm:block bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-800/80 border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Nome</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Email</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Cargo</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Telefone</th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Ações</th>
            </tr></thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {items.map((f) => (
                <tr key={f.id} className="hover:bg-sky-50/50 dark:hover:bg-gray-800/50 transition-colors">
                  <td className="py-3 px-4 font-medium text-gray-900 dark:text-white">{f.nome}</td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{f.email || '—'}</td>
                  <td className="py-3 px-4"><span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">{f.cargo || '—'}</span></td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{f.telefone || '—'}</td>
                  <td className="py-3 px-4"><div className="flex items-center justify-end gap-1.5">
                    <Button variant="outline" onClick={() => openEdit(f)} className="min-h-[36px]">Editar</Button>
                    <Button variant="destructive" onClick={() => remove(f)} className="min-h-[36px]">Excluir</Button>
                  </div></td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
        </>
      )}
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="2xl">
        <div className="p-6 space-y-4">
          <h2 className="text-xl font-bold">{editing ? 'Editar funcionário' : 'Novo funcionário'}</h2>
          {error && <div className="text-sm text-red-600">{error}</div>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2 md:col-span-2"><Label>Nome *</Label><Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} /></div>
            <div className="space-y-2"><Label>Cargo</Label><Input value={form.cargo} onChange={(e) => setForm((f) => ({ ...f, cargo: e.target.value }))} placeholder="Ex.: Recepcionista" /></div>
            <div className="space-y-2"><Label>Telefone</Label><Input value={form.telefone} onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))} /></div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>Cancelar</Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.nome.trim()}>{saving ? 'Salvando...' : 'Salvar'}</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
