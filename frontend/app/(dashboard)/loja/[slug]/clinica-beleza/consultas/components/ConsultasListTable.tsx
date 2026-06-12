"use client";

import { ChevronRight } from "lucide-react";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { CLINICA_CONSULTA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import type { Consulta } from "./consultas-types";

interface Props {
  consultas: Consulta[];
  onSelect: (consulta: Consulta) => void;
  formatData: (d?: string | null) => string;
}

export function ConsultasListTable({ consultas, onSelect, formatData }: Props) {
  return (
    <EntityListTable
      rows={consultas}
      rowKey={(c) => c.id}
      onRowClick={onSelect}
      trailingCell={() => <ChevronRight size={18} />}
      columns={[
        {
          key: "patient",
          header: "Cliente",
          render: (c) => (
            <span className="font-medium text-gray-900 dark:text-gray-100">{c.patient_name}</span>
          ),
        },
        {
          key: "agenda",
          header: "Agenda",
          className: "hidden sm:table-cell",
          render: (c) => (
            <span className="text-gray-600 dark:text-gray-400 text-xs">{c.nome_agenda_name || "—"}</span>
          ),
        },
        {
          key: "procedure",
          header: "Procedimento",
          render: (c) => (
            <span className="text-gray-700 dark:text-gray-300">{c.procedure_name}</span>
          ),
        },
        {
          key: "date",
          header: "Data",
          className: "hidden sm:table-cell",
          render: (c) => (
            <span className="text-gray-600 dark:text-gray-400 text-xs">
              {formatData(c.data_inicio || c.appointment_date)}
            </span>
          ),
        },
        {
          key: "professional",
          header: "Profissional",
          className: "hidden md:table-cell",
          render: (c) => (
            <span className="text-gray-600 dark:text-gray-400">{c.professional_name || "—"}</span>
          ),
        },
        {
          key: "status",
          header: "Status",
          className: "hidden lg:table-cell",
          render: (c) => (
            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-gray-400">
              {CLINICA_CONSULTA_STATUS_LABEL[c.status] || c.status}
            </span>
          ),
        },
      ]}
    />
  );
}
