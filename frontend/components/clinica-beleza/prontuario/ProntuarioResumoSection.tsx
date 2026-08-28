"use client";

import { CalendarDays, CheckCircle2, Play, Trash2 } from "lucide-react";
import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ConsultaPagamentoButton } from "@/components/clinica-beleza/consultas/ConsultaPagamentoButton";
import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { formatConsultaListDate } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  buildProntuarioConsultasResumo,
  consultaProcedimentoLabel,
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
    <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-medium ${colors.bg} ${colors.text}`}>
      {CLINICA_CONSULTA_STATUS_LABEL[status] || status}
    </span>
  );
}

function ConsultaMeta({ consulta }: { consulta: Consulta }) {
  return (
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
  );
}

function ConsultaAtualCard({
  consulta,
  todas,
  iniciando,
  excluindo,
  recebendo,
  onAbrir,
  onIniciar,
  onReceber,
  onExcluir,
}: {
  consulta: Consulta;
  todas: Consulta[];
  iniciando: boolean;
  excluindo: boolean;
  recebendo: boolean;
  onAbrir: (id: number) => void;
  onIniciar: (consulta: Consulta) => void;
  onReceber: (consulta: Consulta) => void;
  onExcluir: (consulta: Consulta) => void;
}) {
  const acoes = prontuarioConsultaAtualAcoes(consulta, todas);
  return (
    <div className="flex flex-col gap-3 p-4 rounded-xl border border-[var(--cb-primary,#8B3D52)]/40 bg-[var(--cb-primary,#8B3D52)]/5">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <ConsultaMeta consulta={consulta} />
        <div className="shrink-0 flex flex-wrap items-center gap-2">
          {acoes.podeExcluir && (
            <button
              type="button"
              onClick={() => onExcluir(consulta)}
              disabled={excluindo || iniciando}
              className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
            >
              <Trash2 size={14} />
              {excluindo ? "Excluindo…" : "Excluir"}
            </button>
          )}
          <ConsultaPagamentoButton
            consulta={consulta}
            onReceber={onReceber}
            size="md"
            loading={recebendo}
          />
          {acoes.podeIniciar && (
            <button
              type="button"
              onClick={() => onIniciar(consulta)}
              disabled={iniciando || excluindo}
              className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              <Play size={14} />
              {iniciando ? "Iniciando…" : "Iniciar a consulta"}
            </button>
          )}
          {acoes.mostrarContinuar && (
            <button
              type="button"
              onClick={() => onAbrir(consulta.id)}
              className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              <Play size={14} />
              Continuar consulta
            </button>
          )}
        </div>
      </div>
      {acoes.bloqueadaPorOutraEmAndamento && (
        <p className="text-xs text-amber-700 dark:text-amber-400">
          Já existe consulta em andamento para este paciente. Finalize-a antes de iniciar outra.
        </p>
      )}
    </div>
  );
}

function ConsultaFinalizadaCard({
  consulta,
  onAbrir,
}: {
  consulta: Consulta;
  onAbrir: (id: number) => void;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 rounded-xl border border-gray-200 dark:border-neutral-700 bg-white/60 dark:bg-neutral-800/40">
      <ConsultaMeta consulta={consulta} />
      <button
        type="button"
        onClick={() => onAbrir(consulta.id)}
        className="shrink-0 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white"
        style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
      >
        <CalendarDays size={14} />
        Abrir consulta
      </button>
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
      {atuais.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
            <Play size={16} style={{ color: "var(--cb-primary, #8B3D52)" }} />
            Consulta atual
          </h2>
          <div className="space-y-3">
            {atuais.map((c) => (
              <ConsultaAtualCard
                key={c.id}
                consulta={c}
                todas={consultas}
                iniciando={iniciandoId === c.id}
                excluindo={excluindoId === c.id}
                recebendo={recebendoId === c.id}
                onAbrir={onAbrirConsulta}
                onIniciar={onIniciarConsulta}
                onReceber={onReceberConsulta}
                onExcluir={onExcluirConsulta}
              />
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
              <ConsultaFinalizadaCard key={c.id} consulta={c} onAbrir={onAbrirConsulta} />
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
