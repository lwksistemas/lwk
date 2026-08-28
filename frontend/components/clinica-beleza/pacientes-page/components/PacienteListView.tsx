"use client";

import { BookOpen, ChevronRight, Pencil, Trash2 } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import {
  entityEmail,
  entityName,
  entityPhone,
  patientCpf,
} from "@/lib/clinica-beleza-entities";
import { formatTelefone, formatCpf } from "@/lib/format-br";
import { CONVENIO_PARTICULAR_LABEL } from "@/lib/convenio-precos";
import type { Patient } from "../lib/paciente-form-utils";

export interface PacienteListViewProps {
  list: Patient[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onEdit: (patient: Patient) => void;
  onExclude: (patient: Patient) => void;
  onVerProntuario: (patient: Patient) => void;
}

function RowActions({
  patient,
  onEdit,
  onExclude,
  onVerProntuario,
  showChevron,
}: {
  patient: Patient;
  onEdit: (patient: Patient) => void;
  onExclude: (patient: Patient) => void;
  onVerProntuario: (patient: Patient) => void;
  showChevron?: boolean;
}) {
  return (
    <div className="flex justify-end gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
      {patient.id >= 0 && (
        <button
          type="button"
          onClick={() => onVerProntuario(patient)}
          className="p-2 rounded-lg hover:bg-[#F5E6EA] dark:hover:bg-neutral-600 transition-colors touch-manipulation"
          style={{ color: "var(--cb-primary, #8B3D52)" }}
          title="Ver prontuário"
          aria-label="Ver prontuário"
        >
          <BookOpen size={18} />
        </button>
      )}
      <button
        type="button"
        onClick={() => onEdit(patient)}
        className="p-2 rounded-lg hover:bg-[#F5E6EA] dark:hover:bg-neutral-600 transition-colors touch-manipulation"
        style={{ color: "var(--cb-primary, #8B3D52)" }}
        title="Editar"
        aria-label="Editar cliente"
      >
        <Pencil size={18} />
      </button>
      {patient.id >= 0 && (
        <button
          type="button"
          onClick={() => onExclude(patient)}
          className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg touch-manipulation"
          title="Desativar"
          aria-label="Desativar cliente"
        >
          <Trash2 size={18} />
        </button>
      )}
      {showChevron ? (
        <ChevronRight size={18} className="text-gray-400 ml-1 hidden md:inline self-center" />
      ) : null}
    </div>
  );
}

export function PacienteListView({
  list,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  onPageChange,
  onEdit,
  onExclude,
  onVerProntuario,
}: PacienteListViewProps) {
  if (loading) {
    return (
      <div className="text-center py-20 text-gray-500 dark:text-gray-400">
        Carregando...
      </div>
    );
  }

  const empty = (
    <div className="p-12 text-center text-gray-500 dark:text-gray-400">
      Nenhum cliente cadastrado. Clique em &quot;Novo Cliente&quot; para começar.
    </div>
  );

  return (
    <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full max-w-full min-w-0">
      {list.length === 0 ? (
        empty
      ) : (
        <>
          {/* Mobile: cards — evita tabela empurrando o layout */}
          <ul className="sm:hidden divide-y divide-gray-100 dark:divide-neutral-700">
            {list.map((p) => (
              <li key={p.id}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => onEdit(p)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onEdit(p);
                    }
                  }}
                  className="w-full flex items-center gap-3 px-3 py-3 text-left touch-manipulation active:bg-gray-50 dark:active:bg-neutral-700/40 min-w-0 cursor-pointer"
                >
                  <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
                      {entityName(p)}
                      {p.id < 0 ? (
                        <span className="text-xs text-amber-600 dark:text-amber-400 font-normal ml-1">
                          (offline)
                        </span>
                      ) : null}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                      {formatTelefone(entityPhone(p)) || "Sem telefone"}
                    </p>
                  </div>
                  <RowActions
                    patient={p}
                    onEdit={onEdit}
                    onExclude={onExclude}
                    onVerProntuario={onVerProntuario}
                  />
                </div>
              </li>
            ))}
          </ul>

          {/* Desktop/tablet: tabela */}
          <div className="hidden sm:block max-w-full min-w-0">
            <EntityListTable
              rows={list}
              rowKey={(p) => p.id}
              onRowClick={onEdit}
              columns={[
                {
                  key: "avatar",
                  header: "",
                  className: "w-12",
                  render: (p) => (
                    <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                  ),
                },
                {
                  key: "nome",
                  header: "Nome",
                  className: "min-w-0 max-w-[14rem] md:max-w-none",
                  render: (p) => (
                    <div className="flex items-center gap-2 font-medium text-gray-900 dark:text-gray-100 min-w-0">
                      <span className="truncate">{entityName(p)}</span>
                      {p.id < 0 && (
                        <span className="text-xs text-amber-600 dark:text-amber-400 font-normal shrink-0">
                          (offline)
                        </span>
                      )}
                    </div>
                  ),
                },
                {
                  key: "telefone",
                  header: "Telefone",
                  className: "whitespace-nowrap",
                  render: (p) => (
                    <span className="text-gray-700 dark:text-gray-300">
                      {formatTelefone(entityPhone(p)) || "—"}
                    </span>
                  ),
                },
                {
                  key: "email",
                  header: "E-mail",
                  className: "hidden md:table-cell max-w-[12rem]",
                  render: (p) => (
                    <span className="text-gray-700 dark:text-gray-300 truncate block">
                      {entityEmail(p) || "—"}
                    </span>
                  ),
                },
                {
                  key: "cpf",
                  header: "CPF",
                  className: "hidden lg:table-cell whitespace-nowrap",
                  render: (p) => (
                    <span className="text-gray-700 dark:text-gray-300">
                      {formatCpf(patientCpf(p) || "") || "—"}
                    </span>
                  ),
                },
                {
                  key: "convenio",
                  header: "Convênio",
                  className: "hidden lg:table-cell",
                  render: (p) => (
                    <span className="text-gray-700 dark:text-gray-300 truncate block max-w-[8rem]">
                      {p.convenio_name || CONVENIO_PARTICULAR_LABEL}
                    </span>
                  ),
                },
                {
                  key: "acoes",
                  header: "Ações",
                  className: "w-36",
                  render: (p) => (
                    <RowActions
                      patient={p}
                      onEdit={onEdit}
                      onExclude={onExclude}
                      onVerProntuario={onVerProntuario}
                      showChevron
                    />
                  ),
                },
              ]}
            />
          </div>
        </>
      )}

      <div className="px-3 sm:px-0">
        <EntityListLoadMore
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          loading={loading}
          onPageChange={onPageChange}
          itemLabel="pacientes"
        />
      </div>
    </div>
  );
}
