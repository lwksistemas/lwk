"use client";

import { CheckCircle2, FileText, Play, Trash2 } from "lucide-react";
import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { toUpperCase } from "@/lib/format-br";
import { ConsultaPagamentoButton } from "./ConsultaPagamentoButton";
import type { Consulta, ConsultaProcedimento } from "./consultas-types";

interface ConsultaDetailStatusBarProps {
  selected: Consulta;
  procedimentosRealizados: ConsultaProcedimento[];
  formatData: (d?: string | null) => string;
  valorPagamentoConsulta: (c: Consulta) => number;
  outraConsultaEmAndamento?: Consulta;
  podeIniciar: boolean;
  podeFinalizar: boolean;
  podeExcluir: boolean;
  consultaAtiva?: boolean;
  recebendo: boolean;
  emitindoNfse?: boolean;
  iniciando: boolean;
  onIniciar: () => void;
  onReceber: () => void;
  onEmitirNfse?: () => void;
  onFinalizar: () => void;
  onExcluir: () => void;
}

export function ConsultaDetailStatusBar({
  selected,
  procedimentosRealizados,
  formatData,
  valorPagamentoConsulta,
  outraConsultaEmAndamento,
  podeIniciar,
  podeFinalizar,
  podeExcluir,
  consultaAtiva = false,
  recebendo,
  emitindoNfse = false,
  iniciando,
  onIniciar,
  onReceber,
  onEmitirNfse,
  onFinalizar,
  onExcluir,
}: ConsultaDetailStatusBarProps) {
  const statusColors =
    CLINICA_CONSULTA_STATUS_COLORS[selected.status] ?? CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-600 dark:text-gray-400">
      <span>Agendado: {formatData(selected.appointment_date)}</span>
      <span>Início: {formatData(selected.data_inicio)}</span>
      <span>Fim: {formatData(selected.data_fim)}</span>
      <span>Total: {formatCurrency(valorPagamentoConsulta(selected))}</span>
      {procedimentosRealizados.length > 0 && (
        <span>
          Procedimentos:{" "}
          <strong className="text-gray-800 dark:text-gray-200 uppercase">
            {procedimentosRealizados
              .map((p) => `${toUpperCase(p.nome)} (${formatCurrency(p.valor)})`)
              .join(" · ")}
          </strong>
        </span>
      )}
      <span
        className={`px-2 py-0.5 rounded-full text-xs font-medium uppercase ${statusColors.bg} ${statusColors.text}`}
      >
        {CLINICA_CONSULTA_STATUS_LABEL[selected.status] || toUpperCase(selected.status)}
      </span>
      {selected.protocol_name && (
        <span>
          Protocolo:{" "}
          <strong className="text-gray-800 dark:text-gray-200 uppercase">
            {toUpperCase(selected.protocol_name)}
          </strong>
        </span>
      )}
      {selected.local_atendimento_name && (
        <span>
          Local:{" "}
          <strong className="text-gray-800 dark:text-gray-200 uppercase">
            {toUpperCase(selected.local_atendimento_name)}
          </strong>
        </span>
      )}
      <span>
        Convênio:{" "}
        <strong className="text-gray-800 dark:text-gray-200 uppercase">
          {toUpperCase(selected.convenio_name || "Particular")}
        </strong>
      </span>
      <div className="ml-auto flex flex-wrap gap-2">
        {outraConsultaEmAndamento &&
          (selected.status === "SCHEDULED" || selected.status === "RECEBER") && (
          <p className="text-xs text-amber-700 dark:text-amber-400 max-w-xs">
            Já existe consulta em andamento para este paciente. Finalize-a antes de iniciar outra.
          </p>
        )}
        <ConsultaPagamentoButton
          consulta={selected}
          onReceber={() => {
            onReceber();
          }}
          size="md"
          loading={recebendo}
        />
        {selected.payment_status === "PAID" && onEmitirNfse && (
          <button
            type="button"
            onClick={onEmitirNfse}
            disabled={emitindoNfse}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            title="Emitir NFS-e desta consulta"
          >
            <FileText size={16} />
            {emitindoNfse ? "Emitindo…" : "Emitir NFS-e"}
          </button>
        )}
        {/* Em atendimento, Finalizar/Excluir ficam no header — aqui só pagamento */}
        {!consultaAtiva && podeIniciar && (
          <button
            type="button"
            onClick={onIniciar}
            disabled={iniciando}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: "#2563eb" }}
          >
            <Play size={16} />
            {iniciando ? "Iniciando…" : "Iniciar consulta"}
          </button>
        )}
        {!consultaAtiva && podeFinalizar && (
          <button
            type="button"
            onClick={onFinalizar}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white text-sm font-medium"
            style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
          >
            <CheckCircle2 size={16} />
            Finalizar consulta
          </button>
        )}
        {!consultaAtiva && podeExcluir && (
          <button
            type="button"
            onClick={onExcluir}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            <Trash2 size={16} />
            Excluir
          </button>
        )}
      </div>
    </div>
  );
}
