'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import Link from 'next/link';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type Quarto = {
  id: number;
  numero: string;
  nome: string;
  tipo: string;
  capacidade: number;
  status: 'disponivel' | 'ocupado' | 'limpeza' | 'manutencao';
  observacoes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

const STATUS_LABEL: Record<Quarto['status'], string> = {
  disponivel: 'Disponível',
  ocupado: 'Ocupado',
  limpeza: 'Limpeza',
  manutencao: 'Manutenção',
};

export default function HotelQuartosPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [items, setItems] = useState<Quarto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Quarto | null>(null);

  const [form, setForm] = useState({
    numero: '',
    nome: '',
    tipo: '',
    capacidade: 2,
    status: 'disponivel' as Quarto['status'],
    observacoes: '',
  });

  const resetForm = useCallback(() => {
    setForm({ numero: '', nome: '', tipo: '', capacidade: 2, status: 'disponivel', observacoes: '' });
  }, []);

  const openNew = () => {
    setEditing(null);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (q: Quarto) => {
    setEditing(q);
    setForm({
      numero: q.numero || '',
      nome: q.nome || '',
      tipo: q.tipo || '',
      capacidade: Number(q.capacidade || 2),
      status: q.status || 'disponivel',
      observacoes: q.observacoes || '',
    });
    setModalOpen(true);
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.get<Quarto[] | { results?: Quarto[] }>('/hotel/quartos/');
      const data = Array.isArray(r.data) ? r.data : (r.data.results ?? []);
      setItems(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao carregar quartos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        numero: form.numero.trim(),
        nome: form.nome.trim(),
        tipo: form.tipo.trim(),
        capacidade: Number(form.capacidade || 0),
        status: form.status,
        observacoes: form.observacoes.trim(),
      };
      if (editing) {
        await apiClient.put(`/hotel/quartos/${editing.id}/`, payload);
      } else {
        await apiClient.post(`/hotel/quartos/`, payload);
      }
      setModalOpen(false);
      setEditing(null);
      resetForm();
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.response?.data?.numero?.[0] || 'Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (q: Quarto) => {
    if (!confirm(`Excluir o quarto "${q.numero}"?`)) return;
    try {
      await apiClient.delete(`/hotel/quartos/${q.id}/`);
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Erro ao excluir.');
    }
  };

  const summary = useMemo(() => {
    const total = items.length;
    const byStatus = items.reduce(
      (acc, it) => {
        acc[it.status] = (acc[it.status] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );
    return { total, byStatus };
  }, [items]);

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Quartos</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Total: {summary.total} • Disponível: {summary.byStatus.disponivel || 0} • Ocupado: {summary.byStatus.ocupado || 0} • Limpeza:{' '}
            {summary.byStatus.limpeza || 0} • Manutenção: {summary.byStatus.manutencao || 0}
          </p>
          <Link href={`/loja/${slug}/hotel`} className="text-sm text-sky-700 hover:underline">
            ← Voltar
          </Link>
        </div>
        <Button onClick={openNew} className="min-h-[40px]">
          + Novo quarto
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
                <th className="text-left p-3">Número</th>
                <th className="text-left p-3">Nome</th>
                <th className="text-left p-3">Tipo</th>
                <th className="text-left p-3">Capacidade</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {items.map((q) => (
                <tr key={q.id} className="text-gray-900 dark:text-gray-100">
                  <td className="p-3 font-medium">{q.numero}</td>
                  <td className="p-3">{q.nome || '—'}</td>
                  <td className="p-3">{q.tipo || '—'}</td>
                  <td className="p-3">{q.capacidade}</td>
                  <td className="p-3">{STATUS_LABEL[q.status]}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" onClick={() => openEdit(q)} className="min-h-[36px]">
                        Editar
                      </Button>
                      <Button variant="destructive" onClick={() => remove(q)} className="min-h-[36px]">
                        Excluir
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td className="p-3 text-gray-600 dark:text-gray-400" colSpan={6}>
                    Nenhum quarto cadastrado.
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
              <h2 className="text-xl font-bold">{editing ? 'Editar quarto' : 'Novo quarto'}</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Cadastre a unidade e o status operacional.</p>
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
            <div className="space-y-2">
              <Label>Número *</Label>
              <Input value={form.numero} onChange={(e) => setForm((f) => ({ ...f, numero: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <Label>Nome</Label>
              <Input value={form.nome} onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))} placeholder="Ex.: Suíte 203" />
            </div>
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Input value={form.tipo} onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value }))} placeholder="Ex.: Standard" />
            </div>
            <div className="space-y-2">
              <Label>Capacidade</Label>
              <Input
                type="number"
                value={form.capacidade}
                onChange={(e) => setForm((f) => ({ ...f, capacidade: Number(e.target.value || 0) }))}
                min={1}
              />
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <select
                className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100"
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as Quarto['status'] }))}
              >
                <option value="disponivel">Disponível</option>
                <option value="ocupado">Ocupado</option>
                <option value="limpeza">Limpeza</option>
                <option value="manutencao">Manutenção</option>
              </select>
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
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.numero.trim()}>
              {saving ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

