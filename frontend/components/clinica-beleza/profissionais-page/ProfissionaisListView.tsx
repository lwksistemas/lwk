"use client";

import { Clock, Pencil, Timer, Trash2 } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { entityName, entityPhone, professionalSpecialty, type ClinicaProfessional } from "@/lib/clinica-beleza-entities";

interface ProfissionaisListViewProps {
  rows: ClinicaProfessional[];
  loading: boolean;
  page: number;
  totalPages: number;
  pageSize: number;
  totalCount: number;
  onPageChange: (page: number) => void;
  onEdit: (id: number) => void;
  onExclude: (p: ClinicaProfessional) => void;
  onToggleProfissional: (p: ClinicaProfessional) => void;
  onHorarios: (p: ClinicaProfessional) => void;
  onTempoConsulta: (p: ClinicaProfessional) => void;
}

export function ProfissionaisListView({
  rows,
  loading,
  page,
  totalPages,
  pageSize,
  totalCount,
  onPageChange,
  onEdit,
  onExclude,
  onToggleProfissional,
  onHorarios,
  onTempoConsulta,
}: ProfissionaisListViewProps) {
  if (loading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>;
  }

  return (
    <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl shadow overflow-hidden">
      <EntityListTable
        rows={rows}
        rowKey={(p) => p.id}
        emptyMessage={
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            Nenhum profissional cadastrado. Clique em &quot;Novo Profissional&quot; para começar.
          </div>
        }
        columns={[
          {
            key: "nome",
            header: "Nome",
            render: (p) => (
              <span className="font-medium text-gray-800 dark:text-gray-200">{entityName(p)}</span>
            ),
          },
          {
            key: "especialidade",
            header: "Especialidade",
            render: (p) => (
              <span className="text-gray-700 dark:text-gray-300">{professionalSpecialty(p) || "—"}</span>
            ),
          },
          {
            key: "telefone",
            header: "Telefone",
            className: "hidden md:table-cell",
            render: (p) => (
              <span className="text-gray-700 dark:text-gray-300">{entityPhone(p) || "—"}</span>
            ),
          },
          {
            key: "acoes",
            header: "Ações",
            render: (p) => (
              <div className="flex flex-wrap gap-1.5" onClick={(e) => e.stopPropagation()}>
                {p.is_administrador_vinculado && (
                  <label
                    className="inline-flex items-center gap-2 cursor-pointer select-none"
                    title={
                      (p.is_profissional ?? true)
                        ? "Desmarcar para ficar só como administrador"
                        : "Marcar para atuar também como profissional"
                    }
                  >
                    <input
                      type="checkbox"
                      checked={p.is_profissional ?? true}
                      onChange={() => onToggleProfissional(p)}
                      className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500 dark:border-neutral-600 dark:bg-neutral-700"
                    />
                  </label>
                )}
                {(p.is_profissional ?? true) && (
                  <>
                    <button
                      type="button"
                      onClick={() => onHorarios(p)}
                      className="p-2 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded"
                      title="Dias e horários de trabalho"
                    >
                      <Clock size={18} />
                    </button>
                    <button
                      type="button"
                      onClick={() => onTempoConsulta(p)}
                      className="p-2 text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/30 rounded"
                      title="Tempo da consulta (min)"
                    >
                      <Timer size={18} />
                    </button>
                  </>
                )}
                <button
                  type="button"
                  onClick={() => onEdit(p.id)}
                  className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                  title="Editar"
                >
                  <Pencil size={18} />
                </button>
                {!p.is_owner && (
                  <button
                    type="button"
                    onClick={() => onExclude(p)}
                    className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                    title="Desativar"
                  >
                    <Trash2 size={18} />
                  </button>
                )}
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
        itemLabel="profissionais"
      />
    </div>
  );
}
