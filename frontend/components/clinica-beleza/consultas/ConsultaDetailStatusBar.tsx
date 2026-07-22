"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, FileText, Pencil, Play, Trash2 } from "lucide-react";
import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { toUpperCase } from "@/lib/format-br";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
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
  onRefreshConsulta?: () => void;
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
  onRefreshConsulta,
}: ConsultaDetailStatusBarProps) {
  const statusColors =
    CLINICA_CONSULTA_STATUS_COLORS[selected.status] ?? CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;
  const consultaFinalizada = selected.status === "COMPLETED";
  const [editandoLocal, setEditandoLocal] = useState(false);
  const [editandoConvenio, setEditandoConvenio] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [locaisAtendimento, setLocaisAtendimento] = useState<Array<{ id: number; nome: string }>>([]);
  const [convenios, setConvenios] = useState<Array<{ id: number; nome: string }>>([]);

  useEffect(() => {
    if (!consultaFinalizada) return;
    ClinicaBelezaAPI.locaisAtendimento.list().then((data) => {
      setLocaisAtendimento(Array.isArray(data) ? data.map((l: { id: number; nome: string }) => ({ id: l.id, nome: l.nome })) : []);
    }).catch(() => {});
    ClinicaBelezaAPI.convenios.list().then((data) => {
      const items = Array.isArray(data) ? data : (data as { results?: unknown[] })?.results ?? [];
      setConvenios(items.map((c: { id: number; nome: string }) => ({ id: c.id, nome: c.nome })));
    }).catch(() => {});
  }, [consultaFinalizada]);

  const salvarCampo = async (campo: "local_atendimento" | "convenio", valor: number | null) => {
    setSalvando(true);
    try {
      await ClinicaBelezaAPI.consultas.update(selected.id, { [campo]: valor });
      onRefreshConsulta?.();
    } catch { /* silencioso */ }
    finally {
      setSalvando(false);
      setEditandoLocal(false);
      setEditandoConvenio(false);
    }
  };

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
      {selected.local_atendimento_name && !editandoLocal && (
        <span className="inline-flex items-center gap-1">
          Local:{" "}
          <strong className="text-gray-800 dark:text-gray-200 uppercase">
            {toUpperCase(selected.local_atendimento_name)}
          </strong>
          {consultaFinalizada && locaisAtendimento.length > 0 && (
            <button type="button" onClick={() => setEditandoLocal(true)} className="text-gray-400 hover:text-gray-600" title="Editar local">
              <Pencil size={12} />
            </button>
          )}
        </span>
      )}
      {editandoLocal && (
        <span className="inline-flex items-center gap-1">
          Local:{" "}
          <select
            className="text-xs border rounded px-1 py-0.5 dark:bg-neutral-800 dark:border-neutral-600"
            defaultValue={selected.local_atendimento ?? ""}
            disabled={salvando}
            onChange={(e) => {
              const v = e.target.value;
              salvarCampo("local_atendimento", v ? Number(v) : null);
            }}
          >
            <option value="">— Nenhum —</option>
            {locaisAtendimento.map((l) => (
              <option key={l.id} value={l.id}>{l.nome}</option>
            ))}
          </select>
          <button type="button" onClick={() => setEditandoLocal(false)} className="text-xs text-gray-400 hover:text-gray-600">✕</button>
        </span>
      )}
      {!editandoConvenio && (
        <span className="inline-flex items-center gap-1">
          Convênio:{" "}
          <strong className="text-gray-800 dark:text-gray-200 uppercase">
            {toUpperCase(selected.convenio_name || "Particular")}
          </strong>
          {consultaFinalizada && convenios.length > 0 && (
            <button type="button" onClick={() => setEditandoConvenio(true)} className="text-gray-400 hover:text-gray-600" title="Editar convênio">
              <Pencil size={12} />
            </button>
          )}
        </span>
      )}
      {editandoConvenio && (
        <span className="inline-flex items-center gap-1">
          Convênio:{" "}
          <select
            className="text-xs border rounded px-1 py-0.5 dark:bg-neutral-800 dark:border-neutral-600"
            defaultValue={selected.convenio ?? ""}
            disabled={salvando}
            onChange={(e) => {
              const v = e.target.value;
              salvarCampo("convenio", v ? Number(v) : null);
            }}
          >
            <option value="">Particular</option>
            {convenios.map((c) => (
              <option key={c.id} value={c.id}>{c.nome}</option>
            ))}
          </select>
          <button type="button" onClick={() => setEditandoConvenio(false)} className="text-xs text-gray-400 hover:text-gray-600">✕</button>
        </span>
      )}
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
