"use client";

import { ClipboardList, Pencil, Trash2 } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import type { Protocol } from "./protocolos-page-types";

interface ProtocolosListViewProps {
  slug: string;
  title: string;
  subtitle: string;
  backHref?: string;
  relatedLinks: { label: string; href: string }[];
  list: Protocol[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  onNew: () => void;
  onEdit: (id: number) => void;
  onExclude: (p: Protocol) => void;
  onPageChange: (page: number) => void;
}

export function ProtocolosListView({
  slug,
  title,
  subtitle,
  backHref,
  relatedLinks,
  list,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  onNew,
  onEdit,
  onExclude,
  onPageChange,
}: ProtocolosListViewProps) {
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={subtitle}
        backHref={backHref}
        icon={ClipboardList}
        newLabel="Novo protocolo"
        onNew={onNew}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <p className="text-center py-16 text-gray-500">Carregando...</p>
        ) : list.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            Nenhum protocolo cadastrado. Clique em <strong>Novo protocolo</strong> para começar.
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel>
            <EntityListTable
              rows={list}
              rowKey={(p) => p.id}
              onRowClick={(p) => onEdit(p.id)}
              columns={[
                {
                  key: "nome",
                  header: "Protocolo",
                  render: (p) => (
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{p.nome}</p>
                      <p className="text-sm text-gray-500 mt-0.5">
                        {p.procedure_name}
                        {p.procedure_categoria ? ` · ${p.procedure_categoria}` : ""}
                      </p>
                    </div>
                  ),
                },
                {
                  key: "tempo",
                  header: "Duração",
                  className: "hidden sm:table-cell",
                  render: (p) => <span className="text-gray-600">{p.tempo_estimado} min</span>,
                },
                {
                  key: "desc",
                  header: "Descrição",
                  className: "hidden md:table-cell",
                  render: (p) => (
                    <span className="text-sm text-gray-500 line-clamp-1">{p.descricao || "—"}</span>
                  ),
                },
              ]}
              trailingCell={(p) => (
                <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => onEdit(p.id)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700"
                    title="Editar"
                  >
                    <Pencil size={16} style={{ color: 'var(--cb-primary, #8B3D52)' }} />
                  </button>
                  <button
                    type="button"
                    onClick={() => onExclude(p)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                    title="Desativar"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            />
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount}
              pageSize={pageSize}
              loading={loading}
              onPageChange={onPageChange}
              itemLabel="protocolos"
            />
          </ClinicaBelezaPanel>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>
    </>
  );
}
