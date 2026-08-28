"use client";

import { Play, Trash2 } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ConsultaPagamentoButton } from "@/components/clinica-beleza/consultas/ConsultaPagamentoButton";
import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { formatConsultaListDate } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  consultaProcedimentoLabel,
  ordenarConsultasProntuarioLista,
  prontuarioConsultaAtualAcoes,
} from "./prontuario-consultas-utils";

interface ProntuarioResumoSectionProps {
  consultas: Consulta[];
  loading: boolean;
  iniciandoId: number | null;
  excluindoId: number | null;
  recebendoId: number | null;
  onAbrirConsulta: (consultaId: number) => void;
  onIniciarConsulta: (consulta: Consulta) => void;
  onReceberConsulta: (consulta: Consulta) => void;
  onExcluirConsulta: (consulta: Consulta) => void;
}

function StatusBadge({ status }: { status: string }) {
  const colors = CLINICA_CONSULTA_STATUS_COLORS[status] ?? CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;
  return (
    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
      {CLINICA_CONSULTA_STATUS_LABEL[status] || status}
    </span>
  );
}

function AcoesConsulta({
  consulta,
  todas,
  iniciando,
  excluindo,
  onAbrir,
  onIniciar,
  onExcluir,
}: {
  consulta: Consulta;
  todas: Consulta[];
  iniciando: boolean;
  excluindo: boolean;
  onAbrir: (id: number) => void;
  onIniciar: (consulta: Consulta) => void;
  onExcluir: (consulta: Consulta) => void;
}) {
  const acoes = prontuarioConsultaAtualAcoes(consulta, todas);
  const btn =
    "inline-flex items-center justify-center gap-1 px-2 py-1 rounded-lg text-xs font-medium whitespace-nowrap disabled:opacity-50";
  return (
    <div className="flex flex-wrap items-center justify-end gap-1.5">
      {acoes.podeExcluir && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onExcluir(consulta);
          }}
          disabled={excluindo || iniciando}
          className={`${btn} border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20`}
        >
          <Trash2 size={12} />
          {excluindo ? "Excluindo…" : "Excluir"}
        </button>
      )}
      {acoes.podeIniciar && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onIniciar(consulta);
          }}
          disabled={iniciando || excluindo}
          className={`${btn} text-white`}
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          <Play size={12} />
          {iniciando ? "Iniciando…" : "Iniciar"}
        </button>
      )}
      {acoes.mostrarContinuar && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onAbrir(consulta.id);
          }}
          className={`${btn} text-white`}
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          <Play size={12} />
          Continuar
        </button>
      )}
      {!acoes.podeIniciar && !acoes.mostrarContinuar && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onAbrir(consulta.id);
          }}
          className={`${btn} text-white`}
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          Abrir
        </button>
      )}
    </div>
  );
}

export function ProntuarioResumoSection({
  consultas,
  loading,
  iniciandoId,
  excluindoId,
  recebendoId,
  onAbrirConsulta,
  onIniciarConsulta,
  onReceberConsulta,
  onExcluirConsulta,
}: ProntuarioResumoSectionProps) {
  if (loading) {
    return (
      <div className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm">
        Carregando consultas...
      </div>
    );
  }

  if (consultas.length === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-sm text-gray-500 dark:text-gray-400">
        Nenhuma consulta ainda. Agende na Agenda para iniciar o atendimento.
        Fotos e demais registros entram somente dentro da consulta.
      </ClinicaBelezaPanel>
    );
  }

  const lista = ordenarConsultasProntuarioLista(consultas);

  return (
    <div className="space-y-3">
      <section className="bg-white dark:bg-neutral-800 rounded-xl shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 dark:bg-neutral-700 border-b border-gray-200 dark:border-neutral-600">
              <tr>
                <th className="text-left py-3 px-4 font-semibold">Nº</th>
                <th className="text-left py-3 px-4 font-semibold">Data</th>
                <th className="text-left py-3 px-4 font-semibold hidden sm:table-cell">Profissional</th>
                <th className="text-left py-3 px-4 font-semibold">Procedimento</th>
                <th className="text-right py-3 px-4 font-semibold hidden md:table-cell">Valor</th>
                <th className="text-left py-3 px-4 font-semibold">Pagamento</th>
                <th className="text-left py-3 px-4 font-semibold">Status</th>
                <th className="py-3 px-4" />
              </tr>
            </thead>
            <tbody>
              {lista.map((c) => {
                const acoes = prontuarioConsultaAtualAcoes(c, consultas);
                return (
                  <tr
                    key={c.id}
                    onClick={() => onAbrirConsulta(c.id)}
                    className={`border-b border-gray-100 dark:border-neutral-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-700/40 ${
                      c.status === "IN_PROGRESS"
                        ? "bg-[color-mix(in_srgb,var(--cb-primary,#8B3D52)_6%,transparent)]"
                        : ""
                    }`}
                  >
                    <td className="py-3 px-4 whitespace-nowrap font-mono text-xs font-semibold text-gray-700 dark:text-gray-300">
                      {c.numero ? `#${c.numero}` : "—"}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-gray-600 dark:text-gray-400">
                      {formatConsultaListDate(c.data_inicio || c.appointment_date)}
                    </td>
                    <td className="py-3 px-4 hidden sm:table-cell text-gray-700 dark:text-gray-300">
                      {c.professional_name || "—"}
                    </td>
                    <td className="py-3 px-4 max-w-[220px] leading-snug text-gray-800 dark:text-gray-200">
                      {consultaProcedimentoLabel(c)}
                      {acoes.bloqueadaPorOutraEmAndamento && (
                        <span className="block text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                          Finalize a consulta em andamento antes de iniciar esta.
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-medium hidden md:table-cell whitespace-nowrap">
                      {formatCurrency(Number(c.valor_consulta) || 0)}
                    </td>
                    <td className="py-3 px-4">
                      <ConsultaPagamentoButton
                        consulta={c}
                        onReceber={onReceberConsulta}
                        size="sm"
                        loading={recebendoId === c.id}
                      />
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <AcoesConsulta
                        consulta={c}
                        todas={consultas}
                        iniciando={iniciandoId === c.id}
                        excluindo={excluindoId === c.id}
                        onAbrir={onAbrirConsulta}
                        onIniciar={onIniciarConsulta}
                        onExcluir={onExcluirConsulta}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Para incluir fotos, evolução ou documentos, abra a consulta atual.
      </p>
    </div>
  );
}
