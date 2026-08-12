'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { fetchLaudoPdf, finalizarLaudo, salvarLaudo } from '@/lib/radiologia-api';
import type { Laudo } from '@/lib/radiologia-types';

export default function RadiologiaLaudoEditorPage() {
  const params = useParams();
  const slug = params.slug as string;
  const id = Number(params.id);
  const [laudo, setLaudo] = useState<Laudo | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    medico_laudador: '',
    crm_laudador: '',
    texto: '',
    conclusao: '',
    bi_rads: '',
  });

  useEffect(() => {
    apiClient
      .get(`/radiologia/laudos/${id}/`)
      .then((res) => {
        const l = res.data as Laudo;
        setLaudo(l);
        setForm({
          medico_laudador: l.medico_laudador || '',
          crm_laudador: l.crm_laudador || '',
          texto: l.texto || '',
          conclusao: l.conclusao || '',
          bi_rads: l.bi_rads || '',
        });
      })
      .catch(() => setError('Laudo não encontrado.'))
      .finally(() => setLoading(false));
  }, [id]);

  const onSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await salvarLaudo(id, form);
      setLaudo(updated);
    } catch {
      setError('Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  };

  const onFinalizar = async (assinar: boolean) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await finalizarLaudo(id, { ...form, assinar });
      setLaudo(updated);
    } catch {
      setError('Erro ao finalizar.');
    } finally {
      setSaving(false);
    }
  };

  const onPdf = async () => {
    try {
      const result = await fetchLaudoPdf(id);
      if (result.url) {
        window.open(result.url, '_blank');
        return;
      }
      if (result.blob) {
        const url = URL.createObjectURL(result.blob);
        window.open(url, '_blank');
      }
    } catch {
      setError('Não foi possível abrir o PDF.');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" />
      </div>
    );
  }

  if (!laudo) {
    return <div className="p-8 text-red-600">{error || 'Laudo não encontrado'}</div>;
  }

  const locked = laudo.status === 'finalizado' || laudo.status === 'assinado' || laudo.status === 'entregue';

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="flex w-full max-w-full flex-col gap-3 px-4 py-4 sm:px-6">
          <div>
            <h1 className="text-xl font-bold">Laudo · {laudo.accession_number}</h1>
            <p className="text-xs text-white/80">{laudo.paciente_nome} · {laudo.status}</p>
          </div>
          <Link href={`/loja/${slug}/radiologia/laudos`} className="inline-flex w-fit items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
            <ArrowLeft className="h-4 w-4" /> Voltar
          </Link>
        </div>
      </header>

      <main className="w-full max-w-full space-y-4 px-4 py-6 sm:px-6">
        {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="rounded-md border px-3 py-2"
            placeholder="Médico laudador"
            disabled={locked}
            value={form.medico_laudador}
            onChange={(e) => setForm({ ...form, medico_laudador: e.target.value })}
          />
          <input
            className="rounded-md border px-3 py-2"
            placeholder="CRM"
            disabled={locked}
            value={form.crm_laudador}
            onChange={(e) => setForm({ ...form, crm_laudador: e.target.value })}
          />
        </div>
        <textarea
          className="min-h-[220px] w-full rounded-md border px-3 py-2"
          placeholder="Texto do laudo"
          disabled={locked}
          value={form.texto}
          onChange={(e) => setForm({ ...form, texto: e.target.value })}
        />
        <textarea
          className="min-h-[100px] w-full rounded-md border px-3 py-2"
          placeholder="Conclusão"
          disabled={locked}
          value={form.conclusao}
          onChange={(e) => setForm({ ...form, conclusao: e.target.value })}
        />
        <input
          className="w-full max-w-xs rounded-md border px-3 py-2"
          placeholder="BI-RADS (opcional)"
          disabled={locked}
          value={form.bi_rads}
          onChange={(e) => setForm({ ...form, bi_rads: e.target.value })}
        />
        <p className="text-xs text-gray-500">
          Assinatura ICP-Brasil em nuvem entra na Fase 1 do piloto. O PDF atual é gerado localmente no RIS.
        </p>
        <div className="flex flex-wrap gap-2">
          {!locked && (
            <>
              <button type="button" disabled={saving} className="rounded-md border px-3 py-2 text-sm" onClick={() => void onSave()}>
                Salvar rascunho
              </button>
              <button type="button" disabled={saving} className="rounded-md bg-teal-700 px-3 py-2 text-sm text-white" onClick={() => void onFinalizar(false)}>
                Finalizar + PDF
              </button>
              <button type="button" disabled={saving} className="rounded-md bg-teal-900 px-3 py-2 text-sm text-white" onClick={() => void onFinalizar(true)}>
                Finalizar (marcar assinado)
              </button>
            </>
          )}
          <button type="button" className="rounded-md bg-white px-3 py-2 text-sm text-teal-800 shadow" onClick={() => void onPdf()}>
            Ver PDF
          </button>
          {laudo.pdf_url ? (
            <a href={laudo.pdf_url} target="_blank" rel="noreferrer" className="rounded-md px-3 py-2 text-sm text-teal-700 underline">
              PDF arquivado
            </a>
          ) : null}
        </div>
      </main>
    </div>
  );
}
