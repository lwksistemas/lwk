'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Download, Search } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { RelatorioPdfActions } from '@/components/clinica-beleza/relatorios-shared/RelatorioPdfActions';
import { abrirRelatorioPdf } from '@/components/clinica-beleza/relatorios-shared/abrir-relatorio-pdf';
import { formatCurrency } from '@/lib/financeiro-helpers';

interface VendaPrazoItem {
  payment_id: number;
  data: string | null;
  patient_id?: number;
  paciente: string;
  telefone: string;
  profissional?: string;
  consulta_numero?: number | null;
  procedimentos: string;
  vencimento: string | null;
  situacao: string;
  situacao_label: string;
  dias_atraso: number;
  valor: number;
  valor_pago: number;
  valor_aberto: number;
}

interface ProfissionalVendaPrazo {
  professional_id: number;
  nome: string;
  total_vendas: number;
  valor_total: number;
  valor_pago: number;
  valor_aberto: number;
  vendas: VendaPrazoItem[];
}

interface ClienteVendaPrazo {
  patient_id: number;
  nome: string;
  telefone: string;
  total_consultas: number;
  valor_total: number;
  valor_pago: number;
  valor_aberto: number;
  consultas: VendaPrazoItem[];
}

interface VendaPrazoData {
  profissionais: ProfissionalVendaPrazo[];
  clientes?: ClienteVendaPrazo[];
  totais: {
    total_vendas: number;
    valor_total: number;
    valor_pago: number;
    valor_aberto: number;
  };
}

interface ProfessionalOption {
  id: number;
  nome: string;
  is_profissional?: boolean;
}

