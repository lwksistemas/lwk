"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Loader2, Search, X } from "lucide-react";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { entityName } from "@/lib/clinica-beleza-entities";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import {
  useLocalizarClienteModal,
  type LocalizarClienteMode,
} from "./useLocalizarClienteModal";

export type LocalizarClienteModalProps = {
  open: boolean;
  mode: LocalizarClienteMode;
  onClose: () => void;
  /** Clientes: editar · Consultas: filtrar lista pelo paciente. */
  onSelectPatient: (patient: PatientQuickOption) => void;
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
}: LocalizarClienteModalProps) {
  const [mounted, setMounted] = useState(false);
  const { query, setQuery, searching, resultados } = useLocalizarClienteModal(open);

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

  const title =
    mode === "edit" ? "Localizar cliente para editar" : "Localizar cliente — histórico";
  const hint =
    mode === "edit"
      ? "Busque por nome, CPF, telefone ou e-mail e clique para editar o cadastro."
      : "Busque por nome, CPF, telefone ou e-mail. Ao clicar, a lista de consultas do cliente abre abaixo.";

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
              <Search size={18} style={{ color: "var(--cb-primary, #8B3D52)" }} />
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
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <input
              type="search"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nome, CPF, telefone ou e-mail"
              className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
            />
          </div>

          <div className="overflow-y-auto flex-1 min-h-[12rem] -mx-1 px-1">
            {searching ? (
              <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                Buscando...
              </div>
            ) : query.trim().length < 1 ? (
              <p className="text-sm text-gray-500 py-8 text-center">Digite para localizar o cliente.</p>
            ) : resultados.length === 0 ? (
              <p className="text-sm text-gray-500 py-8 text-center">Nenhum cliente encontrado.</p>
            ) : (
              <ul className="space-y-1">
                {resultados.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => {
                        onSelectPatient(p);
                        onClose();
                      }}
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
