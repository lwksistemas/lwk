'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { Download, Printer, Search } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';

interface ProfissionalComissao {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  valor_total: number;
  comissao_percentual: number;
  comissao_total: number;
}

interface RelatorioData {
  profissionais: ProfissionalComissao[];
  totais: {
    total_atendimentos: number;
    valor_total: number;
    comissao_total: number;
  };
}

interface ProfessionalOption {
  id: number;
  nome: string;
}

// Estilos para impressão
if (typeof window !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @media print {
      body * { visibility: hidden; }
      .print-area, .print-area * { visibility: visible; }
      .print-area { position: absolute; left: 0; top: 0; width: 100%; }
      .no-print { display: none !important; }
      nav, aside, header { display: none !important; }
    }
  `;
  document.head.appendChild(style);
}

export default function RelatorioComissoesPage() {
  const params = useParams();
  const slug = params.slug as string;

  // Filtros com padrão = mês atual
  const [dataInicio, setDataInicio] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
  });
  const [dataFim, setDataFim] = useState(() => new Date().toISOString().split('T')[0]);
  const [professionalId, setProfessionalId] = useState<string>('');

  const [data, setData] = useState<RelatorioData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [professionals, setProfessionals] = useState<ProfessionalOption[]>([]);

  // Carregar lista de profissionais para o filtro
  useEffect(() => {
    clinicaBelezaFetch('/professionals/')
      .then(async (res) => {
        if (res.ok) {
          const json = await res.json();
          setProfessionals(json.results || json);
        }
      })
      .catch(() => {});
  }, []);

  const buscar = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set('professional_id', professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/comissoes/?${qp.toString()}`);
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
  }, [dataInicio, dataFim, professionalId]);

  useEffect(() => { buscar(); }, [buscar]);

  const formatCurrency = (value: number) =>
    value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const exportarCSV = () => {
    if (!data) return;
    const BOM = '\ufeff';
    let csv = 'Profissional;Atendimentos;Valor Total (R$);Comissão (%);Comissão (R$)\n';
    for (const p of data.profissionais) {
      csv += `${p.nome};${p.total_atendimentos};${p.valor_total.toFixed(2)};${p.comissao_percentual};${p.comissao_total.toFixed(2)}\n`;
    }
    csv += `TOTAIS;${data.totais.total_atendimentos};${data.totais.valor_total.toFixed(2)};;${data.totais.comissao_total.toFixed(2)}\n`;

    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `comissoes_${dataInicio}_${dataFim}.csv`;
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };

  const exportarPDF = () => { window.print(); };

  return (
    <div className="p-4 sm:p-6 print-area">
      {/* Cabeçalho para impressão */}
      <div className="hidden print:block mb-6">
        <h1 className="text-2xl font-bold" style={{ color: CLINICA_BELEZA_PRIMARY }}>
          Relatório de Comissões
        </h1>
        <p className="text-sm text-gray-600">Período: {dataInicio} a {dataFim}</p>
        <hr className="my-4 border-gray-300" />
      </div>

      {/* Título e ações */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6 no-print">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Comissões dos Profissionais</h1>
        <div className="flex gap-2">
          <button
            onClick={exportarCSV}
            disabled={!data || data.profissionais.length === 0}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={16} /> CSV
          </button>
          <button
            onClick={exportarPDF}
            disabled={!data || data.profissionais.length === 0}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            <Printer size={16} /> PDF
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700 mb-6 no-print">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Data Início
            </label>
            <input
              type="date"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full px-3 py-2 min-h-[40px] text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-opacity-50 [color-scheme:light] dark:[color-scheme:dark]"
              style={{ focusRingColor: CLINICA_BELEZA_PRIMARY } as never}
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
              className="w-full px-3 py-2 min-h-[40px] text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-opacity-50 [color-scheme:light] dark:[color-scheme:dark]"
              style={{ focusRingColor: CLINICA_BELEZA_PRIMARY } as never}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Profissional
            </label>
            <select
              value={professionalId}
              onChange={(e) => setProfessionalId(e.target.value)}
              className="w-full px-3 py-2 min-h-[40px] text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-opacity-50 [color-scheme:light] dark:[color-scheme:dark]"
            >
              <option value="">Todos</option>
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>{p.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <button
              onClick={buscar}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 min-h-[40px] text-sm font-medium rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Search size={16} /> Buscar
            </button>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg mb-6 text-sm">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div
            className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin"
            style={{ borderColor: `${CLINICA_BELEZA_PRIMARY} transparent transparent transparent` }}
          />
        </div>
      )}

      {/* Tabela */}
      {!loading && data && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 overflow-hidden">
          {data.profissionais.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <p className="text-base">Nenhum dado encontrado para o período selecionado.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700" style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}10` }}>
                    <th className="text-left px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Profissional</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Atendimentos</th>
                    <th className="text-right px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Valor Total (R$)</th>
                    <th className="text-center px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Comissão (%)</th>
                    <th className="text-right px-4 py-3 font-semibold text-gray-700 dark:text-gray-200">Comissão (R$)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.profissionais.map((p) => (
                    <tr key={p.professional_id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <td className="px-4 py-3 text-gray-900 dark:text-white font-medium">{p.nome}</td>
                      <td className="px-4 py-3 text-center text-gray-700 dark:text-gray-300">{p.total_atendimentos}</td>
                      <td className="px-4 py-3 text-right text-gray-700 dark:text-gray-300">{formatCurrency(p.valor_total)}</td>
                      <td className="px-4 py-3 text-center text-gray-700 dark:text-gray-300">{p.comissao_percentual}%</td>
                      <td className="px-4 py-3 text-right font-semibold" style={{ color: CLINICA_BELEZA_PRIMARY }}>{formatCurrency(p.comissao_total)}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-300 dark:border-gray-600 font-bold" style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}08` }}>
                    <td className="px-4 py-3 text-gray-900 dark:text-white">TOTAIS</td>
                    <td className="px-4 py-3 text-center text-gray-900 dark:text-white">{data.totais.total_atendimentos}</td>
                    <td className="px-4 py-3 text-right text-gray-900 dark:text-white">{formatCurrency(data.totais.valor_total)}</td>
                    <td className="px-4 py-3 text-center text-gray-500">—</td>
                    <td className="px-4 py-3 text-right" style={{ color: CLINICA_BELEZA_PRIMARY }}>{formatCurrency(data.totais.comissao_total)}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
