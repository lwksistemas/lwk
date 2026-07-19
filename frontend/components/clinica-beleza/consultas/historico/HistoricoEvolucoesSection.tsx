"use client";

import { useEffect, useState } from "react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { imprimirConsultaPdfLazy, type ConsultaPrintMeta } from "@/lib/consulta-print-lazy";
import type { Consulta, Evolucao } from "../consultas-types";
import { ConsultaPrintButton } from "../ConsultaPrintButton";

export function HistoricoEvolucoesSection({
  historico,
  formatData,
  printMeta,
  emptyMsg = "Nenhuma evolução registrada.",
}: {
  historico: Consulta[];
  formatData: (d?: string | null) => string;
  printMeta: ConsultaPrintMeta;
  emptyMsg?: string;
}) {
  if (historico.length === 0) return <p className="text-gray-500 text-sm">{emptyMsg}</p>;

  return (
    <div className="space-y-4">
      {historico.map((h) => (
        <EvolucaoConsultaBlock key={h.id} consulta={h} formatData={formatData} />
      ))}
    </div>
  );
}

function EvolucaoConsultaBlock({
  consulta,
  formatData,
}: {
  consulta: Consulta;
  formatData: (d?: string | null) => string;
}) {
  const [evolucoes, setEvolucoes] = useState<Evolucao[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ClinicaBelezaAPI.consultas.evolucoes
      .list(consulta.id)
      .then((data) => {
        setEvolucoes(Array.isArray(data) ? data : []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [consulta.id]);

  return (
    <div className="border border-gray-200 dark:border-neutral-600 rounded-lg overflow-hidden">
      <div className="px-3 py-2 bg-gray-50 dark:bg-neutral-700/50 border-b border-gray-200 dark:border-neutral-600 flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-gray-800 dark:text-gray-200">
          {consulta.procedure_name} · {formatData(consulta.data_inicio)}
          {consulta.professional_name ? ` · ${consulta.professional_name}` : ""}
        </p>
        {!loading && evolucoes.length > 0 && (
          <ConsultaPrintButton
            labelImprimir={evolucoes.length > 1 ? "Imprimir todas" : "Imprimir"}
            onAction={(modo) => imprimirConsultaPdfLazy(consulta.id, "evolucao", modo)}
          />
        )}
      </div>
      <div className="p-3 space-y-2">
        {loading ? (
          <p className="text-xs text-gray-400">Carregando...</p>
        ) : evolucoes.length === 0 ? (
          <p className="text-xs text-gray-400">Sem evoluções.</p>
        ) : (
          evolucoes.map((ev) => (
            <div key={ev.id} className="text-sm space-y-1">
              <p className="text-xs text-gray-500">
                {formatData(ev.created_at)}
                {ev.professional_name ? ` · ${ev.professional_name}` : ""}
              </p>
              {ev.descricao && <p className="text-gray-800 dark:text-gray-200">{ev.descricao}</p>}
              {ev.procedimento_realizado && (
                <p className="text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Procedimento:</span> {ev.procedimento_realizado}
                </p>
              )}
              {ev.produtos_utilizados && (
                <p className="text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Produtos:</span> {ev.produtos_utilizados}
                </p>
              )}
              {ev.orientacoes && (
                <p className="text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Orientações:</span> {ev.orientacoes}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
