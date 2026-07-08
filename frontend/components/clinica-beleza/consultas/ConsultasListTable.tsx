"use client";

import { ChevronRight } from "lucide-react";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { CLINICA_CONSULTA_STATUS_COLORS, CLINICA_CONSULTA_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import { toUpperCase } from "@/lib/format-br";
import { ConsultaPagamentoButton } from "./ConsultaPagamentoButton";
import { consultaProcedimentosNomes, type Consulta } from "./consultas-types";

interface Props {
  consultas: Consulta[];
  onSelect: (consulta: Consulta) => void;
  onReceber?: (consulta: Consulta) => void;
  recebendoConsultaId?: number | null;
  formatData: (d?: string | null) => string;
}

export function ConsultasListTable({
  consultas,
  onSelect,
  onReceber,
  recebendoConsultaId = null,
  formatData,
}: Props) {
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
            <div className="flex items-center gap-2.5 min-w-0">
              <PacienteAvatar
                fotoUrl={c.patient_foto_url}
                name={c.patient_name}
                size="sm"
              />
              <span className="font-medium text-gray-900 dark:text-gray-100 uppercase truncate">
                {toUpperCase(c.patient_name)}
              </span>
            </div>
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
              {formatData(c.appointment_date || c.data_inicio)}
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
          key: "pagamento",
          header: "PAGAMENTO",
          render: (c) => (
            <ConsultaPagamentoButton
              consulta={c}
              onReceber={onReceber}
              loading={recebendoConsultaId === c.id}
            />
          ),
        },
        {
          key: "status",
          header: "STATUS",
          className: "hidden lg:table-cell",
          render: (c) => {
            const colors =
              CLINICA_CONSULTA_STATUS_COLORS[c.status] ?? CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;
            return (
              <span
                className={`text-xs px-2 py-0.5 rounded-full uppercase ${colors.bg} ${colors.text}`}
              >
                {CLINICA_CONSULTA_STATUS_LABEL[c.status] || toUpperCase(c.status)}
              </span>
            );
          },
        },
      ]}
    />
  );
}
