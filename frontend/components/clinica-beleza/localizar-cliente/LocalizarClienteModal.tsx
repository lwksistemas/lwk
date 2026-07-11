"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, Loader2, Search, X } from "lucide-react";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { entityName } from "@/lib/clinica-beleza-entities";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { formatConsultaListDate } from "@/components/clinica-beleza/consultas-page/consultas-page-utils";
import {
  useLocalizarClienteModal,
  type LocalizarClienteMode,
} from "./useLocalizarClienteModal";

export type LocalizarClienteModalProps = {
  open: boolean;
  mode: LocalizarClienteMode;
  onClose: () => void;
  /** Clientes: abre edição. */
  onSelectPatient?: (patient: PatientQuickOption) => void;
  /** Consultas: abre detalhe da consulta. */
  onSelectConsulta?: (consulta: Consulta) => void;
};

function patientSubtitle(p: PatientQuickOption): string {
  const parts: string[] = [];
  const tel = p.telefone || p.phone;
  if (tel) parts.push(formatTelefone(tel));
  if (p.cpf) parts.push(formatCpf(p.cpf));
  if (p.email) parts.push(p.email);
  return parts.join(" · ") || "Sem telefone/CPF/e-mail";
}

export function LocalizarClienteModal({
  open,
  mode,
  onClose,
  onSelectPatient,
  onSelectConsulta,
}: LocalizarClienteModalProps) {
  const [mounted, setMounted] = useState(false);
  const {
    query,
    setQuery,
    searching,
    resultados,
    paciente,
    historico,
    loadingHistorico,
    erroHistorico,
    selecionarPaciente,
    voltarBusca,
  } = useLocalizarClienteModal(open, mode);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || !mounted) return null;

  const showingHistorico = mode === "historico" && paciente != null;
  const title = showingHistorico
    ? `Consultas de ${entityName(paciente)}`
    : mode === "edit"
      ? "Localizar cliente para editar"
      : "Localizar cliente — histórico";
  const hint =
    mode === "edit"
      ? "Busque por nome, CPF, telefone ou e-mail e clique para editar o cadastro."
      : showingHistorico
        ? "Clique em uma consulta para ver o histórico completo."
        : "Busque por nome, CPF, telefone ou e-mail e veja todas as consultas do cliente.";

  const handlePatientClick = async (p: PatientQuickOption) => {
    if (mode === "edit") {
      onSelectPatient?.(p);
      onClose();
      return;
    }
    await selecionarPaciente(p);
  };

  const modal = (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal
        aria-label={title}
      >
        <div className="flex items-start justify-between gap-3 p-5 border-b border-gray-200 dark:border-neutral-700">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              {showingHistorico ? (
                <button
                  type="button"
                  onClick={voltarBusca}
                  className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800"
                  aria-label="Voltar à busca"
                >
                  <ArrowLeft size={18} />
                </button>
              ) : (
                <Search size={18} style={{ color: "var(--cb-primary, #8B3D52)" }} />
              )}
              <span className="truncate">{title}</span>
            </h2>
            <p className="text-sm text-gray-500 mt-1">{hint}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 shrink-0"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-5 flex flex-col gap-3 min-h-0 flex-1 overflow-hidden">
          {!showingHistorico && (
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
              />
              <input
                type="search"
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Nome, CPF, telefone ou e-mail"
                className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
              />
            </div>
          )}

          <div className="overflow-y-auto flex-1 min-h-[12rem] -mx-1 px-1">
            {showingHistorico ? (
              loadingHistorico ? (
                <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Carregando consultas...
                </div>
              ) : erroHistorico ? (
                <p className="text-sm text-red-600 dark:text-red-400 py-8 text-center">{erroHistorico}</p>
              ) : historico.length === 0 ? (
                <p className="text-sm text-gray-500 py-8 text-center">
                  Nenhuma consulta encontrada para este cliente.
                </p>
              ) : (
                <ul className="space-y-2">
                  {historico.map((c) => {
                    const statusColors =
                      CLINICA_CONSULTA_STATUS_COLORS[c.status] ||
                      CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;
                    return (
                      <li key={c.id}>
                        <button
                          type="button"
                          onClick={() => {
                            onSelectConsulta?.(c);
                            onClose();
                          }}
                          className="w-full text-left rounded-lg border border-gray-200 dark:border-neutral-700 p-3 hover:border-gray-400 dark:hover:border-neutral-500 hover:bg-gray-50 dark:hover:bg-neutral-800/80 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                {c.procedure_name || "Consulta"}
                              </p>
                              <p className="text-xs text-gray-500 mt-0.5">
                                {formatConsultaListDate(c.data_inicio)}
                                {c.professional_name ? ` · ${c.professional_name}` : ""}
                              </p>
                            </div>
                            <span
                              className={`text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full shrink-0 ${statusColors.bg} ${statusColors.text}`}
                            >
                              {CLINICA_CONSULTA_STATUS_LABEL[c.status] || c.status}
                            </span>
                          </div>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )
            ) : searching ? (
              <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                Buscando...
              </div>
            ) : query.trim().length < 1 ? (
              <p className="text-sm text-gray-500 py-8 text-center">
                Digite para localizar o cliente.
              </p>
            ) : resultados.length === 0 ? (
              <p className="text-sm text-gray-500 py-8 text-center">Nenhum cliente encontrado.</p>
            ) : (
              <ul className="space-y-1">
                {resultados.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => void handlePatientClick(p)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-neutral-800 text-left transition-colors"
                    >
                      <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {entityName(p)}
                        </p>
                        <p className="text-xs text-gray-500 truncate">{patientSubtitle(p)}</p>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
