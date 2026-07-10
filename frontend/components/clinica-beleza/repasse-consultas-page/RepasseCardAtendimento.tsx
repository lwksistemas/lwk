"use client";

import { formatRelatorioCurrency } from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import type { AtendimentoRepasse } from "./repasse-consultas-page-types";

export function RepasseCardAtendimento({ at }: { at: AtendimentoRepasse }) {
  const fmt = formatRelatorioCurrency;

  return (
    <article className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <header
        className="px-4 py-3 border-b border-gray-100 dark:border-gray-700"
        style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 6%, transparent)' }}
      >
        <h3 className="font-semibold text-gray-900 dark:text-white">
          {at.data_atendimento} às {at.hora_atendimento}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
          <span className="font-medium">{at.paciente_nome}</span>
          {" · "}
          {at.local_nome}
          {" · "}
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
                <td className="px-3 py-2 text-right text-xs">{at.regra_consulta || "—"}</td>
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
                    <td className="px-3 py-2 text-right text-xs">{p.regra || "—"}</td>
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
          style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 7%, transparent)' }}
        >
          <span className="text-gray-700 dark:text-gray-300">Total do atendimento</span>
          <span className="tabular-nums text-gray-600 dark:text-gray-400">Valor: {fmt(at.valor_atendimento)}</span>
          <span className="tabular-nums" style={{ color: 'var(--cb-primary, #8B3D52)' }}>
            Comissão: {fmt(at.comissao_atendimento)}
          </span>
        </div>
      </div>
    </article>
  );
}
