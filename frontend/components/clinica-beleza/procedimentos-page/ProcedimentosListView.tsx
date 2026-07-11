"use client";

import { Pencil, Stethoscope, Trash2 } from "lucide-react";
import {
  entityName,
  procedureCategoria,
} from "@/lib/clinica-beleza-entities";
import { procedureCategoriaLabel } from "@/lib/clinica-beleza-categories";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import type { Procedure } from "./procedimentos-page-types";

interface ProcedimentosListViewProps {
  slug: string;
  title: string;
  subtitle: string;
  backHref?: string;
  relatedLinks: { label: string; href: string }[];
  moduleKey: string;
  showAllCategories: boolean;
  hiddenByCategoryCount: number;
  activeList: Procedure[];
  filteredList: Procedure[];
  convenios: ConvenioItem[];
  loading: boolean;
  matrixLoading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  precoCelula: (procId: number, convId: number) => string;
  /** Quando true, o header já foi renderizado pelo parent (grade → lista). */
  hideHeader?: boolean;
  onToggleShowAll: () => void;
  onNew: () => void;
  onEdit: (id: number) => void;
  onExclude: (p: Procedure) => void;
  onPageChange: (page: number) => void;
}

export function ProcedimentosListView({
  slug,
  title,
  subtitle,
  backHref,
  relatedLinks,
  moduleKey,
  showAllCategories,
  hiddenByCategoryCount,
  activeList,
  filteredList,
  convenios,
  loading,
  matrixLoading,
  page,
  totalPages,
  totalCount,
  pageSize,
  precoCelula,
  hideHeader = false,
  onToggleShowAll,
  onNew,
  onEdit,
  onExclude,
  onPageChange,
}: ProcedimentosListViewProps) {
  return (
    <>
      {!hideHeader && (
        <ClinicaBelezaStandardPageHeader
          title={title}
          subtitle={subtitle}
          backHref={backHref}
          icon={Stethoscope}
          newLabel="Novo Procedimento"
          onNew={onNew}
        />
      )}
      <ClinicaBelezaPageContent>
        {moduleKey && (
          <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
            <span className="px-2 py-1 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200">
              Filtro: {moduleKey === "soroterapia" ? "Soroterapia" : "Estética"}
            </span>
            {hiddenByCategoryCount > 0 && (
              <button
                type="button"
                onClick={onToggleShowAll}
                className="text-purple-700 dark:text-purple-300 underline"
              >
                {showAllCategories
                  ? "Mostrar só deste módulo"
                  : `Mostrar todos (${activeList.length} cadastrados)`}
              </button>
            )}
          </div>
        )}

        {loading || matrixLoading ? (
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        ) : filteredList.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            {activeList.length === 0 ? (
              <>
                Nenhum procedimento cadastrado. Clique em <strong>Novo Procedimento</strong> para começar.
              </>
            ) : (
              <>Nenhum procedimento nesta categoria.</>
            )}
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[480px]">
                <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
                  <tr>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold sticky left-0 bg-gray-50 dark:bg-neutral-900/80 z-10">
                      Procedimento
                    </th>
                    {convenios.map((c) => (
                      <th
                        key={c.id}
                        className="text-left px-4 md:px-6 py-3.5 font-semibold whitespace-nowrap text-xs"
                        title={c.nome}
                      >
                        {c.nome}
                      </th>
                    ))}
                    <th className="text-right px-4 md:px-6 py-3.5 font-semibold w-24">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredList.map((p) => (
                    <tr
                      key={p.id}
                      className="border-t border-gray-100 dark:border-neutral-700/80 hover:bg-[#F5E6EA]/30 dark:hover:bg-neutral-700/20 cursor-pointer"
                      onClick={() => onEdit(p.id)}
                    >
                      <td className="px-4 md:px-6 py-3.5 font-medium text-gray-800 dark:text-gray-200 sticky left-0 bg-white/90 dark:bg-neutral-800/90">
                        <span>{entityName(p)}</span>
                        {procedureCategoria(p) ? (
                          <span className="block text-xs font-normal text-gray-500 dark:text-gray-400 mt-0.5">
                            {procedureCategoriaLabel(procedureCategoria(p))}
                          </span>
                        ) : null}
                      </td>
                      {convenios.map((c) => (
                        <td
                          key={c.id}
                          className="px-4 md:px-6 py-3.5 text-gray-600 dark:text-gray-400 whitespace-nowrap"
                        >
                          {precoCelula(p.id, c.id)}
                        </td>
                      ))}
                      <td className="px-4 md:px-6 py-3.5" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => onEdit(p.id)}
                            className="p-2 text-purple-600 hover:bg-purple-50 rounded"
                            title="Editar"
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => onExclude(p)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded"
                            title="Desativar"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount}
              pageSize={pageSize}
              loading={loading}
              onPageChange={onPageChange}
              itemLabel="procedimentos"
            />
          </ClinicaBelezaPanel>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>
    </>
  );
}
