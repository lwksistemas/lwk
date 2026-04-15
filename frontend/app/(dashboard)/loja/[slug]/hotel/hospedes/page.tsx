'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import Link from 'next/link';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type Hospede = {
  id: number;
  nome: string;
  documento: string;
  telefone: string;
  email: string;
  observacoes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export default function HotelHospedesPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [items, setItems] = useState<Hospede[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Hospede | null>(null);

  const [form, setForm] = useState({
    nome: '',
    documento: '',
    telefone: '',
    email: '',
    observacoes: '',
  });

  const resetForm = () => setForm({ nome: '', documento: '', telefone: '', email: '', observacoes: '' });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.get<Hospede[] | { results?: Hospede[] }>('/hotel/hospedes/');
      const data = Array.isArray(r.data) ? r.data : (r.data.results ?? []);
      setItems(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao carregar hóspedes.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const openNew = () => {
    setEditing(null);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (h: Hospede) => {
    setEditing(h);
    setForm({
      nome: h.nome || '',
      documento: h.documento || '',
      telefone: h.telefone || '',
      email: h.email || '',
      observacoes: h.observacoes || '',
    });
    setModalOpen(true);
  };

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        nome: form.nome.trim(),
        documento: form.documento.trim(),
        telefone: form.telefone.trim(),
        email: form.email.trim(),
        observacoes: form.observacoes.trim(),
      };
      if (editing) {
        await apiClient.put(`/hotel/hospedes/${editing.id}/`, payload);
      } else {
        await apiClient.post(`/hotel/hospedes/`, payload);
      }
      setModalOpen(false);
      setEditing(null);
      resetForm();
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (h: Hospede) => {
    if (!confirm(`Excluir o hóspede "${h.nome}"?`)) return;
    try {
      await apiClient.delete(`/hotel/hospedes/${h.id}/`);
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Erro ao excluir.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Hóspedes</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">Cadastro de hóspedes (documento, telefone, email).</p>
          <Link href={`/loja/${slug}/hotel`} className="text-sm text-sky-700 hover:underline">
            ← Voltar
          </Link>
        </div>
        <Button onClick={openNew} className="min-h-[40px]">
          + Novo hóspede
        </Button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-600 dark:text-gray-400">Carregando...</div>
      ) : error ? (
        <div className="text-sm text-red-600">{error}</div>
      ) : (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg overflow-x-auto">
          <table className="min-w-[900px] w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-200">
              <tr>
                <th className="text-left p-3">Nome</th>
                <th className="text-left p-3">Documento</th>
                <th className="text-left p-3">Telefone</th>
                <th className="text-left p-3">Email</th>
                <th className="text-left p-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {items.map((h) => (
                <tr key={h.id} className="text-gray-900 dark:text-gray-100">
                  <td className="p-3 font-medium">{h.nome}</td>
                  <td className="p-3">{h.documento || '—'}</td>
                  <td className="p-3">{h.telefone || '—'}</td>
                  <td className="p-3">{h.email || '—'}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" onClick={() => openEdit(h)} className="min-h-[36px]">
                        Editar
                      </Button>
                      <Button variant="destructive" onClick={() => remove(h)} className="min-h-[36px]">
                        Excluir
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td className="p-3 text-gray-600 dark:text-gray-400" colSpan={5}>
                    Nenhum hóspede cadastrado.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="2xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold">{editing ? 'Editar hóspede' : 'Novo hóspede'}</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Dados do hóspede e observações.</p>
            </div>
            <button
              onClick={() => setModalOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
            >
              Fechar
            </button>
          </div>

          {error ? <div className="text-sm text-red-600">{error}</div> : null}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2 md:col-span-2">
              <Label>Nome *</Label>
              <Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <Label>Documento</Label>
              <Input value={form.documento} onChange={(e) => setForm((f) => ({ ...f, documento: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <Label>Telefone</Label>
              <Input value={form.telefone} onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Email</Label>
              <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Observações</Label>
              <textarea
                className="w-full min-h-[96px] px-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100"
                value={form.observacoes}
                onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>
              Cancelar
            </Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.nome.trim()}>
              {saving ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

