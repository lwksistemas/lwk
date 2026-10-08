'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  AlertTriangle,
  BarChart3,
  ChevronRight,
  ClipboardList,
  Clock,
  DollarSign,
  FileText,
  Percent,
  User,
} from 'lucide-react';

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
    descricao: 'Comissão do período e o documento de repasse',
    icon: DollarSign,
    relatorios: [
      {
        titulo: 'Comissão',
        descricao: 'Por profissional, por cliente, local ou convênio. O agrupamento fica na própria tela.',
        href: 'comissoes',
        icon: User,
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
    descricao: 'Receita do período, lançamentos, descontos, venda a prazo e inadimplência',
    icon: BarChart3,
    relatorios: [
      {
        titulo: 'Faturamento',
        descricao: 'Por profissional, procedimento, local ou convênio. O agrupamento fica na própria tela.',
        href: 'faturamento',
        icon: BarChart3,
      },
      {
        titulo: 'Lançamentos por profissional',
        descricao: 'Total por profissional com o nome de cada paciente lançado no financeiro',
        href: 'lancamentos',
        icon: ClipboardList,
      },
      {
        titulo: 'Descontos concedidos',
        descricao: 'Total de descontos por profissional, com o nome de cada cliente',
        href: 'descontos',
        icon: Percent,
      },
      {
        titulo: 'Venda a prazo',
        descricao: 'Por profissional ou por cliente, com cada consulta e o saldo em aberto',
        href: 'venda-prazo',
        icon: Clock,
      },
      {
        titulo: 'Inadimplentes',
        descricao: 'Pagamentos a prazo vencidos e em aberto, com valor e dias de atraso',
        href: 'inadimplentes',
        icon: AlertTriangle,
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {CATEGORIAS.map((cat) => {
          const CatIcon = cat.icon;
          return (
            <section key={cat.id} className="flex flex-col min-h-0">
              <div className="flex items-center gap-3 mb-3 px-1">
                <span
                  className="flex w-10 h-10 items-center justify-center rounded-xl shrink-0"
                  style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 8%, transparent)' }}
                >
                  <CatIcon size={20} style={{ color: 'var(--cb-primary, #8B3D52)' }} />
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
                      key={rel.titulo}
                      href={`/loja/${slug}/relatorios/${rel.href}`}
                      className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-gray-50 dark:hover:bg-gray-750"
                    >
                      <span
                        className="flex w-9 h-9 items-center justify-center rounded-lg shrink-0"
                        style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 6%, transparent)' }}
                      >
                        <Icon size={16} style={{ color: 'var(--cb-primary, #8B3D52)' }} />
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
