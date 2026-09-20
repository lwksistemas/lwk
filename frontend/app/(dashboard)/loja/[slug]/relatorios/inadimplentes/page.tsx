'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Download, RefreshCw } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { RelatorioPdfActions } from '@/components/clinica-beleza/relatorios-shared/RelatorioPdfActions';
import { abrirRelatorioPdf } from '@/components/clinica-beleza/relatorios-shared/abrir-relatorio-pdf';

interface InadimplenteItem {
  payment_id: number;
  patient_id: number | null;
  paciente_nome: string;
  telefone: string;
  email: string;
  valor_aberto: number;
  vencimento: string | null;
  dias_atraso: number;
  status: string;
}

interface InadimplentesData {
  linhas: InadimplenteItem[];
  totais: { total_inadimplentes: number; valor_total: number };
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

export default function InadimplentesRelatorioPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [data, setData] = useState<InadimplentesData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const buscar = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await clinicaBelezaFetch('/relatorios/inadimplentes/');
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
  }, []);

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const exportarCSV = () => {
    if (!data) return;
    const BOM = '\ufeff';
    let csv = 'Paciente;Telefone;E-mail;Vencimento;Dias em atraso;Valor em aberto (R$)\n';
    for (const l of data.linhas) {
      csv +=
        `${l.paciente_nome};${l.telefone};${l.email};${formatDate(l.vencimento)};` +
        `${l.dias_atraso};${l.valor_aberto.toFixed(2)}\n`;
    }
    csv += `TOTAL;;;;${data.totais.total_inadimplentes} inadimplentes;${data.totais.valor_total.toFixed(2)}\n`;
    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'inadimplentes.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const abrirPdf = (modo: 'visualizar' | 'imprimir', janela: Window | null) =>
    abrirRelatorioPdf('/relatorios/inadimplentes/pdf/', modo, janela);

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Inadimplentes"
        subtitle="Pagamentos a prazo vencidos e em aberto"
        backHref={`/loja/${slug}/relatorios`}
        extraActions={
          <>
            <button
              type="button"
              onClick={() => void buscar()}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">Atualizar</span>
            </button>
            <button
              type="button"
              onClick={exportarCSV}
              disabled={!data?.linhas.length}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
            >
              <Download size={16} />
              <span className="hidden sm:inline">CSV</span>
            </button>
            <RelatorioPdfActions disabled={!data?.linhas.length} onPdf={abrirPdf} />
          </>
        }
      />
      <ClinicaBelezaPageContent>
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
              <span><strong>{data.totais.total_inadimplentes}</strong> inadimplente{data.totais.total_inadimplentes === 1 ? '' : 's'}</span>
              <span>Total em aberto {formatCurrency(data.totais.valor_total)}</span>
            </div>

            {data.linhas.length === 0 ? (
              <p className="text-center py-12 text-gray-500 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                Nenhum pagamento vencido em aberto. 🎉
              </p>
            ) : (
              <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-xs uppercase text-gray-500 bg-gray-50 dark:bg-gray-800/80">
                        <th className="text-left px-4 py-2">Paciente</th>
                        <th className="text-left px-4 py-2">Telefone</th>
                        <th className="text-left px-4 py-2">Vencimento</th>
                        <th className="text-right px-4 py-2">Atraso</th>
                        <th className="text-right px-4 py-2">Valor em aberto</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                      {data.linhas.map((l) => (
                        <tr key={l.payment_id}>
                          <td className="px-4 py-2 font-medium text-gray-900 dark:text-white">{l.paciente_nome || '—'}</td>
                          <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{l.telefone || '—'}</td>
                          <td className="px-4 py-2 whitespace-nowrap text-gray-600">{formatDate(l.vencimento)}</td>
                          <td className="px-4 py-2 text-right tabular-nums text-red-700 dark:text-red-400">
                            {l.dias_atraso} dia(s)
                          </td>
                          <td className="px-4 py-2 text-right tabular-nums font-medium">{formatCurrency(l.valor_aberto)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}
          </div>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
