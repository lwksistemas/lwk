'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Download, Printer, Search } from 'lucide-react';
import { clinicaBelezaFetch } from '@/lib/clinica-beleza-api';
import { CLINICA_BELEZA_PRIMARY } from '@/components/clinica-beleza/clinica-beleza-nav';
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';

interface DetalheComissao {
  local_nome: string;
  forma_pagamento?: string;
  procedimento_nome: string;
  tipo_linha?: 'consulta' | 'procedimento';
  qtd: number;
  valor_consulta: number;
  valor_procedimento: number;
  comissao_consulta: number;
  comissao_procedimento: number;
  comissao: number;
  modo_consulta: string;
  regra_consulta: string;
  modo_procedimento: string;
  regra_procedimento: string;
  convenio_nome?: string;
}

interface ProfissionalComissao {
  professional_id: number;
  nome: string;
  total_atendimentos: number;
  valor_consulta: number;
  valor_procedimento: number;
  valor_total: number;
  comissao_consulta: number;
  comissao_procedimento: number;
  comissao_total: number;
  detalhes: DetalheComissao[];
}

interface RelatorioData {
  profissionais: ProfissionalComissao[];
  totais: {
    total_atendimentos: number;
    valor_consulta: number;
    valor_procedimento: number;
    valor_total: number;
    comissao_consulta: number;
    comissao_procedimento: number;
    comissao_total: number;
  };
}

interface ProfessionalOption {
  id: number;
  nome: string;
}

type AgrupamentoComissao = 'profissional' | 'local' | 'convenio';

function parseAgrupamentoComissao(raw: string | null): AgrupamentoComissao {
  if (raw === 'local' || raw === 'convenio' || raw === 'profissional') return raw;
  return 'profissional';
}

const AGRUPAMENTO_TITULOS: Record<AgrupamentoComissao, string> = {
  profissional: 'Comissão por Profissional',
  local: 'Comissão por Local de Atendimento',
  convenio: 'Comissão por Convênio',
};

interface LinhaAgrupada {
  nome: string;
  total_atendimentos: number;
  valor_consulta: number;
  valor_procedimento: number;
  valor_total: number;
  comissao_consulta: number;
  comissao_procedimento: number;
  comissao_total: number;
}

function isLinhaConsulta(d: DetalheComissao) {
  return d.tipo_linha === 'consulta' || d.procedimento_nome === 'Consulta';
}

function agruparDetalhes(
  data: RelatorioData,
  chave: 'local' | 'convenio',
): LinhaAgrupada[] {
  const map = new Map<string, LinhaAgrupada>();
  for (const p of data.profissionais) {
    for (const d of p.detalhes) {
      const nome =
        chave === 'local'
          ? (d.local_nome || '').trim() || 'Sem local'
          : (d.convenio_nome || '').trim() || (isLinhaConsulta(d) ? 'Particular / sem convênio' : 'Sem convênio');
      let row = map.get(nome);
      if (!row) {
        row = {
          nome,
          total_atendimentos: 0,
          valor_consulta: 0,
          valor_procedimento: 0,
          valor_total: 0,
          comissao_consulta: 0,
          comissao_procedimento: 0,
          comissao_total: 0,
        };
        map.set(nome, row);
      }
      if (isLinhaConsulta(d)) {
        row.total_atendimentos += d.qtd;
        row.valor_consulta += d.valor_consulta;
        row.comissao_consulta += d.comissao_consulta;
      } else {
        row.valor_procedimento += d.valor_procedimento;
        row.comissao_procedimento += d.comissao_procedimento;
      }
      row.valor_total = row.valor_consulta + row.valor_procedimento;
      row.comissao_total = row.comissao_consulta + row.comissao_procedimento;
    }
  }
  return Array.from(map.values()).sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
}

