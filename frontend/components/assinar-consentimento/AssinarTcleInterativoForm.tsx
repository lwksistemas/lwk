"use client";

import type { TermoConsentimentoSecao } from "@/lib/clinica-beleza-api";
import type { RespostaTcleInterativo } from "./assinar-consentimento-types";

interface Props {
  introducao: string;
  secoes: TermoConsentimentoSecao[];
  respostas: Record<string, RespostaTcleInterativo>;
  disabled?: boolean;
  onChange: (id: string, data: Partial<RespostaTcleInterativo>) => void;
}

export function AssinarTcleInterativoForm({
  introducao,
  secoes,
  respostas,
  disabled,
  onChange,
}: Props) {
  const ordered = [...secoes].sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0));

  return (
    <div className="space-y-6">
      {introducao ? (
        <p className="text-sm text-gray-700 dark:text-slate-300 whitespace-pre-wrap">{introducao}</p>
      ) : null}
      {ordered.map((secao) => {
        const r = respostas[secao.id] || {};
        const cab = secao.codigo ? `${secao.codigo}. ${secao.titulo}` : secao.titulo;
        return (
          <section key={secao.id} className="border border-gray-200 dark:border-slate-600 rounded-xl p-4 space-y-3">
            <h3 className="font-semibold text-gray-900 dark:text-white">{cab}</h3>
            {secao.texto ? (
              <p className="text-sm text-gray-700 dark:text-slate-300 whitespace-pre-wrap">{secao.texto}</p>
            ) : null}

            {(secao.tipo === "sim_nao" || secao.tipo === "fotos" || secao.tipo === "gravidez") && (
              <div className="flex gap-4 text-sm text-gray-800 dark:text-slate-200">
                <label className="inline-flex items-center gap-1.5">
                  <input
                    type="radio"
                    name={`sn-${secao.id}`}
                    disabled={disabled}
                    checked={r.sim_nao === "sim"}
                    onChange={() => onChange(secao.id, { sim_nao: "sim" })}
                  />
                  SIM
                </label>
                <label className="inline-flex items-center gap-1.5">
                  <input
                    type="radio"
                    name={`sn-${secao.id}`}
                    disabled={disabled}
                    checked={r.sim_nao === "nao"}
                    onChange={() => onChange(secao.id, { sim_nao: "nao" })}
                  />
                  NÃO
                </label>
              </div>
            )}

            {secao.tipo === "sim_nao" && (
              <div>
                <label className="text-xs text-gray-500 dark:text-slate-400">Dúvidas (opcional)</label>
                <textarea
                  disabled={disabled}
                  value={r.duvidas || ""}
                  onChange={(e) => onChange(secao.id, { duvidas: e.target.value })}
                  rows={2}
                  className="mt-1 w-full text-sm border border-gray-200 dark:border-slate-600 rounded-lg px-3 py-2 bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100"
                />
              </div>
            )}

            {secao.tipo === "gravidez" && (
              <div className="space-y-2 text-sm text-gray-800 dark:text-slate-200">
                <label className="block text-xs text-gray-500 dark:text-slate-400">Data da última menstruação</label>
                <input
                  type="date"
                  disabled={disabled || r.nao_me_recordo}
                  value={r.dum || ""}
                  onChange={(e) => onChange(secao.id, { dum: e.target.value, nao_me_recordo: false })}
                  className="border border-gray-200 dark:border-slate-600 rounded-lg px-3 py-2 bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100"
                />
                <label className="inline-flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    disabled={disabled}
                    checked={!!r.nao_me_recordo}
                    onChange={(e) => onChange(secao.id, {
                      nao_me_recordo: e.target.checked,
                      dum: e.target.checked ? "" : r.dum,
                    })}
                  />
                  Não me recordo
                </label>
              </div>
            )}

            {secao.tipo === "consinto" && (
              <div className="flex gap-4 text-sm text-gray-800 dark:text-slate-200">
                <label className="inline-flex items-center gap-1.5">
                  <input
                    type="radio"
                    name={`c-${secao.id}`}
                    disabled={disabled}
                    checked={r.consinto === "consinto"}
                    onChange={() => onChange(secao.id, { consinto: "consinto" })}
                  />
                  CONSINTO
                </label>
                <label className="inline-flex items-center gap-1.5">
                  <input
                    type="radio"
                    name={`c-${secao.id}`}
                    disabled={disabled}
                    checked={r.consinto === "recuso"}
                    onChange={() => onChange(secao.id, { consinto: "recuso" })}
                  />
                  RECUSO
                </label>
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}
