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
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Funcionários</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">Gerencie a equipe do hotel.</p>
          <Link href={`/loja/${slug}/hotel/configuracoes`} className="text-sm text-sky-700 hover:underline">← Voltar</Link>
        </div>
        <Button onClick={openNew} className="min-h-[40px]">+ Novo funcionário</Button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-600 dark:text-gray-400">Carregando...</div>
      ) : error && !modalOpen ? (
        <div className="text-sm text-red-600">{error}</div>
      ) : (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg overflow-x-auto">
          <table className="min-w-[700px] w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-200">
              <tr>
                <th className="text-left p-3">Nome</th>
                <th className="text-left p-3">Email</th>
                <th className="text-left p-3">Cargo</th>
                <th className="text-left p-3">Telefone</th>
                <th className="text-left p-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {items.map((f) => (
                <tr key={f.id} className="text-gray-900 dark:text-gray-100">
                  <td className="p-3 font-medium">{f.nome}</td>
                  <td className="p-3">{f.email || '—'}</td>
                  <td className="p-3">{f.cargo || '—'}</td>
                  <td className="p-3">{f.telefone || '—'}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" onClick={() => openEdit(f)} className="min-h-[36px]">Editar</Button>
                      <Button variant="destructive" onClick={() => remove(f)} className="min-h-[36px]">Excluir</Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td className="p-3 text-gray-600 dark:text-gray-400" colSpan={5}>Nenhum funcionário cadastrado.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

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
