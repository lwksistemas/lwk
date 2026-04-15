'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import Link from 'next/link';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

type Quarto = { id: number; numero: string; nome?: string | null };

type Tarefa = {
  id: number;
  quarto: number;
  quarto_numero?: string;
  tipo: 'limpeza' | 'manutencao' | 'enxoval' | 'outros';
  status: 'aberta' | 'em_andamento' | 'concluida';
  descricao: string;
  prioridade: number;
  concluido_em: string | null;
  created_at: string;
  updated_at: string;
};

const TIPO_LABEL: Record<Tarefa['tipo'], string> = {
  limpeza: 'Limpeza',
  manutencao: 'Manutenção',
  enxoval: 'Enxoval',
  outros: 'Outros',
};
const STATUS_LABEL: Record<Tarefa['status'], string> = {
  aberta: 'Aberta',
  em_andamento: 'Em andamento',
  concluida: 'Concluída',
};

export default function HotelGovernancaPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [items, setItems] = useState<Tarefa[]>([]);
  const [quartos, setQuartos] = useState<Quarto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Tarefa | null>(null);

  const [form, setForm] = useState({
    quarto: '',
    tipo: 'limpeza' as Tarefa['tipo'],
    status: 'aberta' as Tarefa['status'],
    descricao: '',
    prioridade: 2,
  });

  const resetForm = () => setForm({ quarto: '', tipo: 'limpeza', status: 'aberta', descricao: '', prioridade: 2 });

  const loadBase = useCallback(async () => {
    try {
      const q = await apiClient.get<Quarto[] | { results?: Quarto[] }>('/hotel/quartos/');
      setQuartos(Array.isArray(q.data) ? q.data : (q.data.results ?? []));
    } catch {
      setQuartos([]);
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await apiClient.get<Tarefa[] | { results?: Tarefa[] }>('/hotel/governanca-tarefas/');
      const data = Array.isArray(r.data) ? r.data : (r.data.results ?? []);
      setItems(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Erro ao carregar tarefas.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBase();
    load();
  }, [loadBase, load]);

  const openNew = () => {
    setEditing(null);
    resetForm();
    setModalOpen(true);
  };

  const openEdit = (t: Tarefa) => {
    setEditing(t);
    setForm({
      quarto: String(t.quarto ?? ''),
      tipo: t.tipo,
      status: t.status,
      descricao: t.descricao || '',
      prioridade: Number(t.prioridade ?? 2),
    });
    setModalOpen(true);
  };

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        quarto: Number(form.quarto),
        tipo: form.tipo,
        status: form.status,
        descricao: (form.descricao || '').trim(),
        prioridade: Number(form.prioridade || 2),
      };
      if (editing) {
        await apiClient.put(`/hotel/governanca-tarefas/${editing.id}/`, payload);
      } else {
        await apiClient.post(`/hotel/governanca-tarefas/`, payload);
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

  const concluir = async (t: Tarefa) => {
    try {
      await apiClient.post(`/hotel/governanca-tarefas/${t.id}/concluir/`);
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Erro ao concluir.');
    }
  };

  const remove = async (t: Tarefa) => {
    if (!confirm(`Excluir a tarefa #${t.id}?`)) return;
    try {
      await apiClient.delete(`/hotel/governanca-tarefas/${t.id}/`);
      await load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Erro ao excluir.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Governança</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">Pendências por quarto (limpeza, manutenção, enxoval).</p>
          <Link href={`/loja/${slug}/hotel`} className="text-sm text-sky-700 hover:underline">
            ← Voltar
          </Link>
        </div>
        <Button onClick={openNew} className="min-h-[40px]">
          + Nova tarefa
        </Button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-600 dark:text-gray-400">Carregando...</div>
      ) : error ? (
        <div className="text-sm text-red-600">{error}</div>
      ) : (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg overflow-x-auto">
          <table className="min-w-[1000px] w-full text-sm">
            <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-200">
              <tr>
                <th className="text-left p-3">#</th>
                <th className="text-left p-3">Quarto</th>
                <th className="text-left p-3">Tipo</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Prioridade</th>
                <th className="text-left p-3">Descrição</th>
                <th className="text-left p-3">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              {items.map((t) => (
                <tr key={t.id} className="text-gray-900 dark:text-gray-100">
                  <td className="p-3 font-medium">#{t.id}</td>
                  <td className="p-3">{t.quarto_numero || String(t.quarto)}</td>
                  <td className="p-3">{TIPO_LABEL[t.tipo]}</td>
                  <td className="p-3">{STATUS_LABEL[t.status]}</td>
                  <td className="p-3">{t.prioridade}</td>
                  <td className="p-3">{t.descricao || '—'}</td>
                  <td className="p-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Button variant="outline" onClick={() => openEdit(t)} className="min-h-[36px]">
                        Editar
                      </Button>
                      {t.status !== 'concluida' && (
                        <Button onClick={() => concluir(t)} className="min-h-[36px]">
                          Concluir
                        </Button>
                      )}
                      <Button variant="destructive" onClick={() => remove(t)} className="min-h-[36px]">
                        Excluir
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td className="p-3 text-gray-600 dark:text-gray-400" colSpan={7}>
                    Nenhuma tarefa cadastrada.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} maxWidth="3xl">
        <div className="p-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold">{editing ? 'Editar tarefa' : 'Nova tarefa'}</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Registre pendências operacionais.</p>
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
              <Label>Quarto *</Label>
              <select
                className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100"
                value={form.quarto}
                onChange={(e) => setForm((f) => ({ ...f, quarto: e.target.value }))}
              >
                <option value="">Selecione</option>
                {quartos.map((q) => (
                  <option key={q.id} value={q.id}>
                    {q.numero} {q.nome ? `- ${q.nome}` : ''}
                  </option>
                ))}
              </select>
              <Link href={`/loja/${slug}/hotel/quartos`} className="text-xs text-sky-700 hover:underline">
                + cadastrar quarto
              </Link>
            </div>
            <div className="space-y-2">
              <Label>Tipo</Label>
              <select
                className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100"
                value={form.tipo}
                onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value as Tarefa['tipo'] }))}
              >
                <option value="limpeza">Limpeza</option>
                <option value="manutencao">Manutenção</option>
                <option value="enxoval">Enxoval</option>
                <option value="outros">Outros</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <select
                className="w-full h-10 px-3 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100"
                value={form.status}
                onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as Tarefa['status'] }))}
              >
                <option value="aberta">Aberta</option>
                <option value="em_andamento">Em andamento</option>
                <option value="concluida">Concluída</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>Prioridade (1 alta - 3 baixa)</Label>
              <Input
                type="number"
                min={1}
                max={3}
                value={form.prioridade}
                onChange={(e) => setForm((f) => ({ ...f, prioridade: Number(e.target.value || 2) }))}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label>Descrição</Label>
              <Input value={form.descricao} onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))} placeholder="Ex.: Limpeza pós check-out" />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setModalOpen(false)} className="min-h-[40px]" disabled={saving}>
              Cancelar
            </Button>
            <Button onClick={submit} className="min-h-[40px]" disabled={saving || !form.quarto}>
              {saving ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