function MiniTabela({
  titulo,
  colunas,
  linhas,
  rodape,
}: {
  titulo: string;
  colunas: string[];
  linhas: (string | number)[][];
  rodape?: (string | number)[];
}) {
  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden">
      <div
        className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-600 dark:text-gray-300"
        style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}08` }}
      >
        {titulo}
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-800/50">
            {colunas.map((c, j) => (
              <th
                key={c}
                className={`px-3 py-2 text-xs font-medium text-gray-500 dark:text-gray-400 ${
                  j === 0 ? 'text-left' : 'text-right'
                }`}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.length === 0 ? (
            <tr>
              <td colSpan={colunas.length} className="px-3 py-4 text-center text-gray-400 text-sm">
                Nenhum registro
              </td>
            </tr>
          ) : (
            linhas.map((row, i) => (
              <tr key={i} className="border-b border-gray-50 dark:border-gray-700/80 last:border-0">
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className={`px-3 py-2 text-gray-700 dark:text-gray-300 ${
                      j > 0 ? 'text-right tabular-nums' : ''
                    }`}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
        {rodape && linhas.length > 0 && (
          <tfoot>
            <tr className="bg-gray-50 dark:bg-gray-700/40 font-semibold">
              {rodape.map((cell, j) => (
                <td
                  key={j}
                  className={`px-3 py-2 text-gray-900 dark:text-white ${
                    j > 0 ? 'text-right tabular-nums' : ''
                  }`}
                >
                  {cell}
                </td>
              ))}
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}

function BlocoProfissional({
  p,
  formatCurrency,
}: {
  p: ProfissionalComissao;
  formatCurrency: (n: number) => string;
}) {
  const linhasConsulta = useMemo(
    () => p.detalhes.filter(isLinhaConsulta),
    [p.detalhes],
  );
  const linhasProcedimento = useMemo(
    () => p.detalhes.filter((d) => !isLinhaConsulta(d)),
    [p.detalhes],
  );

  const qtdProcedimentos = linhasProcedimento.reduce((s, d) => s + d.qtd, 0);
  const valorProcedimentosVisivel = linhasProcedimento.reduce(
    (s, d) => s + d.valor_procedimento,
    0,
  );
  const outrosProcedimentos =
    p.valor_procedimento > valorProcedimentosVisivel + 0.009
      ? p.valor_procedimento - valorProcedimentosVisivel
      : 0;

  return (
    <article className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden print:break-inside-avoid">
      <header
        className="px-4 py-3"
        style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}12` }}
      >
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">{p.nome}</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
          {p.total_atendimentos}{' '}
          {p.total_atendimentos === 1 ? 'consulta paga' : 'consultas pagas'}
          {qtdProcedimentos > 0 && (
            <span className="text-gray-400">
              {' '}
              · {qtdProcedimentos} {qtdProcedimentos === 1 ? 'procedimento' : 'procedimentos'}
            </span>
          )}
        </p>
      </header>

      <div className="p-4 flex flex-col gap-4">
        <MiniTabela
          titulo="1. Consultas"
          colunas={['Local', 'Pagamento', 'Qtd', 'Valor consulta (R$)', 'Regra', 'Comissão consulta (R$)']}
          linhas={linhasConsulta.map((d) => [
            d.local_nome || '—',
            d.forma_pagamento || '—',
            d.qtd,
            formatCurrency(d.valor_consulta),
            d.regra_consulta || '—',
            formatCurrency(d.comissao_consulta),
          ])}
          rodape={
            linhasConsulta.length > 0
              ? [
                  'Subtotal consultas',
                  '',
                  p.total_atendimentos,
                  formatCurrency(p.valor_consulta),
                  '',
                  formatCurrency(p.comissao_consulta),
                ]
              : undefined
          }
        />
        <MiniTabela
          titulo="2. Procedimentos"
          colunas={['Procedimento', 'Convênio', 'Qtd', 'Valor procedimento (R$)', 'Regra', 'Comissão procedimento (R$)']}
          linhas={linhasProcedimento.map((d) => [
            d.procedimento_nome,
            d.convenio_nome || '—',
            d.qtd,
            formatCurrency(d.valor_procedimento),
            d.regra_procedimento || '—',
            formatCurrency(d.comissao_procedimento),
          ])}
          rodape={
            linhasProcedimento.length > 0
              ? [
                  'Subtotal procedimentos',
                  '',
                  qtdProcedimentos,
                  formatCurrency(valorProcedimentosVisivel),
                  '',
                  formatCurrency(p.comissao_procedimento),
                ]
              : undefined
          }
        />
      </div>

      <footer className="px-4 py-4 border-t border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/60 space-y-3 text-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">3. Resumo</p>
        <div className="rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden divide-y divide-gray-100 dark:divide-gray-700">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 px-3 py-2.5 bg-white dark:bg-gray-800/80">
            <span className="text-gray-600 dark:text-gray-400 sm:col-span-2">Consultas</span>
            <span className="text-right tabular-nums font-medium text-gray-900 dark:text-white">
              {formatCurrency(p.valor_consulta)}
            </span>
            <span className="text-right tabular-nums text-gray-700 dark:text-gray-300">
              Comissão {formatCurrency(p.comissao_consulta)}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 px-3 py-2.5 bg-white dark:bg-gray-800/80">
            <span className="text-gray-600 dark:text-gray-400 sm:col-span-2">Procedimentos</span>
            <span className="text-right tabular-nums font-medium text-gray-900 dark:text-white">
              {formatCurrency(valorProcedimentosVisivel)}
            </span>
            <span className="text-right tabular-nums text-gray-700 dark:text-gray-300">
              Comissão {formatCurrency(p.comissao_procedimento)}
            </span>
          </div>
          {outrosProcedimentos > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 px-3 py-2.5 bg-white dark:bg-gray-800/80">
              <span className="text-gray-500 dark:text-gray-400 sm:col-span-2 text-xs">
                Outros procedimentos do atendimento (sem comissão cadastrada)
              </span>
              <span className="text-right tabular-nums text-gray-600 dark:text-gray-400 text-xs">
                {formatCurrency(outrosProcedimentos)}
              </span>
              <span />
            </div>
          )}
          <div
            className="grid grid-cols-2 sm:grid-cols-4 gap-2 px-3 py-3 font-semibold"
            style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}10` }}
          >
            <span className="text-gray-900 dark:text-white sm:col-span-2">Total do período</span>
            <span className="text-right tabular-nums text-lg text-gray-900 dark:text-white">
              {formatCurrency(p.valor_total)}
            </span>
            <span className="text-right tabular-nums text-lg" style={{ color: CLINICA_BELEZA_PRIMARY }}>
              Comissão {formatCurrency(p.comissao_total)}
            </span>
          </div>
        </div>
      </footer>
    </article>
  );
}

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
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const slug = params.slug as string;

  const agrupamento = parseAgrupamentoComissao(searchParams.get('agrupar'));
  const porProfissional = agrupamento === 'profissional';

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
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [clinicaNome, setClinicaNome] = useState('');
  const [temTimbrado, setTemTimbrado] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  const setAgrupamento = (value: AgrupamentoComissao) => {
    const qp = new URLSearchParams(searchParams.toString());
    qp.set('agrupar', value);
    router.replace(`${pathname}?${qp.toString()}`);
  };

  const profissionalNome = useMemo(() => {
    if (!professionalId || !porProfissional) return null;
    const p = professionals.find((x) => String(x.id) === professionalId);
    return p?.nome ?? null;
  }, [professionalId, professionals, porProfissional]);

  const linhasAgrupadas = useMemo(() => {
    if (!data || porProfissional) return [];
    return agruparDetalhes(data, agrupamento === 'local' ? 'local' : 'convenio');
  }, [data, agrupamento, porProfissional]);

  useEffect(() => {
    clinicaBelezaFetch('/loja-info/')
      .then(async (res) => {
        if (res.ok) {
          const info = await res.json();
          setClinicaNome(info.nome || info.owner_username || '');
        }
      })
      .catch(() => {});
    fetch(`/api/superadmin/lojas/info_publica/?slug=${slug}`)
      .then(async (res) => {
        if (res.ok) {
          const info = await res.json();
          if (info.logo) setLogoUrl(info.logo);
          else if (info.login_logo) setLogoUrl(info.login_logo);
          if (info.nome) setClinicaNome(info.nome);
        }
      })
      .catch(() => {});
    clinicaBelezaFetch('/memed/timbrado/')
      .then(async (res) => {
        if (res.ok) {
          const t = await res.json();
          setTemTimbrado(Boolean(t.tem_timbrado));
        }
      })
      .catch(() => {});
  }, [slug]);

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
      if (porProfissional && professionalId) qp.set('professional_id', professionalId);
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
  }, [dataInicio, dataFim, professionalId, porProfissional]);

  useEffect(() => {
    buscar();
  }, [buscar]);

  const formatCurrency = (value: number) =>
    value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const exportarCSV = () => {
    if (!data) return;
    const BOM = '\ufeff';
    let csv = '';
    if (!porProfissional) {
      const label = agrupamento === 'local' ? 'Local' : 'Convênio';
      csv = `${label};Consultas;Valor consulta (R$);Comissão consulta (R$);Valor procedimentos (R$);Comissão procedimentos (R$);Valor total (R$);Comissão total (R$)\n`;
      for (const row of linhasAgrupadas) {
        csv +=
          `${row.nome};${row.total_atendimentos};${row.valor_consulta.toFixed(2)};${row.comissao_consulta.toFixed(2)};` +
          `${row.valor_procedimento.toFixed(2)};${row.comissao_procedimento.toFixed(2)};` +
          `${row.valor_total.toFixed(2)};${row.comissao_total.toFixed(2)}\n`;
      }
      csv +=
        `TOTAL;${data.totais.total_atendimentos};${data.totais.valor_consulta.toFixed(2)};${data.totais.comissao_consulta.toFixed(2)};` +
        `${data.totais.valor_procedimento.toFixed(2)};${data.totais.comissao_procedimento.toFixed(2)};` +
        `${data.totais.valor_total.toFixed(2)};${data.totais.comissao_total.toFixed(2)}\n`;
    } else {
      csv =
        'Profissional;Tipo;Item;Convênio;Local;Qtd;Valor (R$);Regra;Comissão (R$)\n';
      for (const p of data.profissionais) {
        for (const d of p.detalhes.filter(isLinhaConsulta)) {
          csv +=
            `${p.nome};Consulta;${d.local_nome || 'Consulta'};;${d.local_nome || ''};${d.qtd};` +
            `${d.valor_consulta.toFixed(2)};${d.regra_consulta || ''};${d.comissao_consulta.toFixed(2)}\n`;
        }
        for (const d of p.detalhes.filter((x) => !isLinhaConsulta(x))) {
          csv +=
            `${p.nome};Procedimento;${d.procedimento_nome};${d.convenio_nome || ''};${d.local_nome || ''};${d.qtd};` +
            `${d.valor_procedimento.toFixed(2)};${d.regra_procedimento};${d.comissao_procedimento.toFixed(2)}\n`;
        }
        csv +=
          `${p.nome};Resumo consulta;;;${p.total_atendimentos};${p.valor_consulta.toFixed(2)};;${p.comissao_consulta.toFixed(2)}\n`;
        csv +=
          `${p.nome};Resumo procedimentos;;;;${p.valor_procedimento.toFixed(2)};;${p.comissao_procedimento.toFixed(2)}\n`;
        csv +=
          `${p.nome};Total;;;;${p.valor_total.toFixed(2)};;${p.comissao_total.toFixed(2)}\n`;
      }
      csv +=
        `TOTAIS;Valor consulta;;;;${data.totais.valor_consulta.toFixed(2)};;${data.totais.comissao_consulta.toFixed(2)}\n`;
      csv +=
        `TOTAIS;Valor procedimentos;;;;${data.totais.valor_procedimento.toFixed(2)};;${data.totais.comissao_procedimento.toFixed(2)}\n`;
      csv +=
        `TOTAIS;Geral;;;;${data.totais.valor_total.toFixed(2)};;${data.totais.comissao_total.toFixed(2)}\n`;
    }

    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `comissoes_${agrupamento}_${dataInicio}_${dataFim}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const exportarPDF = async () => {
    setPdfLoading(true);
    setError('');
    try {
      const qp = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
      if (professionalId) qp.set('professional_id', professionalId);
      const res = await clinicaBelezaFetch(`/relatorios/comissoes/pdf/?${qp.toString()}`);
      if (!res.ok) {
        setError('Não foi possível gerar o PDF. Tente novamente.');
        return;
      }
      const blob = await res.blob();
      const nomeArquivo = profissionalNome
        ? `comissoes_${profissionalNome.replace(/\s+/g, '_')}_${dataInicio}_${dataFim}.pdf`
        : `comissoes_${dataInicio}_${dataFim}.pdf`;
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = nomeArquivo;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch {
      setError('Não foi possível gerar o PDF. Tente novamente.');
    } finally {
      setPdfLoading(false);
    }
  };

  const temDados = porProfissional
    ? Boolean(data?.profissionais.length)
    : linhasAgrupadas.length > 0;

  const exportActions = (
    <>
      <button
        type="button"
        onClick={exportarCSV}
        disabled={!temDados}
        className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 disabled:opacity-50"
      >
        <Download size={16} />
        <span className="hidden sm:inline">CSV</span>
      </button>
      {porProfissional && (
        <button
          type="button"
          onClick={exportarPDF}
          disabled={!data?.profissionais.length || pdfLoading}
          className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-lg text-white disabled:opacity-50"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          title={
            !logoUrl && temTimbrado
              ? 'PDF com papel timbrado (Configurações → Memed). Para imprimir, use o visualizador do PDF.'
              : 'Baixar relatório em PDF. Para imprimir, use o visualizador do PDF.'
          }
        >
          <Printer size={16} />
          <span className="hidden sm:inline">{pdfLoading ? 'Gerando…' : 'PDF'}</span>
          <span className="sm:hidden">{pdfLoading ? '…' : 'PDF'}</span>
        </button>
      )}
    </>
  );

  const titulo = AGRUPAMENTO_TITULOS[agrupamento];
  const colunaAgrupamento = agrupamento === 'local' ? 'Local' : 'Convênio';

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={titulo}
        subtitle={
          porProfissional
            ? 'Consultas, procedimentos e total por profissional'
            : agrupamento === 'local'
              ? 'Totais consolidados apenas por local de atendimento'
              : 'Totais consolidados apenas por convênio'
        }
        backHref={`/loja/${slug}/relatorios`}
        extraActions={exportActions}
      />
      <ClinicaBelezaPageContent className="print-area">
      <div className="hidden print:block mb-6 text-center">
        {logoUrl ? (
          <div className="flex justify-center mb-4">
            <img src={logoUrl} alt={clinicaNome} className="max-h-20 object-contain" />
          </div>
        ) : clinicaNome ? (
          <p className="text-lg font-bold text-gray-800 mb-2">{clinicaNome}</p>
        ) : null}
        <h1 className="text-2xl font-bold" style={{ color: CLINICA_BELEZA_PRIMARY }}>
          {titulo}
        </h1>
        {profissionalNome && (
          <p className="text-base font-semibold text-gray-800 mt-2">Profissional: {profissionalNome}</p>
        )}
        <p className="text-sm text-gray-600 mt-1">
          Período: {dataInicio} a {dataFim}
        </p>
      </div>

      <ClinicaBelezaPanel className="p-4 mb-6 no-print">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
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
              onChange={(e) => setAgrupamento(e.target.value as AgrupamentoComissao)}
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="profissional">Profissional</option>
              <option value="local">Local de Atendimento</option>
              <option value="convenio">Convênio</option>
            </select>
          </div>
          {porProfissional && (
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Profissional
              </label>
              <select
                value={professionalId}
                onChange={(e) => setProfessionalId(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Todos</option>
                {professionals.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nome}
                  </option>
                ))}
              </select>
            </div>
          )}
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
          <div className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && data && (
        <div className="space-y-6">
          {!temDados ? (
            <p className="text-center py-12 text-gray-500">Nenhum dado no período.</p>
          ) : porProfissional ? (
            <>
              {data.profissionais.map((p) => (
                <BlocoProfissional key={p.professional_id} p={p} formatCurrency={formatCurrency} />
              ))}

              {data.profissionais.length > 1 && (
              <div
                className="rounded-xl border-2 border-gray-300 dark:border-gray-600 p-4"
                style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}08` }}
              >
                <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                  Totais do período
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-gray-500 uppercase">Valor consulta</p>
                    <p className="text-lg font-bold tabular-nums">
                      {formatCurrency(data.totais.valor_consulta)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase">Comissão consulta</p>
                    <p className="text-lg font-bold tabular-nums">
                      {formatCurrency(data.totais.comissao_consulta)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase">Valor procedimentos</p>
                    <p className="text-lg font-bold tabular-nums">
                      {formatCurrency(data.totais.valor_procedimento)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 uppercase">Comissão procedimentos</p>
                    <p className="text-lg font-bold tabular-nums">
                      {formatCurrency(data.totais.comissao_procedimento)}
                    </p>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-300 dark:border-gray-600 flex flex-wrap justify-end items-end gap-x-10 gap-y-2">
                  <div className="text-right">
                    <p className="text-xs text-gray-500 uppercase">Comissão total</p>
                    <p
                      className="text-xl font-bold tabular-nums"
                      style={{ color: CLINICA_BELEZA_PRIMARY }}
                    >
                      {formatCurrency(data.totais.comissao_total)}
                    </p>
                  </div>
                  <div className="text-right pl-6 border-l-2 border-gray-400 dark:border-gray-500">
                    <p className="text-xs text-gray-500 uppercase">Valor total</p>
                    <p className="text-2xl font-bold tabular-nums text-gray-900 dark:text-white">
                      {formatCurrency(data.totais.valor_total)}
                    </p>
                  </div>
                </div>
              </div>
              )}
            </>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 dark:border-gray-700 bg-gray-50/80 dark:bg-gray-800/50">
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500">{colunaAgrupamento}</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">Consultas</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">Valor consulta</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">Comissão consulta</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">Valor procedimentos</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">Comissão procedimentos</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">Valor total</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500">Comissão total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {linhasAgrupadas.map((row) => (
                      <tr key={row.nome} className="border-b border-gray-50 dark:border-gray-700/80 last:border-0">
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{row.nome}</td>
                        <td className="px-4 py-3 text-right tabular-nums">{row.total_atendimentos}</td>
                        <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(row.valor_consulta)}</td>
                        <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(row.comissao_consulta)}</td>
                        <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(row.valor_procedimento)}</td>
                        <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(row.comissao_procedimento)}</td>
                        <td className="px-4 py-3 text-right tabular-nums font-medium">{formatCurrency(row.valor_total)}</td>
                        <td className="px-4 py-3 text-right tabular-nums font-semibold" style={{ color: CLINICA_BELEZA_PRIMARY }}>
                          {formatCurrency(row.comissao_total)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-gray-50 dark:bg-gray-700/40 font-semibold">
                      <td className="px-4 py-3">Total</td>
                      <td className="px-4 py-3 text-right tabular-nums">{data.totais.total_atendimentos}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(data.totais.valor_consulta)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(data.totais.comissao_consulta)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(data.totais.valor_procedimento)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(data.totais.comissao_procedimento)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{formatCurrency(data.totais.valor_total)}</td>
                      <td className="px-4 py-3 text-right tabular-nums" style={{ color: CLINICA_BELEZA_PRIMARY }}>
                        {formatCurrency(data.totais.comissao_total)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
      </ClinicaBelezaPageContent>
    </>
  );
}
