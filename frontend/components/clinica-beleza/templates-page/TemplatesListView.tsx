"use client";

import { Pencil, Trash2 } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import type { DocumentTemplateItem } from "@/lib/clinica-beleza-api";
import {
  formatTemplateUpdatedAt,
  TEMPLATE_FILTER_TIPO_OPTIONS,
  templateTipoLabel,
} from "./templates-page-utils";

interface TemplatesListViewProps {
  filtroTipo: string;
  onFiltroTipoChange: (value: string) => void;
  templates: DocumentTemplateItem[];
  loading: boolean;
  page: number;
  totalPages: number;
  pageSize: number;
  totalCount: number;
  onPageChange: (page: number) => void;
  onEdit: (t: DocumentTemplateItem) => void;
  onDelete: (t: DocumentTemplateItem) => void;
}

export function TemplatesListView({
  filtroTipo,
  onFiltroTipoChange,
  templates,
  loading,
  page,
  totalPages,
  pageSize,
  totalCount,
  onPageChange,
  onEdit,
  onDelete,
}: TemplatesListViewProps) {
  return (
    <>
      <div className="mb-4 flex items-center gap-3">
        <label className="text-sm text-gray-600 dark:text-gray-400 whitespace-nowrap">Filtrar por tipo:</label>
        <select
          value={filtroTipo}
          onChange={(e) => onFiltroTipoChange(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
        >
          {TEMPLATE_FILTER_TIPO_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
      ) : templates.length === 0 ? (
        <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl p-8 text-center text-gray-500 dark:text-gray-400">
          {filtroTipo
            ? "Nenhum template encontrado para este tipo."
            : 'Nenhum template cadastrado. Clique em "Novo Template" para começar.'}
        </div>
      ) : (
        <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-300">
                <tr>
                  <th className="text-left p-3">Nome</th>
                  <th className="text-left p-3">Tipo</th>
                  <th className="text-left p-3 hidden md:table-cell">Atualizado em</th>
                  <th className="w-28 p-3">Ações</th>
                </tr>
              </thead>
              <tbody>
                {templates.map((t) => (
                  <tr key={t.id} className="border-t border-gray-100 dark:border-neutral-700">
                    <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{t.nome}</td>
                    <td className="p-3 text-gray-700 dark:text-gray-300">
                      <span
                        className="inline-block px-2 py-0.5 text-xs rounded-full"
                        style={{
                          backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 8%, transparent)',
                          color: 'var(--cb-primary, #8B3D52)',
                        }}
                      >
                        {templateTipoLabel(t.tipo)}
                      </span>
                    </td>
                    <td className="p-3 hidden md:table-cell text-gray-700 dark:text-gray-300">
                      {formatTemplateUpdatedAt(t.updated_at)}
                    </td>
                    <td className="p-3">
                      <div className="flex gap-2">
                        <button
                          onClick={() => onEdit(t)}
                          className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                          title="Editar"
                        >
                          <Pencil size={18} />
                        </button>
                        <button
                          onClick={() => onDelete(t)}
                          className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                          title="Desativar"
                        >
                          <Trash2 size={18} />
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
            itemLabel="templates"
          />
        </div>
      )}
    </>
  );
}
