'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Download, Search } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';

interface ProcedimentoAtendimento {
  nome: string;
  valor: number;
  comissao: number;
  regra: string;
}

interface AtendimentoRepasse {
  appointment_id: number;
  data_atendimento: string;
  hora_atendimento: string;
  paciente_nome: string;
  local_nome: string;
  forma_pagamento: string;
  valor_consulta: number;
  comissao_consulta: number;
  regra_consulta: string;
  procedimentos: ProcedimentoAtendimento[];
  valor_procedimentos: number;
  comissao_procedimentos: number;
  valor_atendimento: number;
  comissao_atendimento: number;
}

interface ProfissionalRepasse {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  comissao_total: number;
  atendimentos: AtendimentoRepasse[];
}

interface RelatorioRepasseData {
  profissionais: ProfissionalRepasse[];
  totais: {
    total_atendimentos: number;
    comissao_total: number;
  };
}

interface ProfessionalOption {
  id: number;
  nome: string;
}

function formatCurrency(value: number) {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function CardAtendimento({
  at,
  formatCurrency: fmt,
}: {
  at: AtendimentoRepasse;
  formatCurrency: (n: number) => string;
}) {
  return (
    <article className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <header
        className="px-4 py-3 border-b border-gray-100 dark:border-gray-700"
        style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}10` }}
      >
        <h3 className="font-semibold text-gray-900 dark:text-white">
          {at.data_atendimento} às {at.hora_atendimento}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
          <span className="font-medium">{at.paciente_nome}</span>
          {' · '}
          {at.local_nome}
          {' · '}
          {at.forma_pagamento}
        </p>
      </header>

      <div className="p-4 space-y-4">
        <div className="rounded-lg border border-gray-100 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800/50 text-xs text-gray-500">
                <th className="text-left px-3 py-2">Consulta</th>
                <th className="text-right px-3 py-2">Valor</th>
                <th className="text-right px-3 py-2">Regra</th>
                <th className="text-right px-3 py-2">Comissão</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="px-3 py-2">Taxa de consulta</td>
                <td className="px-3 py-2 text-right tabular-nums">{fmt(at.valor_consulta)}</td>
                <td className="px-3 py-2 text-right text-xs">{at.regra_consulta || '—'}</td>
                <td className="px-3 py-2 text-right tabular-nums font-medium">{fmt(at.comissao_consulta)}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {at.procedimentos.length > 0 && (
          <div className="rounded-lg border border-gray-100 dark:border-gray-700 overflow-hidden">
            <p className="px-3 py-2 text-xs font-semibold uppercase text-gray-500 bg-gray-50 dark:bg-gray-800/50">
              Procedimentos desta consulta
            </p>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-700 text-xs text-gray-500">
                  <th className="text-left px-3 py-2">Procedimento</th>
                  <th className="text-right px-3 py-2">Valor</th>
                  <th className="text-right px-3 py-2">Regra</th>
                  <th className="text-right px-3 py-2">Comissão</th>
                </tr>
              </thead>
              <tbody>
                {at.procedimentos.map((p) => (
                  <tr key={p.nome} className="border-b border-gray-50 dark:border-gray-800 last:border-0">
                    <td className="px-3 py-2">{p.nome}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmt(p.valor)}</td>
                    <td className="px-3 py-2 text-right text-xs">{p.regra || '—'}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmt(p.comissao)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50 dark:bg-gray-800/40 font-semibold text-sm">
                  <td className="px-3 py-2">Subtotal procedimentos</td>
                  <td className="px-3 py-2 text-right tabular-nums">{fmt(at.valor_procedimentos)}</td>
                  <td className="px-3 py-2" />
                  <td className="px-3 py-2 text-right tabular-nums">{fmt(at.comissao_procedimentos)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}

        <div
          className="flex flex-wrap justify-between items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold"
          style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}12` }}
        >
          <span className="text-gray-700 dark:text-gray-300">Total do atendimento</span>
          <span className="tabular-nums text-gray-600 dark:text-gray-400">
            Valor: {fmt(at.valor_atendimento)}
          </span>
          <span className="tabular-nums" style={{ color: CLINICA_BELEZA_PRIMARY }}>
            Comissão: {fmt(at.comissao_atendimento)}
          </span>
        </div>
      </div>
    </article>
  );
}

export default function RelatorioRepasseConsultasPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [dataInicio, setDataInicio] = useState(() => {
    const d = new Date();
    return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split('T')[0];
  });
  const [dataFim, setDataFim] = useState(() => new Date().toISOString().split('T')[0]);
  const [professionalId, setProfessionalId] = useState('');
  const [data, setData] = useState<RelatorioRepasseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState('');
  const [professionals, setProfessionals] = useState<ProfessionalOption[]>([]);

  const profissionalNome = useMemo(() => {
    if (!professionalId) return null;
    return professionals.find((x) => String(x.id) === professionalId)?.nome ?? null;
  }, [professionalId, professionals]);

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
      const res = await clinicaBelezaFetch(`/relatorios/repasse-consultas/?${qp.toString()}`);
      if (res.ok) {
        setData(await res.json());
      } else {
        setError('Erro ao carregar dados.');
        setData(null);
      }
    } catch {
      setError('Erro ao carregar dados.');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dataInicio, dataFim, professionalId]);

  useEffect(() => {
    buscar();
  }, [buscar]);

  const exportarPDF = async () => {
    setPdfLoading(true);
    setError('');
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set('professional_id', professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/repasse-consultas/pdf/?${qp.toString()}`);
      if (!res.ok) {
        setError('Não foi possível gerar o PDF.');
        return;
      }
      const blob = await res.blob();
      const nome = profissionalNome
        ? `repasse_${profissionalNome.replace(/\s+/g, '_')}_${dataInicio}_${dataFim}.pdf`
        : `repasse_consultas_${dataInicio}_${dataFim}.pdf`;
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = nome;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch {
      setError('Não foi possível gerar o PDF.');
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <ClinicaBelezaPageContent>
      <Link
        href={`/loja/${slug}/relatorios`}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-4 no-print"
      >
        <ArrowLeft size={16} /> Voltar aos relatórios
      </Link>

      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Repasse por Consulta
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Cada atendimento com consulta e procedimentos — para o profissional apresentar à clínica.
          </p>
        </div>
        <button
          type="button"
          onClick={exportarPDF}
          disabled={pdfLoading || !data?.profissionais.length}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50 shrink-0"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          <Download size={16} />
          {pdfLoading ? 'Gerando PDF…' : 'PDF'}
        </button>
      </div>

      <ClinicaBelezaPanel className="p-4 md:p-5 mb-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">De</label>
            <input
              type="date"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Até</label>
            <input
              type="date"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional</label>
            <select
              value={professionalId}
              onChange={(e) => setProfessionalId(e.target.value)}
              className="w-full px-3 py-2 text-sm border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="">Todos</option>
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>{p.nome}</option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={buscar}
            disabled={loading}
            className="self-end w-full inline-flex items-center justify-center gap-1.5 px-4 py-2 min-h-[40px] text-sm font-medium rounded-lg text-white"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            <Search size={16} /> Buscar
          </button>
        </div>
      </ClinicaBelezaPanel>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg mb-6 text-sm">{error}</div>
      )}

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && data && (
        <div className="space-y-8">
          {data.profissionais.length === 0 ? (
            <p className="text-center py-12 text-gray-500">Nenhum atendimento pago no período.</p>
          ) : (
            data.profissionais.map((p) => (
              <section key={p.professional_id}>
                <h2
                  className="text-lg font-bold mb-4"
                  style={{ color: CLINICA_BELEZA_PRIMARY }}
                >
                  {p.nome}
                  <span className="text-sm font-normal text-gray-500 ml-2">
                    {p.total_atendimentos} atendimento(s) · Comissão {formatCurrency(p.comissao_total)}
                  </span>
                </h2>
                <div className="grid grid-cols-1 2xl:grid-cols-2 gap-4">
                  {p.atendimentos.map((at) => (
                    <CardAtendimento
                      key={at.appointment_id}
                      at={at}
                      formatCurrency={formatCurrency}
                    />
                  ))}
                </div>
              </section>
            ))
          )}

          {data.profissionais.length > 1 && (
            <div
              className="rounded-xl border-2 border-gray-300 dark:border-gray-600 p-4"
              style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}08` }}
            >
              <p className="text-sm font-semibold mb-2">Totais do período</p>
              <p className="text-lg font-bold tabular-nums">
                {data.totais.total_atendimentos} atendimentos ·{' '}
                Comissão {formatCurrency(data.totais.comissao_total)}
              </p>
            </div>
          )}
        </div>
      )}
    </ClinicaBelezaPageContent>
  );
}
