"use client";

import { FileText, Trash2 } from "lucide-react";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import { isConvenioParticularNome, ordenarConveniosComParticularPrimeiro } from "@/lib/convenio-precos";

interface ConveniosListViewProps {
  convenios: ConvenioItem[];
  loading: boolean;
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  salvando: boolean;
  erro: string;
  onNova: () => void;
  onExcluir: (c: ConvenioItem) => void;
  onPageChange: (page: number) => void;
}

export function ConveniosListView({
  convenios,
  loading,
  page,
  totalPages,
  totalCount,
  pageSize,
  salvando,
  erro,
  onNova,
  onExcluir,
  onPageChange,
}: ConveniosListViewProps) {
  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Convênios"
        subtitle="Planos cadastrados com código automático — preços nos procedimentos"
        newLabel="Novo convênio"
        onNew={onNova}
        icon={FileText}
      />
      <ClinicaBelezaPageContent>
        {loading ? (
          <div className="text-center py-20 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : convenios.length === 0 ? (
          <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 p-12 text-center text-gray-500 dark:text-gray-400 shadow-sm">
            Nenhum convênio cadastrado. Clique em &quot;Novo convênio&quot; para começar.
          </div>
        ) : (
          <div className="rounded-xl bg-white/80 dark:bg-neutral-800/80 border border-gray-200 dark:border-neutral-700 shadow-sm overflow-hidden w-full">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
                  <tr>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Nome</th>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold">Código</th>
                    <th className="text-right px-4 md:px-6 py-3.5 font-semibold w-28">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {ordenarConveniosComParticularPrimeiro(convenios).map((c) => {
                    const padrao = isConvenioParticularNome(c.nome);
                    return (
                      <tr
                        key={c.id}
                        className="border-t border-gray-100 dark:border-neutral-700/80 hover:bg-[#F5E6EA]/40 dark:hover:bg-neutral-700/30 transition-colors"
                      >
                        <td className="px-4 md:px-6 py-4 font-medium text-gray-900 dark:text-gray-100">
                          <span className="inline-flex items-center gap-2">
                            {c.nome}
                            {padrao && (
                              <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200">
                                Padrão
                              </span>
                            )}
                          </span>
                        </td>
                        <td className="px-4 md:px-6 py-4 text-gray-600 dark:text-gray-400 font-mono text-xs">
                          {c.codigo || "—"}
                        </td>
                        <td className="px-4 md:px-6 py-4">
                          <div className="flex justify-end">
                            {!padrao && (
                              <button
                                type="button"
                                onClick={() => onExcluir(c)}
                                disabled={salvando}
                                className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                title="Excluir convênio"
                              >
                                <Trash2 size={18} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <EntityListLoadMore
              page={page}
              totalPages={totalPages}
              totalCount={totalCount ?? 0}
              pageSize={pageSize}
              loading={loading}
              onPageChange={onPageChange}
              itemLabel="convênios"
            />
          </div>
        )}
        {erro && <p className="mt-4 text-sm text-red-600 dark:text-red-400">{erro}</p>}
      </ClinicaBelezaPageContent>
    </>
  );
}
