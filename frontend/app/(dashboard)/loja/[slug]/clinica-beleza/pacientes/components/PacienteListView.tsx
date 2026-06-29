"use client";

import { ChevronRight, Pencil, Trash2 } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
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
}: PacienteListViewProps) {
  if (loading) {
    return (
      <div className="text-center py-20 text-gray-500 dark:text-gray-400">
        Carregando...
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full">
      <EntityListTable
        rows={list}
        rowKey={(p) => p.id}
        onRowClick={onEdit}
        emptyMessage={
          <div className="p-12 text-center text-gray-500 dark:text-gray-400">
            Nenhum cliente cadastrado. Clique em &quot;Novo Cliente&quot; para começar.
          </div>
        }
        columns={[
          {
            key: "avatar",
            header: "",
            render: (p) => (
              <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
            ),
          },
          {
            key: "nome",
            header: "Nome",
            render: (p) => (
              <div className="flex items-center gap-2 font-medium text-gray-900 dark:text-gray-100">
                {entityName(p)}
                {p.id < 0 && (
                  <span className="text-xs text-amber-600 dark:text-amber-400 font-normal">
                    (offline)
                  </span>
                )}
              </div>
            ),
          },
          {
            key: "telefone",
            header: "Telefone",
            render: (p) => (
              <span className="text-gray-700 dark:text-gray-300">
                {formatTelefone(entityPhone(p)) || "—"}
              </span>
            ),
          },
          {
            key: "email",
            header: "E-mail",
            className: "hidden sm:table-cell",
            render: (p) => (
              <span className="text-gray-700 dark:text-gray-300">
                {entityEmail(p) || "—"}
              </span>
            ),
          },
          {
            key: "cpf",
            header: "CPF",
            className: "hidden lg:table-cell",
            render: (p) => (
              <span className="text-gray-700 dark:text-gray-300">
                {formatCpf(patientCpf(p) || "") || "—"}
              </span>
            ),
          },
          {
            key: "convenio",
            header: "Convênio",
            className: "hidden md:table-cell",
            render: (p) => (
              <span className="text-gray-700 dark:text-gray-300">
                {p.convenio_name || CONVENIO_PARTICULAR_LABEL}
              </span>
            ),
          },
          {
            key: "acoes",
            header: "Ações",
            render: (p) => (
              <div
                className="flex justify-end gap-1"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  type="button"
                  onClick={() => onEdit(p)}
                  className="p-2 rounded-lg hover:bg-[#F5E6EA] dark:hover:bg-neutral-600 transition-colors"
                  style={{ color: CLINICA_BELEZA_PRIMARY }}
                  title="Editar"
                >
                  <Pencil size={18} />
                </button>
                {p.id >= 0 && (
                  <button
                    type="button"
                    onClick={() => onExclude(p)}
                    className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                    title="Desativar"
                  >
                    <Trash2 size={18} />
                  </button>
                )}
                <ChevronRight
                  size={18}
                  className="text-gray-400 ml-1 hidden md:inline self-center"
                />
              </div>
            ),
          },
        ]}
      />
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
  );
}
