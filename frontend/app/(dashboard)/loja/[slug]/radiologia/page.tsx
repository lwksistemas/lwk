'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Activity,
  ClipboardList,
  FileText,
  Monitor,
  Stethoscope,
  Users,
} from 'lucide-react';
import { radiologiaHealth } from '@/lib/radiologia-api';

function CardLink({
  href,
  title,
  description,
  icon,
}: {
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="block rounded-xl border border-teal-200/60 bg-white p-5 shadow-sm transition hover:border-teal-500/40 hover:shadow-md dark:border-gray-800 dark:bg-gray-900 sm:p-6 active:scale-[0.98]"
    >
      <div className="flex items-start gap-3 sm:gap-4">
        <div className="shrink-0 rounded-lg bg-teal-100 p-2 text-teal-800 dark:bg-teal-900/40 dark:text-teal-200 sm:p-2.5">
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 sm:text-lg">{title}</h2>
          <p className="mt-1 text-xs text-gray-600 dark:text-gray-400 sm:text-sm">{description}</p>
        </div>
      </div>
    </Link>
  );
}

export default function RadiologiaHomePage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const [health, setHealth] = useState<{ orthanc_ok: boolean; orthanc_url: string } | null>(null);

  useEffect(() => {
    radiologiaHealth()
      .then((h) => setHealth({ orthanc_ok: h.orthanc_ok, orthanc_url: h.orthanc_url }))
      .catch(() => setHealth({ orthanc_ok: false, orthanc_url: '' }));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      <nav className="bg-gradient-to-r from-teal-700 to-teal-900 text-white shadow-lg">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex min-h-[64px] flex-col items-start justify-between gap-2 py-3 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-xl font-bold sm:text-2xl">Radiologia</h1>
              <p className="text-xs text-white/80 sm:text-sm">RIS · Worklist · Laudos</p>
            </div>
            <button
              type="button"
              onClick={() => router.push(`/loja/${slug}/dashboard`)}
              className="rounded-md bg-white/15 px-3 py-2 text-sm transition-colors hover:bg-white/25 active:scale-95 sm:px-4"
            >
              Voltar ao Dashboard
            </button>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
        {health && (
          <div
            className={`mb-4 rounded-lg border px-4 py-3 text-sm ${
              health.orthanc_ok
                ? 'border-teal-200 bg-teal-50 text-teal-900 dark:border-teal-800 dark:bg-teal-950/40 dark:text-teal-100'
                : 'border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100'
            }`}
          >
            PACS Orthanc: {health.orthanc_ok ? 'online' : 'indisponível'}
            {health.orthanc_url ? ` · ${health.orthanc_url}` : ''}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-6">
          <CardLink
            href={`/loja/${slug}/radiologia/pedidos`}
            title="Pedidos / Worklist"
            description="Criar pedido, Accession, publicar MWL e acompanhar status."
            icon={<ClipboardList className="h-5 w-5 sm:h-6 sm:w-6" />}
          />
          <CardLink
            href={`/loja/${slug}/radiologia/pacientes`}
            title="Pacientes"
            description="Cadastro de pacientes do fluxo de exames."
            icon={<Users className="h-5 w-5 sm:h-6 sm:w-6" />}
          />
          <CardLink
            href={`/loja/${slug}/radiologia/procedimentos`}
            title="Procedimentos"
            description="Catálogo de exames e templates de laudo."
            icon={<Stethoscope className="h-5 w-5 sm:h-6 sm:w-6" />}
          />
          <CardLink
            href={`/loja/${slug}/radiologia/equipamentos`}
            title="Equipamentos"
            description="Aparelhos liberados pelo Super Admin — escolha no exame e pareie o DICOM."
            icon={<Monitor className="h-5 w-5 sm:h-6 sm:w-6" />}
          />
          <CardLink
            href={`/loja/${slug}/radiologia/laudos`}
            title="Laudos"
            description="Laudo estruturado e PDF (ICP-Brasil na Fase 1)."
            icon={<FileText className="h-5 w-5 sm:h-6 sm:w-6" />}
          />
          <CardLink
            href={`/loja/${slug}/radiologia/viewer`}
            title="Viewer"
            description="OHIF via proxy DICOMweb LWK (nunca direto no Orthanc)."
            icon={<Activity className="h-5 w-5 sm:h-6 sm:w-6" />}
          />
        </div>
      </main>
    </div>
  );
}
