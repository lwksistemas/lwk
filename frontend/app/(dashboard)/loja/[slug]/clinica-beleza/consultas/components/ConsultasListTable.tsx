"use client";

import { ChevronRight } from "lucide-react";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { CLINICA_CONSULTA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import { toUpperCase } from "@/lib/format-br";
import { consultaProcedimentosNomes, type Consulta } from "./consultas-types";

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
          header: "CLIENTE",
          render: (c) => (
            <span className="font-medium text-gray-900 dark:text-gray-100 uppercase">
              {toUpperCase(c.patient_name)}
            </span>
          ),
        },
        {
          key: "agenda",
          header: "AGENDA",
          className: "hidden sm:table-cell",
          render: (c) => (
            <span className="text-gray-600 dark:text-gray-400 text-xs uppercase">
              {c.nome_agenda_name ? toUpperCase(c.nome_agenda_name) : "—"}
            </span>
          ),
        },
        {
          key: "procedure",
          header: "PROCEDIMENTO",
          render: (c) => (
            <span className="text-gray-700 dark:text-gray-300 uppercase">
              {consultaProcedimentosNomes(c)}
            </span>
          ),
        },
        {
          key: "date",
          header: "DATA",
          className: "hidden sm:table-cell",
          render: (c) => (
            <span className="text-gray-600 dark:text-gray-400 text-xs">
              {formatData(c.data_inicio || c.appointment_date)}
            </span>
          ),
        },
        {
          key: "professional",
          header: "PROFISSIONAL",
          className: "hidden md:table-cell",
          render: (c) => (
            <span className="text-gray-600 dark:text-gray-400 uppercase">
              {c.professional_name ? toUpperCase(c.professional_name) : "—"}
            </span>
          ),
        },
        {
          key: "status",
          header: "STATUS",
          className: "hidden lg:table-cell",
          render: (c) => (
            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-neutral-800 text-gray-600 dark:text-gray-400 uppercase">
              {CLINICA_CONSULTA_STATUS_LABEL[c.status] || toUpperCase(c.status)}
            </span>
          ),
        },
      ]}
    />
  );
}
