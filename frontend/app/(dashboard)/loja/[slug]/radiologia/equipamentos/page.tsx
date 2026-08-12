'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { ArrowLeft, Copy, Monitor, Plus, RefreshCw } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { useRadiologiaCrud } from '@/hooks/useRadiologiaCrud';
import type { Equipamento } from '@/lib/radiologia-types';

const empty = {
  nome: '',
  ae_title: '',
  modality: 'US',
  fabricante: '',
  modelo: '',
  numero_serie: '',
  suporte_mwl: true,
  suporte_dicom_storage: true,
  suporte_sr: false,
};

export default function RadiologiaEquipamentosPage() {
  const slug = useParams().slug as string;
  const { items, loading, error, saving, save, remove, load } = useRadiologiaCrud<Equipamento>(
    '/radiologia/equipamentos/',
  );
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Equipamento | null>(null);
  const [form, setForm] = useState(empty);
  const [actionError, setActionError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const openNew = () => {
    setEditing(null);
    setForm(empty);
    setOpen(true);
  };
  const openEdit = (e: Equipamento) => {
    setEditing(e);
    setForm({
      nome: e.nome,
      ae_title: e.ae_title,
      modality: e.modality || 'US',
      fabricante: e.fabricante || '',
      modelo: e.modelo || '',
      numero_serie: e.numero_serie || '',
      suporte_mwl: e.suporte_mwl,
      suporte_dicom_storage: e.suporte_dicom_storage,
      suporte_sr: e.suporte_sr,
    });
    setOpen(true);
  };
  const submit = async () => {
    setActionError(null);
    const ok = await save(
      {
        ...form,
        nome: form.nome.trim(),
        ae_title: form.ae_title.trim(),
        numero_serie: form.numero_serie.trim().toUpperCase(),
        is_active: true,
      },
      editing?.id,
    );
    if (ok) setOpen(false);
  };

  const copyCode = async (eq: Equipamento) => {
    if (!eq.codigo_vinculo) return;
    try {
      await navigator.clipboard.writeText(eq.codigo_vinculo);
      setCopiedId(eq.id);
      setTimeout(() => setCopiedId(null), 1500);
    } catch {
      setActionError('Não foi possível copiar o código.');
    }
  };

  const regenerar = async (id: number) => {
    if (!confirm('Gerar novo código de vínculo? O código anterior deixa de valer.')) return;
    setActionError(null);
    try {
      await apiClient.post(`/radiologia/equipamentos/${id}/regenerar-codigo/`);
      await load();
    } catch {
      setActionError('Falha ao regenerar código.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Monitor className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Equipamentos</h1>
              <p className="text-xs text-white/80">Serial do US + código aleatório vinculam à clínica (CPF/CNPJ)</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href={`/loja/${slug}/radiologia`} className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
              <ArrowLeft className="h-4 w-4" /> Voltar
            </Link>
            <button type="button" onClick={openNew} className="ml-auto inline-flex items-center gap-1 rounded-md bg-white px-3 py-2 text-sm font-semibold text-teal-800">
              <Plus className="h-4 w-4" /> Novo
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {(error || actionError) && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {actionError || error}
          </div>
        )}
        {loading ? (
          <div className="flex justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" /></div>
        ) : (
          <div className="overflow-x-auto overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full min-w-[880px] text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">AE Title</th>
                  <th className="px-4 py-3">Nº série</th>
                  <th className="px-4 py-3">Código vínculo</th>
                  <th className="px-4 py-3">MWL / Storage</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((e) => (
                  <tr key={e.id} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-3 font-medium">{e.nome}</td>
                    <td className="px-4 py-3 font-mono text-xs">{e.ae_title}</td>
                    <td className="px-4 py-3 font-mono text-xs">{e.numero_serie || '—'}</td>
                    <td className="px-4 py-3">
                      {e.codigo_vinculo ? (
                        <div className="flex items-center gap-1">
                          <span className="rounded bg-teal-50 px-2 py-0.5 font-mono text-xs font-semibold tracking-wider text-teal-900 dark:bg-teal-950 dark:text-teal-100">
                            {e.codigo_vinculo}
                          </span>
                          <button type="button" className="text-teal-700" title="Copiar" onClick={() => void copyCode(e)}>
                            <Copy className="h-3.5 w-3.5" />
                          </button>
                          {copiedId === e.id && <span className="text-[10px] text-teal-600">ok</span>}
                        </div>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {[e.suporte_mwl && 'MWL', e.suporte_dicom_storage && 'C-STORE', e.suporte_sr && 'SR']
                        .filter(Boolean)
                        .join(' · ') || '—'}
                    </td>
                    <td className="space-x-2 px-4 py-3 text-right text-xs">
                      <button type="button" className="inline-flex items-center gap-0.5 text-teal-700" onClick={() => void regenerar(e.id)}>
                        <RefreshCw className="h-3 w-3" /> Código
                      </button>
                      <button type="button" className="text-teal-700" onClick={() => openEdit(e)}>Editar</button>
                      <button type="button" className="text-red-600" onClick={() => remove(e.id, e.nome)}>Excluir</button>
                    </td>
                  </tr>
                ))}
                {!items.length && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-gray-500">
                      Nenhum ultrassom cadastrado. Cadastre com o número de série para vincular à clínica.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-xl bg-white p-5 shadow-xl dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold">{editing ? 'Editar equipamento' : 'Novo equipamento'}</h2>
            <p className="mb-3 text-xs text-gray-500">
              O sistema gera um código aleatório ao salvar. Ao receber exames, usa <strong>serial + CPF/CNPJ da clínica</strong> e o <strong>Accession</strong> do pedido.
            </p>
            <div className="space-y-3">
              <input className="w-full rounded-md border px-3 py-2" placeholder="Nome" value={form.nome} onChange={(ev) => setForm({ ...form, nome: ev.target.value })} />
              <input className="w-full rounded-md border px-3 py-2 font-mono" placeholder="AE Title (máx. 16)" maxLength={16} value={form.ae_title} onChange={(ev) => setForm({ ...form, ae_title: ev.target.value.toUpperCase() })} />
              <input
                className="w-full rounded-md border px-3 py-2 font-mono"
                placeholder="Número de série do ultrassom *"
                value={form.numero_serie}
                onChange={(ev) => setForm({ ...form, numero_serie: ev.target.value.toUpperCase() })}
              />
              {editing?.codigo_vinculo && (
                <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-2 text-sm dark:border-teal-900 dark:bg-teal-950">
                  Código vínculo: <span className="font-mono font-semibold tracking-wider">{editing.codigo_vinculo}</span>
                </div>
              )}
              <input className="w-full rounded-md border px-3 py-2" placeholder="Modalidade (US, CR, DX…)" value={form.modality} onChange={(ev) => setForm({ ...form, modality: ev.target.value.toUpperCase() })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Fabricante" value={form.fabricante} onChange={(ev) => setForm({ ...form, fabricante: ev.target.value })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="Modelo" value={form.modelo} onChange={(ev) => setForm({ ...form, modelo: ev.target.value })} />
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.suporte_mwl} onChange={(ev) => setForm({ ...form, suporte_mwl: ev.target.checked })} /> Consulta MWL</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.suporte_dicom_storage} onChange={(ev) => setForm({ ...form, suporte_dicom_storage: ev.target.checked })} /> DICOM Storage</label>
              <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.suporte_sr} onChange={(ev) => setForm({ ...form, suporte_sr: ev.target.checked })} /> SR de medidas</label>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-md px-3 py-2 text-sm" onClick={() => setOpen(false)}>Cancelar</button>
              <button
                type="button"
                disabled={saving || !form.nome.trim() || !form.ae_title.trim() || !form.numero_serie.trim()}
                className="rounded-md bg-teal-700 px-3 py-2 text-sm text-white disabled:opacity-50"
                onClick={() => void submit()}
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
