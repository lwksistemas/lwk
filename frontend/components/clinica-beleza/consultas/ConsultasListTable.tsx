"use client";

import { useMemo, type ReactNode } from "react";
import { BookOpen, Play, Trash2 } from "lucide-react";
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
import { prontuarioConsultaAtualAcoes } from "@/components/clinica-beleza/prontuario/prontuario-consultas-utils";

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
  onIniciar?: (consulta: Consulta) => void;
  onExcluir?: (consulta: Consulta) => void;
  onVerProntuario?: (consulta: Consulta) => void;
  recebendoConsultaId?: number | null;
  iniciandoConsultaId?: number | null;
  excluindoConsultaId?: number | null;
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
    numero: {
      key: "numero",
      header: "Nº",
      className: "w-16",
      render: (c) => (
        <span className="font-mono text-xs font-semibold text-gray-700 dark:text-gray-300 tabular-nums">
          {c.numero || "—"}
        </span>
      ),
    },
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
  onIniciar,
  onExcluir,
  onVerProntuario,
  recebendoConsultaId = null,
  iniciandoConsultaId = null,
  excluindoConsultaId = null,
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

  const btn =
    "inline-flex items-center justify-center gap-1 px-2 py-1 rounded-lg text-xs font-medium whitespace-nowrap disabled:opacity-50";

  return (
    <EntityListTable
      rows={consultas}
      rowKey={(c) => c.id}
      onRowClick={onSelect}
      trailingCell={(c) => {
        const acoes = prontuarioConsultaAtualAcoes(c, consultas);
        const iniciando = iniciandoConsultaId === c.id;
        const excluindo = excluindoConsultaId === c.id;
        return (
          <div className="flex flex-wrap items-center justify-end gap-1.5">
            {onExcluir && acoes.podeExcluir && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onExcluir(c);
                }}
                disabled={excluindo || iniciando}
                className={`${btn} border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20`}
              >
                <Trash2 size={12} />
                {excluindo ? "Excluindo…" : "Excluir"}
              </button>
            )}
            {onIniciar && acoes.podeIniciar && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onIniciar(c);
                }}
                disabled={iniciando || excluindo}
                className={`${btn} text-white`}
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                <Play size={12} />
                {iniciando ? "Iniciando…" : "Iniciar consulta"}
              </button>
            )}
            {acoes.mostrarContinuar && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(c);
                }}
                className={`${btn} text-white`}
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                <Play size={12} />
                Continuar
              </button>
            )}
            {onVerProntuario && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onVerProntuario(c);
                }}
                className={`${btn} border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-neutral-800`}
              >
                <BookOpen size={12} />
                Ver prontuário
              </button>
            )}
          </div>
        );
      }}
      columns={columns}
    />
  );
}
