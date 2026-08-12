'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';
import { ArrowLeft, Activity } from 'lucide-react';
import apiClient from '@/lib/api-client';

function ViewerInner() {
  const slug = useParams().slug as string;
  const search = useSearchParams();
  const study = search.get('study') || '';
  const [studyInput, setStudyInput] = useState(study);
  const [meta, setMeta] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadStudy = async () => {
    setLoading(true);
    setError(null);
    setMeta('');
    try {
      const uid = studyInput.trim();
      const res = await apiClient.get('/radiologia/dicomweb/studies', {
        params: uid ? { StudyInstanceUID: uid } : undefined,
      });
      setMeta(typeof res.data === 'string' ? res.data : JSON.stringify(res.data, null, 2));
    } catch {
      setError(
        'Proxy DICOMweb falhou. Confira Orthanc na VM de imagens e se o StudyInstanceUID pertence a um pedido desta loja.',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <header className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow">
        <div className="flex w-full max-w-full flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Activity className="hidden h-6 w-6 sm:block" />
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Viewer / DICOMweb</h1>
              <p className="text-xs text-white/80">Acesso só via proxy Django (tenant + auditoria)</p>
            </div>
          </div>
          <Link href={`/loja/${slug}/radiologia`} className="inline-flex w-fit items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25">
            <ArrowLeft className="h-4 w-4" /> Voltar
          </Link>
        </div>
      </header>

      <main className="w-full max-w-full space-y-4 px-4 py-6 sm:px-6 lg:px-8">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          O OHIF na VM de imagens deve apontar o data source para{' '}
          <code className="rounded bg-gray-100 px-1 text-xs dark:bg-gray-800">/api/radiologia/dicomweb/</code>.
          Aqui você valida o proxy QIDO com o StudyInstanceUID do pedido.
        </p>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            className="flex-1 rounded-md border px-3 py-2 font-mono text-xs"
            placeholder="StudyInstanceUID"
            value={studyInput}
            onChange={(e) => setStudyInput(e.target.value)}
          />
          <button
            type="button"
            disabled={loading}
            className="rounded-md bg-teal-700 px-4 py-2 text-sm text-white disabled:opacity-50"
            onClick={() => void loadStudy()}
          >
            Consultar QIDO
          </button>
        </div>
        {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        {meta && (
          <pre className="max-h-[480px] overflow-auto rounded-xl border border-gray-200 bg-white p-4 text-xs dark:border-gray-800 dark:bg-gray-900">
            {meta}
          </pre>
        )}
      </main>
    </div>
  );
}

export default function RadiologiaViewerPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-sm text-gray-500">Carregando…</div>}>
      <ViewerInner />
    </Suspense>
  );
}
