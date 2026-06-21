'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  BarChart3,
  Building2,
  ChevronRight,
  ClipboardList,
  DollarSign,
  FileText,
  Heart,
  MapPin,
  User,
} from 'lucide-react';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';

interface RelatorioItem {
  titulo: string;
  descricao: string;
  href: string;
  icon: React.ElementType;
}

interface CategoriaRelatorio {
  id: string;
  titulo: string;
  descricao: string;
  icon: React.ElementType;
  relatorios: RelatorioItem[];
}

const CATEGORIAS: CategoriaRelatorio[] = [
  {
    id: 'comissoes',
    titulo: 'Comissões',
    descricao: 'Relatórios de comissão por diferentes agrupamentos',
    icon: DollarSign,
    relatorios: [
      {
        titulo: 'Comissão por Profissional',
        descricao: 'Resumo consolidado de comissões por profissional no período',
        href: 'comissoes',
        icon: User,
      },
      {
        titulo: 'Comissão por Procedimento',
        descricao: 'Comissões agrupadas por tipo de procedimento realizado',
        href: 'comissoes?agrupar=procedimento',
        icon: ClipboardList,
      },
      {
        titulo: 'Comissão por Local de Atendimento',
        descricao: 'Comissões separadas por sala ou local',
        href: 'comissoes?agrupar=local',
        icon: MapPin,
      },
      {
        titulo: 'Comissão por Convênio',
        descricao: 'Comissões agrupadas por convênio do paciente',
        href: 'comissoes?agrupar=convenio',
        icon: Heart,
      },
      {
        titulo: 'Repasse por Consulta',
        descricao: 'Documento detalhado por atendimento para repasse ao profissional',
        href: 'repasse-consultas',
        icon: FileText,
      },
    ],
  },
  {
    id: 'faturamento',
    titulo: 'Faturamento',
    descricao: 'Relatórios de receita e faturamento da clínica',
    icon: BarChart3,
    relatorios: [
      {
        titulo: 'Faturamento por Profissional',
        descricao: 'Receita total da clínica agrupada por profissional',
        href: 'faturamento?agrupar=profissional',
        icon: User,
      },
      {
        titulo: 'Faturamento por Procedimento',
        descricao: 'Receita agrupada por tipo de procedimento',
        href: 'faturamento?agrupar=procedimento',
        icon: ClipboardList,
      },
      {
        titulo: 'Faturamento por Local',
        descricao: 'Receita separada por local de atendimento',
        href: 'faturamento?agrupar=local',
        icon: MapPin,
      },
      {
        titulo: 'Faturamento por Convênio',
        descricao: 'Receita agrupada por convênio (Particular, Unimed, etc.)',
        href: 'faturamento?agrupar=convenio',
        icon: Building2,
      },
    ],
  },
];

export default function RelatoriosHubPage() {
  const params = useParams();
  const slug = params.slug as string;

  return (
    <div className="p-4 sm:p-6 h-full">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Relatórios</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Selecione o tipo de relatório que deseja visualizar
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100%-5rem)]">
        {CATEGORIAS.map((cat) => {
          const CatIcon = cat.icon;
          return (
            <section key={cat.id} className="flex flex-col min-h-0">
              <div className="flex items-center gap-3 mb-3 px-1">
                <span
                  className="flex w-10 h-10 items-center justify-center rounded-xl shrink-0"
                  style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}15` }}
                >
                  <CatIcon size={20} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                </span>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {cat.titulo}
                  </h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{cat.descricao}</p>
                </div>
              </div>

              <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700 overflow-hidden shadow-sm">
                {cat.relatorios.map((rel) => {
                  const Icon = rel.icon;
                  return (
                    <Link
                      key={rel.href}
                      href={`/loja/${slug}/relatorios/${rel.href}`}
                      className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-gray-50 dark:hover:bg-gray-750"
                    >
                      <span
                        className="flex w-9 h-9 items-center justify-center rounded-lg shrink-0"
                        style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}10` }}
                      >
                        <Icon size={16} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                      </span>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {rel.titulo}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                          {rel.descricao}
                        </p>
                      </div>
                      <ChevronRight size={16} className="text-gray-400 shrink-0" />
                    </Link>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
