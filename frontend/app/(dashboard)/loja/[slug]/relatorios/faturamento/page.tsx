'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Download, Search } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';

type Agrupamento = 'profissional' | 'procedimento' | 'local' | 'convenio';

interface LinhaFaturamento {
  nome: string;
  total_atendimentos: number;
  valor_consulta: number;
  valor_procedimento: number;
  valor_total: number;
}

interface FaturamentoData {
  linhas: LinhaFaturamento[];
  totais: {
    total_atendimentos: number;
    valor_consulta: number;
    valor_procedimento: number;
    valor_total: number;
  };
  agrupamento: string;
}

const AGRUPAMENTO_LABELS: Record<Agrupamento, string> = {
  profissional: 'Profissional',
  procedimento: 'Procedimento',
  local: 'Local de Atendimento',
  convenio: 'Convênio',
};

const AGRUPAMENTO_TITULOS: Record<Agrupamento, string> = {
  profissional: 'Faturamento por Profissional',
  procedimento: 'Faturamento por Procedimento',
  local: 'Faturamento por Local de Atendimento',
  convenio: 'Faturamento por Convênio',
};

function parseAgrupamento(raw: string | null): Agrupamento {
  if (raw === 'procedimento' || raw === 'local' || raw === 'convenio' || raw === 'profissional') {
    return raw;
  }
  return 'profissional';
}

export default function FaturamentoPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const slug = params.slug as string;

  const agrupamento = parseAgrupamento(searchParams.get('agrupar'));

  const [dataInicio, setDataInicio] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
  });
  const [dataFim, setDataFim] = useState(() => new Date().toISOString().split('T')[0]);

  const [data, setData] = useState<FaturamentoData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const setAgrupamento = (value: Agrupamento) => {
    const qp = new URLSearchParams(searchParams.toString());
    qp.set('agrupar', value);
    router.replace(`${pathname}?${qp.toString()}`);
  };

  const buscar = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const qp = new URLSearchParams({
        data_inicio: dataInicio,
        data_fim: dataFim,
        agrupar: agrupamento,
      });
      const res = await clinicaBelezaFetch(`/relatorios/faturamento/?${qp.toString()}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError('Erro ao carregar dados. Tente novamente.');
        setData(null);
      }
    } catch {
      setError('Erro ao carregar dados. Tente novamente.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dataInicio, dataFim, agrupamento]);

  useEffect(() => {
    buscar();
  }, [buscar]);

  const formatCurrency = (value: number) =>
    value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const exportarCSV = () => {
    if (!data) return;
    const BOM = '\ufeff';
    const label = AGRUPAMENTO_LABELS[agrupamento];
    let csv = `${label};Atendimentos;Valor Consultas (R$);Valor Procedimentos (R$);Valor Total (R$)\n`;
    for (const linha of data.linhas) {
      csv += `${linha.nome};${linha.total_atendimentos};${linha.valor_consulta.toFixed(2)};${linha.valor_procedimento.toFixed(2)};${linha.valor_total.toFixed(2)}\n`;
    }
    csv += `TOTAL;${data.totais.total_atendimentos};${data.totais.valor_consulta.toFixed(2)};${data.totais.valor_procedimento.toFixed(2)};${data.totais.valor_total.toFixed(2)}\n`;

    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `faturamento_${agrupamento}_${dataInicio}_${dataFim}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const titulo = AGRUPAMENTO_TITULOS[agrupamento];

  const exportActions = (
    <button
      type="button"
      onClick={exportarCSV}
      disabled={!data?.linhas.length}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
    >
      <Download size={16} />
      <span className="hidden sm:inline">Exportar CSV</span>
      <span className="sm:hidden">CSV</span>
    </button>
  );

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={titulo}
        subtitle={`Período: ${dataInicio} a ${dataFim}`}
        backHref={`/loja/${slug}/relatorios`}
        extraActions={exportActions}
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Início
              </label>
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Fim
              </label>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Agrupar por
              </label>
              <select
                value={agrupamento}
                onChange={(e) => setAgrupamento(e.target.value as Agrupamento)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="profissional">Profissional</option>
                <option value="procedimento">Procedimento</option>
                <option value="local">Local de Atendimento</option>
                <option value="convenio">Convênio</option>
              </select>
            </div>
            <button
              onClick={buscar}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 min-h-[40px] text-sm font-medium rounded-lg text-white"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Search size={16} /> Buscar
            </button>
          </div>
        </ClinicaBelezaPanel>

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        {loading && (
          <div className="flex justify-center py-12">
            <div
              className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin"
              style={{ borderColor: `${CLINICA_BELEZA_PRIMARY}30`, borderTopColor: 'transparent' }}
            />
          </div>
        )}

        {!loading && data && (
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
            {data.linhas.length === 0 ? (
              <p className="text-center py-12 text-gray-500">Nenhum dado no período selecionado.</p>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80">
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">
                          {AGRUPAMENTO_LABELS[agrupamento]}
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">
                          Atendimentos
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase hidden sm:table-cell">
                          Consultas
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase hidden sm:table-cell">
                          Procedimentos
                        </th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">
                          Total
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {data.linhas.map((linha, i) => (
                        <tr key={i} className="hover:bg-gray-50/50 dark:hover:bg-gray-750">
                          <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                            {linha.nome || '—'}
                          </td>
                          <td className="px-4 py-3 text-right tabular-nums text-gray-700 dark:text-gray-300">
                            {linha.total_atendimentos}
                          </td>
                          <td className="px-4 py-3 text-right tabular-nums text-gray-700 dark:text-gray-300 hidden sm:table-cell">
                            {formatCurrency(linha.valor_consulta)}
                          </td>
                          <td className="px-4 py-3 text-right tabular-nums text-gray-700 dark:text-gray-300 hidden sm:table-cell">
                            {formatCurrency(linha.valor_procedimento)}
                          </td>
                          <td className="px-4 py-3 text-right tabular-nums font-semibold text-gray-900 dark:text-white">
                            {formatCurrency(linha.valor_total)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr
                        className="border-t-2 border-gray-200 dark:border-gray-600 font-bold"
                        style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}08` }}
                      >
                        <td className="px-4 py-3 text-gray-900 dark:text-white">Total</td>
                        <td className="px-4 py-3 text-right tabular-nums text-gray-900 dark:text-white">
                          {data.totais.total_atendimentos}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-gray-900 dark:text-white hidden sm:table-cell">
                          {formatCurrency(data.totais.valor_consulta)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-gray-900 dark:text-white hidden sm:table-cell">
                          {formatCurrency(data.totais.valor_procedimento)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-lg" style={{ color: CLINICA_BELEZA_PRIMARY }}>
                          {formatCurrency(data.totais.valor_total)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                {/* Cards resumo mobile */}
                <div className="sm:hidden p-4 border-t border-gray-200 dark:border-gray-700 grid grid-cols-2 gap-3">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 uppercase">Consultas</p>
                    <p className="text-base font-bold tabular-nums text-gray-900 dark:text-white">
                      {formatCurrency(data.totais.valor_consulta)}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500 uppercase">Procedimentos</p>
                    <p className="text-base font-bold tabular-nums text-gray-900 dark:text-white">
                      {formatCurrency(data.totais.valor_procedimento)}
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
