'use client';

import { useEffect, useState } from 'react';
import { fetchRelatorio } from '@/lib/clinica-geral-api';
import type { RelatorioResposta, TipoRelatorio } from '@/lib/clinica-geral-types';
import { RELATORIO_TITULO, STATUS_LABEL, TIPO_CONSULTA_LABEL } from '@/lib/clinica-geral-types';
import { formatBRL, formatHora, monthRange } from '@/lib/clinica-geral-utils';

const TEAL = '#0D9B9B';

export function RelatoriosPage({ tipo }: { tipo: TipoRelatorio }) {
  const padrao = monthRange();
  const [de, setDe] = useState(padrao.de);
  const [ate, setAte] = useState(padrao.ate);
  const [dados, setDados] = useState<RelatorioResposta | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    setLoading(true);
    setErro('');
    void fetchRelatorio(tipo, de, ate)
      .then(setDados)
      .catch(() => setErro('Não foi possível carregar o relatório.'))
      .finally(() => setLoading(false));
  }, [tipo, de, ate]);

  return (
    <div className="p-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <h1 className="text-xl font-semibold text-slate-800">{RELATORIO_TITULO[tipo]}</h1>
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-sm text-slate-600">
            De
            <input type="date" value={de} onChange={(e) => setDe(e.target.value)} className="ml-2 rounded border border-slate-300 px-2 py-1" />
          </label>
          <label className="text-sm text-slate-600">
            Até
            <input type="date" value={ate} onChange={(e) => setAte(e.target.value)} className="ml-2 rounded border border-slate-300 px-2 py-1" />
          </label>
          <button type="button" onClick={() => window.print()} className="rounded-md px-3 py-1.5 text-sm text-white" style={{ backgroundColor: TEAL }}>
            Imprimir
          </button>
        </div>
      </div>

      {erro && <p className="text-sm text-red-600">{erro}</p>}
      {loading && <p className="text-sm text-slate-500">Carregando relatório...</p>}
      {!loading && dados && <Conteudo tipo={tipo} dados={dados} />}
    </div>
  );
}

function Conteudo({ tipo, dados }: { tipo: TipoRelatorio; dados: RelatorioResposta }) {
  if (tipo === 'indicacao') {
    return (
      <Tabela
        colunas={['Indicação', 'Pacientes']}
        linhas={(dados.itens || []).map((i) => [i.indicacao || '—', String(i.total ?? 0)])}
        rodape={`Sem indicação: ${dados.sem_indicacao ?? 0}`}
      />
    );
  }
  if (tipo === 'status') {
    return (
      <Tabela
        colunas={['Status', 'Total']}
        linhas={(dados.itens || []).map((i) => [STATUS_LABEL[i.status as keyof typeof STATUS_LABEL] || i.status || '—', String(i.total ?? 0)])}
        rodape={`Total no período: ${dados.total ?? 0}`}
      />
    );
  }
  if (tipo === 'financeiro') {
    return (
      <div>
        <Tabela
          colunas={['Convênio', 'Consultas', 'Valor']}
          linhas={(dados.itens || []).map((i) => [
            i.convenio || 'PARTICULAR',
            String(i.total ?? 0),
            formatBRL(i.valor),
          ])}
          rodape={`Total: ${dados.total ?? 0} · ${formatBRL(dados.valor_total)}`}
        />
      </div>
    );
  }
  if (tipo === 'outros') {
    return (
      <Tabela
        colunas={['Indicador', 'Total']}
        linhas={[
          ['Faltas', String(dados.faltas ?? 0)],
          ['Desmarcados', String(dados.desmarcados ?? 0)],
          ['Primeiras consultas', String(dados.primeiras ?? 0)],
          ['Retornos', String(dados.retornos ?? 0)],
          ['Pacientes novos no período', String(dados.pacientes_novos ?? 0)],
          ['Pacientes ativos', String(dados.pacientes_ativos ?? 0)],
        ]}
      />
    );
  }
  return (
    <Tabela
      colunas={['Data', 'Hora', 'Paciente', 'Tipo', 'Convênio', 'Status']}
      linhas={(dados.itens || []).map((c) => [
        c.data || '',
        formatHora(c.hora || ''),
        c.paciente_nome || '—',
        TIPO_CONSULTA_LABEL[c.tipo] || c.tipo || '—',
        c.convenio || 'PARTICULAR',
        STATUS_LABEL[c.status as keyof typeof STATUS_LABEL] || c.status || '—',
      ])}
      rodape={`Total de atendimentos: ${dados.total ?? 0}`}
    />
  );
}

function Tabela({
  colunas,
  linhas,
  rodape,
}: {
  colunas: string[];
  linhas: string[][];
  rodape?: string;
}) {
  return (
    <div className="overflow-auto rounded-lg border border-slate-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500">
          <tr>
            {colunas.map((c) => (
              <th key={c} className="px-4 py-2 font-medium">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.length === 0 ? (
            <tr>
              <td colSpan={colunas.length} className="px-4 py-6 text-slate-500">
                Nenhum registro no período.
              </td>
            </tr>
          ) : (
            linhas.map((linha, i) => (
              <tr key={i} className="border-t border-slate-100">
                {linha.map((cel, j) => (
                  <td key={j} className="px-4 py-2">{cel}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {rodape && <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-500">{rodape}</p>}
    </div>
  );
}
