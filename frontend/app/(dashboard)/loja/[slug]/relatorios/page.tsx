'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { BarChart3, FileText } from 'lucide-react';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';

const RELATORIOS = [
  {
    titulo: 'Comissões dos Profissionais',
    descricao: 'Resumo consolidado por profissional — consultas e procedimentos no período.',
    href: 'comissoes',
    icon: BarChart3,
  },
  {
    titulo: 'Repasse por Consulta',
    descricao: 'Cada atendimento com consulta e procedimentos — documento para o profissional receber da clínica.',
    href: 'repasse-consultas',
    icon: FileText,
  },
];

export default function RelatoriosHubPage() {
  const params = useParams();
  const slug = params.slug as string;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Relatórios</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {RELATORIOS.map((rel) => (
          <Link
            key={rel.href}
            href={`/loja/${slug}/relatorios/${rel.href}`}
            className="block p-6 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
          >
            <rel.icon className="w-8 h-8 mb-3" style={{ color: CLINICA_BELEZA_PRIMARY }} />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{rel.titulo}</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{rel.descricao}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