function formatDate(iso: string | null) {
  if (!iso) return '—';
  const [y, m, d] = iso.split('-');
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

function situacaoClass(codigo: string) {
  if (codigo === 'vencido') return 'text-red-700 dark:text-red-400';
  if (codigo === 'em_dia') return 'text-emerald-700 dark:text-emerald-400';
  return 'text-amber-700 dark:text-amber-400';
}

export default function VendaPrazoRelatorioPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [dataInicio, setDataInicio] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
  });
  const [dataFim, setDataFim] = useState(() => new Date().toISOString().split('T')[0]);
  const [professionalId, setProfessionalId] = useState('');
  const [agrupar, setAgrupar] = useState<'profissional' | 'cliente'>('profissional');
  const [professionals, setProfessionals] = useState<ProfessionalOption[]>([]);
  const [data, setData] = useState<VendaPrazoData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    clinicaBelezaFetch('/professionals/')
      .then(async (res) => {
        if (!res.ok) return;
        const json = await res.json();
        const list: ProfessionalOption[] = json.results || json;
        setProfessionals(list.filter((p) => p.is_profissional !== false));
      })
      .catch(() => {});
  }, []);

  const buscar = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set('professional_id', professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/venda-prazo/?${qp.toString()}`);
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

  useEffect(() => {
    void buscar();
  }, [buscar]);

  const exportarCSV = () => {
    if (!data) return;
    const BOM = '\ufeff';
    const porCliente = agrupar === 'cliente';
    let csv = porCliente
      ? 'Cliente;Telefone;Data;Consulta;Profissional;Procedimentos;Vencimento;Situação;Valor (R$);Recebido (R$);Em aberto (R$)\n'
      : 'Profissional;Data;Paciente;Telefone;Procedimentos;Vencimento;Situação;Valor (R$);Recebido (R$);Em aberto (R$)\n';
    if (porCliente) {
      for (const c of data.clientes || []) {
        for (const v of c.consultas) {
          csv +=
            `${c.nome};${c.telefone};${formatDate(v.data)};${v.consulta_numero ? `nº ${v.consulta_numero}` : ''};` +
            `${v.profissional || ''};${v.procedimentos};${formatDate(v.vencimento)};${v.situacao_label};` +
            `${v.valor.toFixed(2)};${v.valor_pago.toFixed(2)};${v.valor_aberto.toFixed(2)}\n`;
        }
        csv +=
          `${c.nome};TOTAL;;;;;;;;${c.valor_total.toFixed(2)};${c.valor_pago.toFixed(2)};${c.valor_aberto.toFixed(2)}\n`;
      }
    } else {
      for (const p of data.profissionais) {
        for (const v of p.vendas) {
          csv +=
            `${p.nome};${formatDate(v.data)};${v.paciente};${v.telefone};${v.procedimentos};` +
            `${formatDate(v.vencimento)};${v.situacao_label};${v.valor.toFixed(2)};` +
            `${v.valor_pago.toFixed(2)};${v.valor_aberto.toFixed(2)}\n`;
        }
        csv +=
          `${p.nome};TOTAL;;;;;${p.valor_total.toFixed(2)};${p.valor_pago.toFixed(2)};${p.valor_aberto.toFixed(2)}\n`;
      }
    }
    csv +=
      `TOTAL GERAL;${data.totais.total_vendas} vendas;;;;;` +
      `;${data.totais.valor_total.toFixed(2)};${data.totais.valor_pago.toFixed(2)};${data.totais.valor_aberto.toFixed(2)}\n`;
    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `venda_prazo_${dataInicio}_${dataFim}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const abrirPdf = (modo: 'visualizar' | 'imprimir', janela: Window | null) => {
    const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim, agrupar });
    if (professionalId) qp.set('professional_id', professionalId);
    return abrirRelatorioPdf(`/relatorios/venda-prazo/pdf/?${qp.toString()}`, modo, janela);
  };

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Venda a prazo"
        subtitle={`Período: ${dataInicio} a ${dataFim}`}
        backHref={`/loja/${slug}/relatorios`}
        extraActions={
          <>
            <button
              type="button"
              onClick={exportarCSV}
              disabled={!data || (agrupar === 'cliente' ? !(data.clientes || []).length : !data.profissionais.length)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
            >
              <Download size={16} />
              <span className="hidden sm:inline">CSV</span>
            </button>
            <RelatorioPdfActions
              disabled={!data || (agrupar === 'cliente' ? !(data.clientes || []).length : !data.profissionais.length)}
              onPdf={abrirPdf}
            />
          </>
        }
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
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
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Agrupar por</label>
              <select
                value={agrupar}
                onChange={(e) => setAgrupar(e.target.value as 'profissional' | 'cliente')}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="profissional">Profissional</option>
                <option value="cliente">Cliente — consultas</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional</label>
              <select
                value={professionalId}
                onChange={(e) => setProfessionalId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="">Todos</option>
                {professionals.map((p) => (
                  <option key={p.id} value={p.id}>{p.nome}</option>
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
              <span><strong>{data.totais.total_vendas}</strong> venda{data.totais.total_vendas === 1 ? '' : 's'}</span>
              <span>Total {formatCurrency(data.totais.valor_total)}</span>
              <span>Recebido {formatCurrency(data.totais.valor_pago)}</span>
              <span>Em aberto {formatCurrency(data.totais.valor_aberto)}</span>
            </div>

            {(agrupar === 'cliente' ? (data.clientes || []).length : data.profissionais.length) === 0 ? (
              <p className="text-center py-12 text-gray-500 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                Nenhuma venda a prazo no período.
              </p>
            ) : agrupar === 'cliente' ? (
              (data.clientes || []).map((c) => (
                <section key={c.patient_id || c.nome} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="font-semibold text-gray-900 dark:text-white">
                      {c.nome}
                      {c.telefone ? (
                        <span className="ml-2 text-sm font-normal text-gray-500">{c.telefone}</span>
                      ) : null}
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {c.total_consultas} consulta{c.total_consultas === 1 ? '' : 's'} · em aberto {formatCurrency(c.valor_aberto)}
                    </p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs uppercase text-gray-500 bg-gray-50 dark:bg-gray-800/80">
                          <th className="text-left px-4 py-2">Data</th>
                          <th className="text-left px-4 py-2">Consulta</th>
                          <th className="text-left px-4 py-2">Profissional</th>
                          <th className="text-left px-4 py-2">Procedimentos</th>
                          <th className="text-left px-4 py-2">Vencimento</th>
                          <th className="text-left px-4 py-2">Situação</th>
                          <th className="text-right px-4 py-2">Valor</th>
                          <th className="text-right px-4 py-2">Recebido</th>
                          <th className="text-right px-4 py-2">Em aberto</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {c.consultas.map((v) => (
                          <tr key={v.payment_id}>
                            <td className="px-4 py-2 whitespace-nowrap text-gray-600">{formatDate(v.data)}</td>
                            <td className="px-4 py-2 whitespace-nowrap">{v.consulta_numero ? `nº ${v.consulta_numero}` : '—'}</td>
                            <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{v.profissional || '—'}</td>
                            <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{v.procedimentos}</td>
                            <td className="px-4 py-2 whitespace-nowrap">{formatDate(v.vencimento)}</td>
                            <td className={`px-4 py-2 whitespace-nowrap ${situacaoClass(v.situacao)}`}>
                              {v.situacao_label}
                              {v.dias_atraso > 0 ? ` · ${v.dias_atraso} dia${v.dias_atraso === 1 ? '' : 's'}` : ''}
                            </td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(v.valor)}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(v.valor_pago)}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(v.valor_aberto)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              ))
            ) : (
              data.profissionais.map((p) => (
                <section key={p.professional_id} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex flex-wrap items-baseline justify-between gap-2">
                    <h2 className="font-semibold text-gray-900 dark:text-white">{p.nome}</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {p.total_vendas} venda{p.total_vendas === 1 ? '' : 's'} · em aberto {formatCurrency(p.valor_aberto)}
                    </p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-xs uppercase text-gray-500 bg-gray-50 dark:bg-gray-800/80">
                          <th className="text-left px-4 py-2">Data</th>
                          <th className="text-left px-4 py-2">Paciente</th>
                          <th className="text-left px-4 py-2">Procedimentos</th>
                          <th className="text-left px-4 py-2">Vencimento</th>
                          <th className="text-left px-4 py-2">Situação</th>
                          <th className="text-right px-4 py-2">Valor</th>
                          <th className="text-right px-4 py-2">Recebido</th>
                          <th className="text-right px-4 py-2">Em aberto</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                        {p.vendas.map((v) => (
                          <tr key={v.payment_id}>
                            <td className="px-4 py-2 whitespace-nowrap text-gray-600">{formatDate(v.data)}</td>
                            <td className="px-4 py-2 font-medium text-gray-900 dark:text-white">
                              {v.paciente}
                              {v.telefone ? (
                                <span className="block text-xs font-normal text-gray-500">{v.telefone}</span>
                              ) : null}
                            </td>
                            <td className="px-4 py-2 text-gray-700 dark:text-gray-300">{v.procedimentos}</td>
                            <td className="px-4 py-2 whitespace-nowrap">{formatDate(v.vencimento)}</td>
                            <td className={`px-4 py-2 whitespace-nowrap ${situacaoClass(v.situacao)}`}>
                              {v.situacao_label}
                              {v.dias_atraso > 0 ? ` · ${v.dias_atraso} dia${v.dias_atraso === 1 ? '' : 's'}` : ''}
                            </td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(v.valor)}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(v.valor_pago)}</td>
                            <td className="px-4 py-2 text-right tabular-nums">{formatCurrency(v.valor_aberto)}</td>
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
