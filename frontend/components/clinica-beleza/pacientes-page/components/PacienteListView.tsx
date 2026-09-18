"use client";

import { useMemo } from "react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { EntityListTable, type EntityListColumn } from "@/components/clinica-beleza/EntityListTable";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import {
  entityEmail,
  entityName,
  entityPhone,
  patientBirthDate,
  patientCpf,
} from "@/lib/clinica-beleza-entities";
import { formatTelefone, formatCpf } from "@/lib/format-br";
import { formatDate } from "@/lib/financeiro-helpers";
import { CONVENIO_PARTICULAR_LABEL } from "@/lib/convenio-precos";
import {
  DEFAULT_COLUNAS_PACIENTES,
  resolveColunasPacientes,
} from "@/lib/clinica-pacientes-colunas-config";
import type { Patient } from "../lib/paciente-form-utils";

export interface PacienteListViewProps {
  list: Patient[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onEdit: (patient: Patient) => void;
  colunasVisiveis?: string[];
}

function sexoLabel(sexo: string | null | undefined): string {
  if (sexo === "M") return "Masculino";
  if (sexo === "F") return "Feminino";
  return "—";
}

function buildColumnRegistry(): Record<string, EntityListColumn<Patient>> {
  return {
    nome: {
      key: "nome",
      header: "Nome",
      className: "min-w-0",
      render: (p) => (
        <div className="flex items-center gap-3 font-medium text-gray-900 dark:text-gray-100 min-w-0">
          <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
          <span className="truncate">{entityName(p)}</span>
          {p.id < 0 && (
            <span className="text-xs text-amber-600 dark:text-amber-400 font-normal shrink-0">
              (offline)
            </span>
          )}
        </div>
      ),
    },
    telefone: {
      key: "telefone",
      header: "Telefone",
      className: "whitespace-nowrap",
      render: (p) => (
        <span className="text-gray-700 dark:text-gray-300">
          {formatTelefone(entityPhone(p)) || "—"}
        </span>
      ),
    },
    email: {
      key: "email",
      header: "E-mail",
      className: "max-w-[14rem]",
      render: (p) => (
        <span className="text-gray-700 dark:text-gray-300 truncate block">
          {entityEmail(p) || "—"}
        </span>
      ),
    },
    cpf: {
      key: "cpf",
      header: "CPF",
      className: "whitespace-nowrap",
      render: (p) => (
        <span className="text-gray-700 dark:text-gray-300">
          {formatCpf(patientCpf(p) || "") || "—"}
        </span>
      ),
    },
    convenio: {
      key: "convenio",
      header: "Convênio",
      render: (p) => (
        <span className="text-gray-700 dark:text-gray-300 truncate block max-w-[10rem]">
          {p.convenio_name || CONVENIO_PARTICULAR_LABEL}
        </span>
      ),
    },
    data_nascimento: {
      key: "data_nascimento",
      header: "Nascimento",
      className: "whitespace-nowrap",
      render: (p) => (
        <span className="text-gray-700 dark:text-gray-300">
          {formatDate(patientBirthDate(p), "—")}
        </span>
      ),
    },
    cidade: {
      key: "cidade",
      header: "Cidade",
      render: (p) => (
        <span className="text-gray-700 dark:text-gray-300 truncate block max-w-[10rem]">
          {p.cidade || p.city || "—"}
        </span>
      ),
    },
    sexo: {
      key: "sexo",
      header: "Sexo",
      className: "whitespace-nowrap",
      render: (p) => (
        <span className="text-gray-700 dark:text-gray-300">{sexoLabel(p.sexo)}</span>
      ),
    },
  };
}

export function PacienteListView({
  list,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  onPageChange,
  onEdit,
  colunasVisiveis,
}: PacienteListViewProps) {
  const columns = useMemo(() => {
    const registry = buildColumnRegistry();
    const keys =
      colunasVisiveis && colunasVisiveis.length > 0
        ? colunasVisiveis
        : DEFAULT_COLUNAS_PACIENTES;
    return keys.map((key) => registry[key]).filter(Boolean);
  }, [colunasVisiveis]);

  const resumoMobile = resolveColunasPacientes(
    colunasVisiveis && colunasVisiveis.length > 0 ? colunasVisiveis : DEFAULT_COLUNAS_PACIENTES,
  )
    .map((c) => c.key)
    .filter((k) => k !== "nome");

  if (loading) {
    return (
      <div className="text-center py-20 text-gray-500 dark:text-gray-400">
        Carregando...
      </div>
    );
  }

  const empty = (
    <div className="p-12 text-center text-gray-500 dark:text-gray-400">
      Nenhum cliente cadastrado. Clique em &quot;Novo Cliente&quot; para começar.
    </div>
  );

  const cellText = (p: Patient, key: string): string => {
    if (key === "telefone") return formatTelefone(entityPhone(p)) || "Sem telefone";
    if (key === "email") return entityEmail(p) || "—";
    if (key === "cpf") return formatCpf(patientCpf(p) || "") || "—";
    if (key === "convenio") return p.convenio_name || CONVENIO_PARTICULAR_LABEL;
    if (key === "data_nascimento") return formatDate(patientBirthDate(p), "—");
    if (key === "cidade") return p.cidade || p.city || "—";
    if (key === "sexo") return sexoLabel(p.sexo);
    return "";
  };

  return (
    <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full max-w-full min-w-0">
      {list.length === 0 ? (
        empty
      ) : (
        <>
          <ul className="sm:hidden divide-y divide-gray-100 dark:divide-neutral-700">
            {list.map((p) => (
              <li key={p.id}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => onEdit(p)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onEdit(p);
                    }
                  }}
                  className="w-full flex items-center gap-3 px-3 py-3 text-left touch-manipulation active:bg-gray-50 dark:active:bg-neutral-700/40 min-w-0 cursor-pointer"
                >
                  <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
                      {entityName(p)}
                      {p.id < 0 ? (
                        <span className="text-xs text-amber-600 dark:text-amber-400 font-normal ml-1">
                          (offline)
                        </span>
                      ) : null}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                      {resumoMobile.map((k) => cellText(p, k)).filter(Boolean).slice(0, 2).join(" · ") || "—"}
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <div className="hidden sm:block max-w-full min-w-0">
            <EntityListTable
              rows={list}
              rowKey={(p) => p.id}
              onRowClick={onEdit}
              columns={columns}
            />
          </div>
        </>
      )}

      <div className="px-3 sm:px-0">
        <EntityListLoadMore
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          loading={loading}
          onPageChange={onPageChange}
          itemLabel="pacientes"
        />
      </div>
    </div>
  );
}
