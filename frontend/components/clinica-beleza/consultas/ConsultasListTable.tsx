"use client";

import { useMemo, type ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import {
  CLINICA_CONSULTA_STATUS_COLORS,
  CLINICA_CONSULTA_STATUS_LABEL,
} from "@/lib/clinica-beleza-constants";
import { DEFAULT_COLUNAS_CONSULTAS } from "@/lib/clinica-consultas-colunas-config";
import { toUpperCase } from "@/lib/format-br";
import { ConsultaPagamentoButton } from "./ConsultaPagamentoButton";
import { consultaProcedimentosNomes, type Consulta } from "./consultas-types";

type ColumnDef = {
  key: string;
  header: string;
  className?: string;
  render: (c: Consulta) => ReactNode;
};

interface Props {
  consultas: Consulta[];
  onSelect: (consulta: Consulta) => void;
  onReceber?: (consulta: Consulta) => void;
  recebendoConsultaId?: number | null;
  formatData: (d?: string | null) => string;
  /** Chaves na ordem desejada; vazio/undefined = padrão sem AGENDA. */
  colunasVisiveis?: string[];
}

function buildColumnRegistry(
  formatData: (d?: string | null) => string,
  onReceber?: (consulta: Consulta) => void,
  recebendoConsultaId: number | null = null,
): Record<string, ColumnDef> {
  return {
    patient: {
      key: "patient",
      header: "CLIENTE",
      render: (c) => (
        <div className="flex items-center gap-2.5 min-w-0">
          <PacienteAvatar fotoUrl={c.patient_foto_url} name={c.patient_name} size="sm" />
          <span className="font-medium text-gray-900 dark:text-gray-100 uppercase truncate">
            {toUpperCase(c.patient_name)}
          </span>
        </div>
      ),
    },
    agenda: {
      key: "agenda",
      header: "AGENDA",
      className: "hidden sm:table-cell",
      render: (c) => (
        <span className="text-gray-600 dark:text-gray-400 text-xs uppercase">
          {c.nome_agenda_name ? toUpperCase(c.nome_agenda_name) : "—"}
        </span>
      ),
    },
    procedure: {
      key: "procedure",
      header: "PROCEDIMENTO",
      render: (c) => (
        <span className="text-gray-700 dark:text-gray-300 uppercase">
          {consultaProcedimentosNomes(c)}
        </span>
      ),
    },
    date: {
      key: "date",
      header: "DATA",
      className: "hidden sm:table-cell",
      render: (c) => (
        <span className="text-gray-600 dark:text-gray-400 text-xs">
          {formatData(c.appointment_date || c.data_inicio)}
        </span>
      ),
    },
    professional: {
      key: "professional",
      header: "PROFISSIONAL",
      className: "hidden md:table-cell",
      render: (c) => (
        <span className="text-gray-600 dark:text-gray-400 uppercase">
          {c.professional_name ? toUpperCase(c.professional_name) : "—"}
        </span>
      ),
    },
    pagamento: {
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
    status: {
      key: "status",
      header: "STATUS",
      className: "hidden lg:table-cell",
      render: (c) => {
        const colors =
          CLINICA_CONSULTA_STATUS_COLORS[c.status] ?? CLINICA_CONSULTA_STATUS_COLORS.SCHEDULED;
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full uppercase ${colors.bg} ${colors.text}`}>
            {CLINICA_CONSULTA_STATUS_LABEL[c.status] || toUpperCase(c.status)}
          </span>
        );
      },
    },
  };
}

export function ConsultasListTable({
  consultas,
  onSelect,
  onReceber,
  recebendoConsultaId = null,
  formatData,
  colunasVisiveis,
}: Props) {
  const columns = useMemo(() => {
    const registry = buildColumnRegistry(formatData, onReceber, recebendoConsultaId);
    const keys =
      colunasVisiveis && colunasVisiveis.length > 0
        ? colunasVisiveis
        : DEFAULT_COLUNAS_CONSULTAS;
    return keys.map((key) => registry[key]).filter(Boolean);
  }, [colunasVisiveis, formatData, onReceber, recebendoConsultaId]);

  return (
    <EntityListTable
      rows={consultas}
      rowKey={(c) => c.id}
      onRowClick={onSelect}
      trailingCell={() => <ChevronRight size={18} />}
      columns={columns}
    />
  );
}
