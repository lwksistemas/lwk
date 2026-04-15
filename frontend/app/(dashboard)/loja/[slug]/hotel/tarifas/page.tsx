'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import Link from 'next/link';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type Tarifa = {
  id: number;
  nome: string;
  tipo_quarto: string;
  valor_diaria: string | number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export default function HotelTarifasPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [items, setItems] = useState<Tarifa[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Tarifa | null>(null);

  const [form, setForm] = useState({
    nome: '',
    tipo_quarto: '',
    valor_diaria: '',
  });

  const resetForm = () => setForm({ nome: '', tipo_quarto: '', valor_diaria: '' });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.get<Tarifa[] | { results?: Tarifa[] }>('/hotel/tarifas/');
      const data = Array.isArray(r.data) ? r.data : (r.data.results ?? []);
      setItems(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao carregar tarifas.');
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

  const openEdit = (t: Tarifa) => {
    setEditing(t);
    setForm({
      nome: t.nome || '',
      tipo_quarto: t.tipo_quarto || '',
      valor_diaria: String(t.valor_diaria ?? ''),
    });
    setModalOpen(true);
  };

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        nome: form.nome.trim(),
        tipo_quarto: form.tipo_quarto.trim(),
        valor_diaria: Number(String(form.valor_diaria).replace(',', '.')),
      };
      if (editing) {
        await apiClient.put(`/hotel/tarifas/${editing.id}/`, payload);
      } else {
        await apiClient.post(`/hotel/tarifas/`, payload);
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

  const remove = async (t: Tarifa) => {
    if (!confirm(`Excluir a tarifa "${t.nome}"?`)) return;
    try {
      await apiClient.delete(`/hotel/tarifas/${t.id}/`);
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Erro ao excluir.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Tarifas</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">Tarifário base e valores de diária.</p>
          <Link href={`/loja/${slug}/hotel`} className="text-sm text-sky-700 hover:underline">
            ← Voltar
          </Link>
        </div>
        <Button onClick={openNew} className="min-h-[40px]">
          + Nova tarifa
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
                <th className="text-left p-3">Tipo quarto</th>
                <th className="text-left p-3">Diária</th>
                <th className="text-left p-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {items.map((t) => (
                <tr key={t.id} className="text-gray-900 dark:text-gray-100">
                  <td className="p-3 font-medium">{t.nome}</td>
                  <td className="p-3">{t.tipo_quarto || '—'}</td>
                  <td className="p-3">R$ {Number(String(t.valor_diaria).replace(',', '.')).toFixed(2)}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2">
                      <Button variant="outline" onClick={() => openEdit(t)} className="min-h-[36px]">
                        Editar
                      </Button>
                      <Button variant="destructive" onClick={() => remove(t)} className="min-h-[36px]">
                        Excluir
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td className="p-3 text-gray-600 dark:text-gray-400" colSpan={4}>
                    Nenhuma tarifa cadastrada.
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
              <h2 className="text-xl font-bold">{editing ? 'Editar tarifa' : 'Nova tarifa'}</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Use tipo_quarto para diferenciar categorias.</p>
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
              <Label>Tipo quarto</Label>
              <Input value={form.tipo_quarto} onChange={(e) => setForm((f) => ({ ...f, tipo_quarto: e.target.value }))} placeholder="Ex.: Standard" />
            </div>
            <div className="space-y-2">
              <Label>Valor diária (R$) *</Label>
              <Input value={form.valor_diaria} onChange={(e) => setForm((f) => ({ ...f, valor_diaria: e.target.value }))} placeholder="Ex.: 285.00" />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>
              Cancelar
            </Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.nome.trim() || !String(form.valor_diaria).trim()}>
              {saving ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

