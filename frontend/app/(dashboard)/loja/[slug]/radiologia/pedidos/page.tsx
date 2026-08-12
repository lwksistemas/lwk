'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, ClipboardList, Plus } from 'lucide-react';
import apiClient from '@/lib/api-client';
import {
  abrirLaudo,
  cancelarPedido,
  listEquipamentos,
  listPacientes,
  listPedidos,
  listProcedimentos,
  publicarMwl,
  sincronizarImagensPedido,
} from '@/lib/radiologia-api';
import type { Equipamento, PacienteRadiologia, PedidoExame, Procedimento } from '@/lib/radiologia-types';
import { PEDIDO_STATUS_LABEL } from '@/lib/radiologia-types';

export default function RadiologiaPedidosPage() {
  const slug = useParams().slug as string;
  const router = useRouter();
  const [items, setItems] = useState<PedidoExame[]>([]);
  const [pacientes, setPacientes] = useState<PacienteRadiologia[]>([]);
  const [procedimentos, setProcedimentos] = useState<Procedimento[]>([]);
  const [equipamentos, setEquipamentos] = useState<Equipamento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    paciente: '',
    procedimento: '',
    equipamento: '',
    medico_solicitante: '',
    crm_solicitante: '',
    indicacao_clinica: '',
    agendado_para: '',
    observacoes: '',
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [pedidos, pacs, procs, equips] = await Promise.all([
        listPedidos(),
        listPacientes(),
        listProcedimentos(),
        listEquipamentos(),
      ]);
      setItems(pedidos);
      setPacientes(pacs as PacienteRadiologia[]);
      setProcedimentos(procs as Procedimento[]);
      setEquipamentos(equips as Equipamento[]);
    } catch {
      setError('Erro ao carregar pedidos.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const submit = async () => {
    setSaving(true);
    try {
      await apiClient.post('/radiologia/pedidos/', {
        paciente: Number(form.paciente),
        procedimento: Number(form.procedimento),
        equipamento: form.equipamento ? Number(form.equipamento) : null,
        medico_solicitante: form.medico_solicitante.trim(),
        crm_solicitante: form.crm_solicitante.trim(),
        indicacao_clinica: form.indicacao_clinica.trim(),
        agendado_para: form.agendado_para || new Date().toISOString(),
        observacoes: form.observacoes.trim(),
      });
      setOpen(false);
      await load();
    } catch {
      setError('Não foi possível criar o pedido.');
    } finally {
      setSaving(false);
    }
  };

  const onPublicar = async (id: number) => {
    try {
      await publicarMwl(id);
      await load();
    } catch {
      setError('Falha ao publicar MWL.');
    }
  };

  const onCancelar = async (id: number) => {
    if (!confirm('Cancelar este pedido e remover da worklist?')) return;
    try {
      await cancelarPedido(id);
      await load();
    } catch {
      setError('Falha ao cancelar.');
    }
  };

  const onLaudo = async (id: number) => {
    try {
      const laudo = await abrirLaudo(id);
      router.push(`/loja/${slug}/radiologia/laudos/${laudo.id}`);
    } catch {
      setError('Falha ao abrir laudo.');
    }
  };

  const onSincronizar = async (id: number) => {
    try {
      await sincronizarImagensPedido(id);
      await load();
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? String((err as { response?: { data?: { error?: string } } }).response?.data?.error || '')
          : '';
      setError(msg || 'Falha ao arquivar imagens DICOM na pasta do paciente.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <ClipboardList className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Pedidos / Worklist</h1>
              <p className="text-xs text-white/80">Accession e Study UID gerados no RIS</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href={`/loja/${slug}/radiologia`} className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
              <ArrowLeft className="h-4 w-4" /> Voltar
            </Link>
            <button type="button" onClick={() => setOpen(true)} className="ml-auto inline-flex items-center gap-1 rounded-md bg-white px-3 py-2 text-sm font-semibold text-teal-800">
              <Plus className="h-4 w-4" /> Novo pedido
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {error && <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        {loading ? (
          <div className="flex justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" /></div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-3 py-3">Accession</th>
                  <th className="px-3 py-3">Paciente</th>
                  <th className="px-3 py-3">Procedimento</th>
                  <th className="px-3 py-3">Equipamento</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="px-3 py-3 font-mono text-xs">{p.accession_number || '—'}</td>
                    <td className="px-3 py-3">{p.paciente_nome}</td>
                    <td className="px-3 py-3">{p.procedimento_nome}</td>
                    <td className="px-3 py-3 text-xs">
                      {p.equipamento_nome ? (
                        <span>
                          {p.equipamento_nome}
                          {p.equipamento_ae_title ? (
                            <span className="ml-1 font-mono text-[10px] text-gray-500">({p.equipamento_ae_title})</span>
                          ) : null}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <span className="rounded-full bg-teal-50 px-2 py-0.5 text-xs text-teal-800 dark:bg-teal-950 dark:text-teal-200">
                        {PEDIDO_STATUS_LABEL[p.status] || p.status}
                      </span>
                    </td>
                    <td className="space-x-2 px-3 py-3 text-right text-xs">
                      <button type="button" className="text-teal-700" onClick={() => void onPublicar(p.id)}>MWL</button>
                      <button type="button" className="text-teal-700" onClick={() => void onSincronizar(p.id)} title="Arquivar ZIP DICOM na pasta do paciente">
                        DICOM
                      </button>
                      {p.dicom_media_url && (
                        <a className="text-teal-700" href={p.dicom_media_url} target="_blank" rel="noreferrer">ZIP</a>
                      )}
                      <Link className="text-teal-700" href={`/loja/${slug}/radiologia/viewer?study=${encodeURIComponent(p.study_instance_uid)}`}>Viewer</Link>
                      <button type="button" className="text-teal-700" onClick={() => void onLaudo(p.id)}>Laudo</button>
                      {p.status !== 'cancelado' && (
                        <button type="button" className="text-red-600" onClick={() => void onCancelar(p.id)}>Cancelar</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-5 shadow-xl dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold">Novo pedido</h2>
            <div className="space-y-3">
              <select className="w-full rounded-md border px-3 py-2" value={form.paciente} onChange={(e) => setForm({ ...form, paciente: e.target.value })}>
                <option value="">Paciente</option>
                {pacientes.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
              </select>
              <select className="w-full rounded-md border px-3 py-2" value={form.procedimento} onChange={(e) => setForm({ ...form, procedimento: e.target.value })}>
                <option value="">Procedimento</option>
                {procedimentos.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}
              </select>
              <select className="w-full rounded-md border px-3 py-2" value={form.equipamento} onChange={(e) => setForm({ ...form, equipamento: e.target.value })}>
                <option value="">Equipamento (obrigatório)</option>
                {equipamentos.map((e) => <option key={e.id} value={e.id}>{e.nome} ({e.ae_title})</option>)}
              </select>
              {!equipamentos.length && (
                <p className="text-xs text-amber-700">
                  Cadastre o ultrassom em{' '}
                  <Link href={`/loja/${slug}/radiologia/equipamentos`} className="underline">
                    Equipamentos
                  </Link>
                  {' '}(liberado pelo Super Admin) antes de criar o pedido.
                </p>
              )}
              <input className="w-full rounded-md border px-3 py-2" placeholder="Médico solicitante" value={form.medico_solicitante} onChange={(e) => setForm({ ...form, medico_solicitante: e.target.value })} />
              <input className="w-full rounded-md border px-3 py-2" placeholder="CRM" value={form.crm_solicitante} onChange={(e) => setForm({ ...form, crm_solicitante: e.target.value })} />
              <input type="datetime-local" className="w-full rounded-md border px-3 py-2" value={form.agendado_para} onChange={(e) => setForm({ ...form, agendado_para: e.target.value })} />
              <textarea className="w-full rounded-md border px-3 py-2" rows={3} placeholder="Indicação clínica" value={form.indicacao_clinica} onChange={(e) => setForm({ ...form, indicacao_clinica: e.target.value })} />
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-md px-3 py-2 text-sm" onClick={() => setOpen(false)}>Cancelar</button>
              <button
                type="button"
                disabled={saving || !form.paciente || !form.procedimento || !form.equipamento}
                className="rounded-md bg-teal-700 px-3 py-2 text-sm text-white disabled:opacity-50"
                onClick={() => void submit()}
              >
                Criar e publicar MWL
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
