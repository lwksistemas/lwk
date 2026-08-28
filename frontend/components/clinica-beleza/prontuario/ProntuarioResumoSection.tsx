"use client";

import { CalendarDays, CheckCircle2, Play } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatConsultaListDate } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  buildProntuarioConsultasResumo,
  consultaAcaoLabel,
  consultaProcedimentoLabel,
} from "./prontuario-consultas-utils";

interface ProntuarioResumoSectionProps {
  consultas: Consulta[];
  loading: boolean;
  onAbrirConsulta: (consultaId: number) => void;
}

function StatusBadge({ status }: { status: string }) {
  const colors = CLINICA_CONSULTA_STATUS_COLORS[status] ?? CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-medium ${colors.bg} ${colors.text}`}>
      {CLINICA_CONSULTA_STATUS_LABEL[status] || status}
    </span>
  );
}

function ConsultaCard({
  consulta,
  destaque,
  onAbrir,
}: {
  consulta: Consulta;
  destaque?: boolean;
  onAbrir: (id: number) => void;
}) {
  const acao = consultaAcaoLabel(consulta.status);
  return (
    <div
      className={`flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl border ${
        destaque
          ? "border-[var(--cb-primary,#8B3D52)]/40 bg-[var(--cb-primary,#8B3D52)]/5"
          : "border-gray-200 dark:border-neutral-700 bg-white/60 dark:bg-neutral-800/40"
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          {consulta.numero ? (
            <span className="text-xs font-semibold text-gray-500">#{consulta.numero}</span>
          ) : null}
          <StatusBadge status={consulta.status} />
        </div>
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
          {consultaProcedimentoLabel(consulta)}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          {consulta.professional_name ? `${consulta.professional_name} · ` : ""}
          {formatConsultaListDate(consulta.data_inicio || consulta.appointment_date)}
        </p>
      </div>
      <button
        type="button"
        onClick={() => onAbrir(consulta.id)}
        className="shrink-0 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white"
        style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
      >
        {destaque ? <Play size={14} /> : <CalendarDays size={14} />}
        {acao}
      </button>
    </div>
  );
}

export function ProntuarioResumoSection({
  consultas,
  loading,
  onAbrirConsulta,
}: ProntuarioResumoSectionProps) {
  if (loading) {
    return (
      <div className="text-center py-16 text-gray-500 dark:text-gray-400 text-sm">
        Carregando consultas...
      </div>
    );
  }

  const { atuais, finalizadas, total } = buildProntuarioConsultasResumo(consultas);

  if (total === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-sm text-gray-500 dark:text-gray-400">
        Nenhuma consulta ainda. Agende na Agenda para iniciar o atendimento.
        Fotos e demais registros entram somente dentro da consulta.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 max-w-md">
        <ClinicaBelezaPanel className="p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Consulta atual</p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-1">{atuais.length}</p>
        </ClinicaBelezaPanel>
        <ClinicaBelezaPanel className="p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Finalizadas</p>
          <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mt-1">{finalizadas.length}</p>
        </ClinicaBelezaPanel>
      </div>

      {atuais.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
            <Play size={16} style={{ color: "var(--cb-primary, #8B3D52)" }} />
            Consulta atual
          </h2>
          <div className="space-y-3">
            {atuais.map((c) => (
              <ConsultaCard key={c.id} consulta={c} destaque onAbrir={onAbrirConsulta} />
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600" />
          Consultas finalizadas
        </h2>
        {finalizadas.length === 0 ? (
          <ClinicaBelezaPanel className="p-8 text-center text-sm text-gray-500 dark:text-gray-400">
            Nenhuma consulta finalizada ainda.
          </ClinicaBelezaPanel>
        ) : (
          <div className="space-y-3">
            {finalizadas.map((c) => (
              <ConsultaCard key={c.id} consulta={c} onAbrir={onAbrirConsulta} />
            ))}
          </div>
        )}
      </section>

      <p className="text-xs text-gray-500 dark:text-gray-400">
        Para incluir fotos, evolução ou documentos, abra a consulta atual.
      </p>
    </div>
  );
}
