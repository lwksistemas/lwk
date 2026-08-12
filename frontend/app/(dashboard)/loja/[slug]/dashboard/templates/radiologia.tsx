'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Activity, ClipboardList, FileText, Monitor, Stethoscope, Users } from 'lucide-react';

type LojaInfo = {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
};

function QuickLink({
  title,
  description,
  href,
  icon: Icon,
  accent,
}: {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  accent: string;
}) {
  return (
    <Link
      href={href}
      className="group block rounded-2xl border border-gray-200/80 bg-white p-5 shadow-sm transition hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-11 w-11 items-center justify-center rounded-xl"
          style={{ backgroundColor: `${accent}18`, color: accent }}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
        </div>
      </div>
    </Link>
  );
}

export default function DashboardRadiologia({ loja }: { loja: LojaInfo }) {
  const params = useParams();
  // Usar slug da URL (atalho "radio"), não loja.slug (CPF/hash) — senão os links quebram a sessão.
  const routeSlug = (typeof params?.slug === 'string' ? params.slug : '') || loja.slug;
  const accent = loja.cor_primaria || '#0F766E';
  const base = `/loja/${routeSlug}/radiologia`;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold" style={{ color: accent }}>
          {loja.nome}
        </h2>
        <p className="text-sm text-gray-500">RIS Radiologia — pedidos, worklist DICOM e laudos</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <QuickLink href={`${base}/pedidos`} title="Pedidos / MWL" description="Accession, Study UID e worklist" icon={ClipboardList} accent={accent} />
        <QuickLink href={`${base}/pacientes`} title="Pacientes" description="Cadastro do fluxo de exames" icon={Users} accent={accent} />
        <QuickLink href={`${base}/procedimentos`} title="Procedimentos" description="Catálogo e template de laudo" icon={Stethoscope} accent={accent} />
        <QuickLink href={`${base}/equipamentos`} title="Equipamentos" description="Máquinas liberadas — pareamento DICOM" icon={Monitor} accent={accent} />
        <QuickLink href={`${base}/laudos`} title="Laudos" description="Laudo estruturado e PDF" icon={FileText} accent={accent} />
        <QuickLink href={`${base}/viewer`} title="Viewer" description="Proxy DICOMweb + OHIF" icon={Activity} accent={accent} />
      </div>
      <Link
        href={base}
        className="inline-flex rounded-lg px-4 py-2 text-sm font-medium text-white"
        style={{ backgroundColor: accent }}
      >
        Abrir módulo Radiologia
      </Link>
    </div>
  );
}
