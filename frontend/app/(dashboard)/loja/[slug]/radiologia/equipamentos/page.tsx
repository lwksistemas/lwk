'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState } from 'react';
import { ArrowLeft, Copy, Link2, Monitor, RefreshCw } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { useRadiologiaCrud } from '@/hooks/useRadiologiaCrud';
import type { Equipamento } from '@/lib/radiologia-types';

export default function RadiologiaEquipamentosPage() {
  const slug = useParams().slug as string;
  const { items, loading, error, load } = useRadiologiaCrud<Equipamento>(
    '/radiologia/equipamentos/',
  );
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionOk, setActionOk] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

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
    setActionOk(null);
    try {
      await apiClient.post(`/radiologia/equipamentos/${id}/regenerar-codigo/`);
      await load();
      setActionOk('Novo código gerado.');
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? String((err as { response?: { data?: { error?: string } } }).response?.data?.error || '')
          : '';
      setActionError(msg || 'Falha ao regenerar código.');
    }
  };

  const processarVinculo = async (id: number) => {
    setBusyId(id);
    setActionError(null);
    setActionOk(null);
    try {
      const res = await apiClient.post(`/radiologia/equipamentos/${id}/processar-vinculo/`);
      const serial = res.data?.numero_serie || '';
      await load();
      setActionOk(
        serial
          ? `Vínculo OK. Serial lido do DICOM: ${serial}`
          : 'Vínculo processado com sucesso.',
      );
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? String((err as { response?: { data?: { error?: string } } }).response?.data?.error || '')
          : '';
      setActionError(msg || 'Exame de vínculo ainda não chegou ao PACS.');
    } finally {
      setBusyId(null);
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
              <p className="text-xs text-white/80">
                Máquinas liberadas pelo Super Admin — pareie o DICOM e use no exame
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href={`/loja/${slug}/radiologia`} className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
              <ArrowLeft className="h-4 w-4" /> Voltar
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="mb-4 rounded-xl border border-teal-200 bg-teal-50/80 p-4 text-sm text-teal-950 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
          <p className="font-semibold">Como usar a máquina</p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs sm:text-sm">
            <li>O Super Admin cadastra, cobra e <strong>libera</strong> o aparelho nesta clínica.</li>
            <li>Configure no US: PACS <code className="rounded bg-white/60 px-1">LWKPACS</code> · IP <code className="rounded bg-white/60 px-1">201.23.81.50</code> · porta <code className="rounded bg-white/60 px-1">4242</code>.</li>
            <li>Envie um exame de teste com o <strong>código</strong> no Accession Number e clique em <strong>Vincular</strong>.</li>
            <li>Ao abrir o exame do paciente, <strong>escolha este aparelho</strong> na lista.</li>
          </ol>
        </div>

        {actionOk && (
          <div className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{actionOk}</div>
        )}
        {(error || actionError) && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {actionError || error}
          </div>
        )}
        {loading ? (
          <div className="flex justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" /></div>
        ) : (
          <div className="overflow-x-auto overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full min-w-[960px] text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-xs uppercase text-gray-500 dark:bg-gray-800">
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">AE Title</th>
                  <th className="px-4 py-3">Código</th>
                  <th className="px-4 py-3">Serial (DICOM)</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody>
                {items.map((e) => (
                  <tr key={e.id} className="border-b border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-3 font-medium">{e.nome}</td>
                    <td className="px-4 py-3 font-mono text-xs">{e.ae_title}</td>
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
                    <td className="px-4 py-3 font-mono text-xs">{e.numero_serie || '—'}</td>
                    <td className="px-4 py-3">
                      {e.vinculado_em ? (
                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">
                          Vinculado
                        </span>
                      ) : (
                        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-800 dark:bg-amber-950 dark:text-amber-200">
                          Aguardando exame
                        </span>
                      )}
                    </td>
                    <td className="space-x-2 px-4 py-3 text-right text-xs">
                      <button
                        type="button"
                        disabled={busyId === e.id}
                        className="inline-flex items-center gap-0.5 text-teal-700 disabled:opacity-50"
                        onClick={() => void processarVinculo(e.id)}
                        title="Buscar exame com este código no PACS e ler o serial"
                      >
                        <Link2 className="h-3 w-3" />
                        {busyId === e.id ? '…' : 'Vincular'}
                      </button>
                      {!e.vinculado_em && (
                        <button type="button" className="inline-flex items-center gap-0.5 text-teal-700" onClick={() => void regenerar(e.id)}>
                          <RefreshCw className="h-3 w-3" /> Código
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {!items.length && (
                  <tr>
                    <td colSpan={6} className="px-4 py-10 text-center text-gray-500">
                      Nenhum aparelho liberado. O Super Admin precisa cadastrar e liberar a máquina nesta clínica.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
