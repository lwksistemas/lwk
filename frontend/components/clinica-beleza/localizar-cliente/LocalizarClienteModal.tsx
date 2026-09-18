"use client";

import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { Loader2, Search, X } from "lucide-react";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { entityName } from "@/lib/clinica-beleza-entities";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { isLocalizarPainelExpandido, splitPatientMatch } from "./localizar-cliente-utils";
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

function HighlightedName({ text, query }: { text: string; query: string }) {
  const parts = splitPatientMatch(text, query);
  return (
    <>
      {parts.map((part, i) =>
        part.hit ? (
          <mark
            key={`${part.text}-${i}`}
            className="bg-transparent p-0 font-semibold"
            style={{ color: "var(--cb-primary, #8B3D52)" }}
          >
            {part.text}
          </mark>
        ) : (
          <span key={`${part.text}-${i}`}>{part.text}</span>
        ),
      )}
    </>
  );
}

export function LocalizarClienteModal({
  open,
  mode,
  onClose,
  onSelectPatient,
}: LocalizarClienteModalProps) {
  const [mounted, setMounted] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const listRef = useRef<HTMLUListElement>(null);
  const { query, setQuery, searching, resultados } = useLocalizarClienteModal(open);
  const expandido = isLocalizarPainelExpandido(query);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, resultados]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    const el = listRef.current?.querySelector("[data-active='true']");
    el?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  if (!open || !mounted) return null;

  const title =
    mode === "edit" ? "Localizar cliente para editar" : "Localizar cliente — histórico";
  const hint =
    mode === "edit"
      ? "Ao digitar, os cadastros aparecem. Clique para editar."
      : "Ao digitar, os cadastros aparecem. Clique para ver as consultas do cliente.";
  const acao = mode === "edit" ? "Editar" : "Consultas";
  const lastIndex = Math.max(resultados.length - 1, 0);

  const escolher = (p: PatientQuickOption) => {
    onSelectPatient(p);
    onClose();
  };

  const onInputKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown" || e.key === "ArrowRight") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, lastIndex));
    } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const p = resultados[activeIndex];
      if (p) escolher(p);
    }
  };

  const mostrarLista = resultados.length > 0;
  const mostrarVazio = expandido && !searching && resultados.length === 0;

  const overlay = (
    <div
      className="fixed inset-0 z-[200] flex items-start justify-center bg-black/40 px-3 pt-20 sm:pt-24"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl border border-gray-200 dark:border-neutral-700 w-full max-w-xl max-h-[min(70vh,32rem)] flex flex-col p-3"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal
        aria-label={title}
      >
        <div className="flex items-center justify-between gap-2 px-1 pb-2 shrink-0">
          <div className="min-w-0">
            <p className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">{title}</p>
            {expandido ? <p className="text-xs text-gray-500 mt-0.5 truncate">{hint}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 shrink-0"
            aria-label="Fechar"
          >
            <X size={16} />
          </button>
        </div>

        <form
          className={`flex flex-col gap-2 min-h-0 ${expandido ? "flex-1 overflow-hidden" : ""}`}
          autoComplete="off"
          onSubmit={(e) => e.preventDefault()}
        >
          <div className="relative shrink-0">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <input
              type="text"
              name="clinica-localizar-cliente"
              autoFocus
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck={false}
              data-lpignore="true"
              data-1p-ignore="true"
              data-form-type="other"
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={mostrarLista}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onInputKeyDown}
              placeholder="Digite o nome, CPF, telefone ou e-mail"
              className="w-full pl-9 pr-10 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 outline-none focus:ring-2 focus:ring-[var(--cb-primary,#8B3D52)]/30 focus:border-[var(--cb-primary,#8B3D52)]"
            />
            {searching ? (
              <Loader2 className="absolute right-9 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-gray-400" />
            ) : null}
            {query ? (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                aria-label="Limpar busca"
              >
                <X size={14} />
              </button>
            ) : null}
          </div>

          {expandido ? (
            <div className="overflow-y-auto min-h-0 flex-1">
              {mostrarVazio ? (
                <p className="text-sm text-gray-500 py-3 text-center">
                  Nenhum cliente encontrado para “{query.trim()}”.
                </p>
              ) : mostrarLista ? (
                <>
                  <p className="text-xs text-gray-500 px-1 pb-1.5">
                    {resultados.length} cliente{resultados.length === 1 ? "" : "s"} · setas e Enter
                  </p>
                  <ul ref={listRef} className="flex flex-col gap-0.5" role="listbox">
                    {resultados.map((p, index) => {
                      const ativo = index === activeIndex;
                      return (
                        <li key={p.id} role="option" aria-selected={ativo} data-active={ativo ? "true" : "false"}>
                          <button
                            type="button"
                            onClick={() => escolher(p)}
                            onMouseEnter={() => setActiveIndex(index)}
                            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                              ativo
                                ? "bg-[#F5E6EA]/80 dark:bg-neutral-800"
                                : "hover:bg-gray-50 dark:hover:bg-neutral-800"
                            }`}
                          >
                            <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                            <div className="min-w-0 flex-1">
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                <HighlightedName text={entityName(p)} query={query} />
                              </p>
                              <p className="text-xs text-gray-500 truncate">{patientSubtitle(p)}</p>
                            </div>
                            <span
                              className="shrink-0 text-[11px] font-medium"
                              style={{ color: "var(--cb-primary, #8B3D52)" }}
                            >
                              {acao}
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </>
              ) : searching ? (
                <div className="flex items-center justify-center gap-2 py-3 text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Buscando...
                </div>
              ) : null}
            </div>
          ) : null}
        </form>
      </div>
    </div>
  );

  return createPortal(overlay, document.body);
}
