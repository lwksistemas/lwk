"use client";

import { BookOpen, Loader2, Search } from "lucide-react";
import { PacienteAvatar } from "@/components/clinica-beleza/PacienteAvatar";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { entityName } from "@/lib/clinica-beleza-entities";
import { formatCpf, formatTelefone } from "@/lib/format-br";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { useProntuarioHub } from "./useProntuarioHub";

function patientSubtitle(p: PatientQuickOption): string {
  const parts: string[] = [];
  const tel = p.telefone || p.phone;
  if (tel) parts.push(formatTelefone(tel));
  if (p.cpf) parts.push(formatCpf(p.cpf));
  if (p.email) parts.push(p.email);
  return parts.join(" · ") || "Sem telefone/CPF/e-mail";
}

export function ProntuarioHubPageContent() {
  const { query, setQuery, searching, resultados, abrirProntuario } = useProntuarioHub();

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Prontuário"
        subtitle="Pesquise o paciente para ver o histórico, as fotos e a consulta atual"
        icon={BookOpen}
      />
      <ClinicaBelezaPageContent>
        <ClinicaBelezaPanel className="p-4 sm:p-6">
          <label htmlFor="prontuario-busca-paciente" className="sr-only">
            Pesquisar paciente
          </label>
          <div className="relative max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <input
              id="prontuario-busca-paciente"
              type="search"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nome, CPF, telefone ou e-mail"
              className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100"
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            Fotos, evolução e demais registros são incluídos dentro da consulta.
          </p>
        </ClinicaBelezaPanel>

        <div className="mt-4">
          {searching ? (
            <ClinicaBelezaPanel className="p-12 text-center text-sm text-gray-500 dark:text-gray-400">
              <span className="inline-flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Buscando...
              </span>
            </ClinicaBelezaPanel>
          ) : query.trim().length < 1 ? (
            <ClinicaBelezaPanel className="p-12 text-center text-sm text-gray-500 dark:text-gray-400">
              Digite o nome do paciente para abrir o prontuário.
            </ClinicaBelezaPanel>
          ) : resultados.length === 0 ? (
            <ClinicaBelezaPanel className="p-12 text-center text-sm text-gray-500 dark:text-gray-400">
              Nenhum paciente encontrado.
            </ClinicaBelezaPanel>
          ) : (
            <ClinicaBelezaPanel>
              <ul className="divide-y divide-gray-100 dark:divide-neutral-700">
                {resultados.map((p) => (
                  <li key={p.id}>
                    <div className="flex items-center gap-3 px-4 py-3">
                      <PacienteAvatar fotoUrl={p.foto_url} name={entityName(p)} size="sm" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {entityName(p)}
                        </p>
                        <p className="text-xs text-gray-500 truncate">{patientSubtitle(p)}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => abrirProntuario(p.id)}
                        className="shrink-0 inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-white"
                        style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
                      >
                        <BookOpen size={16} />
                        Ver prontuário
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </ClinicaBelezaPanel>
          )}
        </div>
      </ClinicaBelezaPageContent>
    </>
  );
}
