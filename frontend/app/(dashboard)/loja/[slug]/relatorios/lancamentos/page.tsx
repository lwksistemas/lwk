'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Download, Search } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { CLINICA_FORMA_PAGAMENTO_LABEL } from '@/lib/clinica-beleza-constants';
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { RelatorioPdfActions } from '@/components/clinica-beleza/relatorios-shared/RelatorioPdfActions';
import { abrirRelatorioPdf } from '@/components/clinica-beleza/relatorios-shared/abrir-relatorio-pdf';

interface LancamentoItem {
  payment_id: number;
  data: string | null;
  paciente: string;
  procedimentos: string;
  convenio: string;
  forma_pagamento: string;
  forma_pagamento_label: string;
  status: string;
  valor: number;
  comissao: number;
}

interface ProfissionalLancamentos {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  valor_total: number;
  comissao_total: number;
  lancamentos: LancamentoItem[];
}

interface LancamentosData {
  profissionais: ProfissionalLancamentos[];
  totais: {
    total_atendimentos: number;
    valor_total: number;
    comissao_total: number;
  };
}

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatDate(iso: string | null) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

export default function LancamentosRelatorioPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [dataInicio, setDataInicio] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
  });
  const [dataFim, setDataFim] = useState(() => new Date().toISOString().split('T')[0]);
  const [forma, setForma] = useState('');
  const [data, setData] = useState<LancamentosData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const buscar = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (forma) qp.set('forma', forma);
      const res = await clinicaBelezaFetch(`/relatorios/lancamentos/?${qp.toString()}`);
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
  }, [dataInicio, dataFim, forma]);

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const exportarCSV = () => {
    if (!data) return;
    const BOM = '\ufeff';
    let csv = 'Profissional;Data;Paciente;Procedimentos;Convênio;Forma;Valor (R$);Comissão (R$)\n';
    for (const p of data.profissionais) {
      for (const l of p.lancamentos) {
        csv +=
          `${p.nome};${formatDate(l.data)};${l.paciente};${l.procedimentos};${l.convenio};` +
          `${l.forma_pagamento_label};${l.valor.toFixed(2)};${l.comissao.toFixed(2)}\n`;
      }
      csv += `${p.nome};TOTAL;;;;;${p.valor_total.toFixed(2)};${p.comissao_total.toFixed(2)}\n`;
    }
    csv += `TOTAL GERAL;${data.totais.total_atendimentos} atendimentos;;;;;${data.totais.valor_total.toFixed(2)};${data.totais.comissao_total.toFixed(2)}\n`;
    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `lancamentos_${dataInicio}_${dataFim}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const abrirPdf = (modo: 'visualizar' | 'imprimir', janela: Window | null) => {
    const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
    if (forma) qp.set('forma', forma);
    return abrirRelatorioPdf(`/relatorios/lancamentos/pdf/?${qp.toString()}`, modo, janela);
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Lançamentos por profissional"
        subtitle={`Período: ${dataInicio} a ${dataFim}`}
        backHref={`/loja/${slug}/relatorios`}
        extraActions={
          <>
            <button
              type="button"
              onClick={exportarCSV}
              disabled={!data?.profissionais.length}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
            >
              <Download size={16} />
              <span className="hidden sm:inline">CSV</span>
            </button>
            <RelatorioPdfActions
              disabled={!data?.profissionais.length}
              onPdf={abrirPdf}
            />
          </>
        }
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Data início</label>
              <input
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Data fim</label>
              <input
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Forma de pagamento</label>
              <select
                value={forma}
                onChange={(e) => setForma(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="">Todas</option>
                {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <button
              type="button"
              onClick={() => void buscar()}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 min-h-[40px] text-sm font-medium rounded-lg text-white"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
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
              style={{ borderColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 19%, transparent)', borderTopColor: 'transparent' }}
            />
          </div>
        )}

        {!loading && data && (
          <div className="space-y-4">
            <div
              className="rounded-xl border border-gray-200 dark:border-gray-700 px-4 py-3 flex flex-wrap gap-x-6 gap-y-1 text-sm"
              style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 4%, transparent)' }}
            >
              <span><strong>{data.totais.total_atendimentos}</strong> atendimentos</span>
              <span>Total {formatCurrency(data.totais.valor_total)}</span>
              <span>Comissão {formatCurrency(data.totais.comissao_total)}</span>
            </div>

            {data.profissionais.length === 0 ? (
              <p className="text-center py-12 text-gray-500 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                Nenhum lançamento no período.
              </p>
            ) : (
              data.profissionais.map((p) => (
                <section key={p.professional_id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="font-semibold text-gray-900 dark:text-white">{p.nome}</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {p.total_atendimentos} paciente{p.total_atendimentos === 1 ? '' : 's'} · {formatCurrency(p.valor_total)}
                    </p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs uppercase text-gray-500 bg-gray-50 dark:bg-gray-800/80">
                          <th className="text-left px-4 py-2">Data</th>
                          <th className="text-left px-4 py-2">Paciente</th>
                          <th className="text-left px-4 py-2">Procedimentos</th>
                          <th className="text-left px-4 py-2">Convênio</th>
                          <th className="text-left px-4 py-2">Forma</th>
                          <th className="text-right px-4 py-2">Valor</th>
                          <th className="text-right px-4 py-2">Comissão</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {p.lancamentos.map((l) => (
                          <tr key={l.payment_id}>
                            <td className="px-4 py-2 whitespace-nowrap text-gray-600">{formatDate(l.data)}</td>
                            <td className="px-4 py-2 font-medium text-gray-900 dark:text-white">{l.paciente}</td>
                            <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{l.procedimentos}</td>
                            <td className="px-4 py-2">{l.convenio}</td>
                            <td className="px-4 py-2">{l.forma_pagamento_label}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(l.valor)}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(l.comissao)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              ))
            )}
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
