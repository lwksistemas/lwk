"use client";

import { useMemo } from "react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { formatRelatorioCurrency } from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import type { ProfissionalComissao } from "./comissoes-page-types";
import { calcOutrosProcedimentos, isLinhaConsulta } from "./comissoes-page-utils";

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
                  j === 0 ? "text-left" : "text-right"
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
                      j > 0 ? "text-right tabular-nums" : ""
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
                    j > 0 ? "text-right tabular-nums" : ""
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

export function ComissoesBlocoProfissional({ p }: { p: ProfissionalComissao }) {
  const formatCurrency = formatRelatorioCurrency;

  const linhasConsulta = useMemo(() => p.detalhes.filter(isLinhaConsulta), [p.detalhes]);
  const linhasProcedimento = useMemo(
    () => p.detalhes.filter((d) => !isLinhaConsulta(d)),
    [p.detalhes],
  );

  const qtdProcedimentos = linhasProcedimento.reduce((s, d) => s + d.qtd, 0);
  const valorProcedimentosVisivel = linhasProcedimento.reduce(
    (s, d) => s + d.valor_procedimento,
    0,
  );
  const outrosProcedimentos = calcOutrosProcedimentos(p, valorProcedimentosVisivel);

  return (
    <article className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden print:break-inside-avoid">
      <header className="px-4 py-3" style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}12` }}>
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">{p.nome}</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
          {p.total_atendimentos}{" "}
          {p.total_atendimentos === 1 ? "consulta paga" : "consultas pagas"}
          {qtdProcedimentos > 0 && (
            <span className="text-gray-400">
              {" "}
              · {qtdProcedimentos} {qtdProcedimentos === 1 ? "procedimento" : "procedimentos"}
            </span>
          )}
        </p>
      </header>

      <div className="p-4 flex flex-col gap-4">
        <MiniTabela
          titulo="1. Consultas"
          colunas={["Local", "Pagamento", "Qtd", "Valor consulta (R$)", "Regra", "Comissão consulta (R$)"]}
          linhas={linhasConsulta.map((d) => [
            d.local_nome || "—",
            d.forma_pagamento || "—",
            d.qtd,
            formatCurrency(d.valor_consulta),
            d.regra_consulta || "—",
            formatCurrency(d.comissao_consulta),
          ])}
          rodape={
            linhasConsulta.length > 0
              ? [
                  "Subtotal consultas",
                  "",
                  p.total_atendimentos,
                  formatCurrency(p.valor_consulta),
                  "",
                  formatCurrency(p.comissao_consulta),
                ]
              : undefined
          }
        />
        <MiniTabela
          titulo="2. Procedimentos"
          colunas={["Procedimento", "Convênio", "Qtd", "Valor procedimento (R$)", "Regra", "Comissão procedimento (R$)"]}
          linhas={linhasProcedimento.map((d) => [
            d.procedimento_nome,
            d.convenio_nome || "—",
            d.qtd,
            formatCurrency(d.valor_procedimento),
            d.regra_procedimento || "—",
            formatCurrency(d.comissao_procedimento),
          ])}
          rodape={
            linhasProcedimento.length > 0
              ? [
                  "Subtotal procedimentos",
                  "",
                  qtdProcedimentos,
                  formatCurrency(valorProcedimentosVisivel),
                  "",
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
