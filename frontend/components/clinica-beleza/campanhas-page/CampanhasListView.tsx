"use client";

import { Megaphone, Pencil, Send, Trash2 } from "lucide-react";
import { CampanhaEnviarModal } from "@/components/clinica-beleza/CampanhaEnviarModal";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  campanhaFoiEnviada,
  formatCampanhaEnvio,
  formatCampanhaVigencia,
} from "./campanhas-page-utils";
import { CampanhaExcluirModal } from "./CampanhaExcluirModal";
import type { Campanha } from "./campanhas-page-types";

interface CampanhasListViewProps {
  list: Campanha[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  enviarCampanha: Campanha | null;
  excluirCampanha: Campanha | null;
  excluindo: boolean;
  onNew: () => void;
  onEdit: (id: number) => void;
  onEnviar: (c: Campanha) => void;
  onExcluir: (c: Campanha) => void;
  onCloseEnviar: () => void;
  onCloseExcluir: () => void;
  onConfirmExcluir: () => void;
  onPageChange: (page: number) => void;
  onSent: () => void;
}

export function CampanhasListView({
  list,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  enviarCampanha,
  excluirCampanha,
  excluindo,
  onNew,
  onEdit,
  onEnviar,
  onExcluir,
  onCloseEnviar,
  onCloseExcluir,
  onConfirmExcluir,
  onPageChange,
  onSent,
}: CampanhasListViewProps) {
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Campanhas de Promoções"
        subtitle="Crie promoções e envie por WhatsApp para os pacientes"
        icon={Megaphone}
        newLabel="Nova Campanha"
        onNew={onNew}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        ) : list.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            Nenhuma campanha cadastrada. Clique em <strong>Nova Campanha</strong> para começar.
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel>
            <EntityListTable
              rows={list}
              rowKey={(c) => c.id}
              onRowClick={(c) => onEdit(c.id)}
              columns={[
                {
                  key: "titulo",
                  header: "Campanha",
                  render: (c) => (
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{c.titulo}</p>
                      <p className="text-sm text-gray-500 line-clamp-1 mt-0.5">{c.mensagem}</p>
                    </div>
                  ),
                },
                {
                  key: "vigencia",
                  header: "Vigência",
                  className: "hidden md:table-cell",
                  render: (c) => (
                    <span className="text-xs text-gray-500">{formatCampanhaVigencia(c)}</span>
                  ),
                },
                {
                  key: "envio",
                  header: "Envio",
                  className: "hidden lg:table-cell",
                  render: (c) =>
                    campanhaFoiEnviada(c) ? (
                      <span className="text-xs text-green-600 dark:text-green-400">
                        {formatCampanhaEnvio(c)}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">{formatCampanhaEnvio(c)}</span>
                    ),
                },
              ]}
              trailingCell={(c) => (
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    onClick={() => onEnviar(c)}
                    className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg"
                    title="Enviar WhatsApp"
                  >
                    <Send size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => onEdit(c.id)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700"
                    title="Editar"
                  >
                    <Pencil size={16} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                  </button>
                  <button
                    type="button"
                    onClick={() => onExcluir(c)}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                    title="Excluir"
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
              itemLabel="campanhas"
            />
          </ClinicaBelezaPanel>
        )}
      </ClinicaBelezaPageContent>

      <CampanhaEnviarModal
        open={!!enviarCampanha}
        campanha={enviarCampanha}
        onClose={onCloseEnviar}
        onSent={onSent}
      />

      <CampanhaExcluirModal
        campanha={excluirCampanha}
        excluindo={excluindo}
        onClose={onCloseExcluir}
        onConfirm={onConfirmExcluir}
      />
    </>
  );
}
