"use client";

import { useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, FileText, Save, Trash2 } from "lucide-react";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaPaginatedList } from "@/hooks/clinica-beleza";
import { toUpperCase } from "@/lib/format-br";
import { isConvenioParticularNome, ordenarConveniosComParticularPrimeiro } from "@/lib/convenio-precos";

export default function ConveniosPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = params.slug as string;
  const basePath = `/loja/${slug}/clinica-beleza/convenios`;

  const {
    list: convenios,
    loading,
    load: carregarLista,
    page,
    setPage,
    totalPages,
    pageSize,
    totalCount,
  } = useClinicaBelezaPaginatedList<ConvenioItem>({ path: "/convenios/" });

  const [novoNome, setNovoNome] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  const isNovo = searchParams.get("novo") === "1";

  const voltarLista = () => {
    setErro("");
    router.replace(basePath, { scroll: false });
  };

  const abrirNovo = () => {
    router.replace(`${basePath}?novo=1`, { scroll: false });
  };

  const criarConvenio = async () => {
    if (!novoNome.trim()) {
      setErro("Informe o nome do convênio.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.convenios.create({ nome: novoNome.trim() });
      await carregarLista();
      voltarLista();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao criar convênio.");
    } finally {
      setSalvando(false);
    }
  };

  const excluirConvenio = async (c: ConvenioItem) => {
    if (isConvenioParticularNome(c.nome)) {
      alert("O convênio Particular é padrão do sistema e não pode ser excluído.");
      return;
    }
    if (!confirm(`Excluir o convênio "${c.nome}"? Os preços vinculados nos procedimentos serão removidos.`)) {
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.convenios.delete(c.id);
      await carregarLista();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erro ao excluir convênio.");
    } finally {
      setSalvando(false);
    }
  };

  if (isNovo) {
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title="Novo convênio"
          subtitle="Informe o nome; o código será gerado automaticamente"
          backHref={basePath}
          icon={FileText}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 !p-0">
          <div className="px-4 md:px-6 lg:px-8 pt-2 pb-3 border-b border-gray-200 dark:border-neutral-800 bg-white/80 dark:bg-neutral-900/80">
            <button
              type="button"
              onClick={voltarLista}
              className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            >
              <ArrowLeft size={16} />
              Voltar à lista
            </button>
          </div>
          <div className="flex-1 p-4 md:p-6 lg:p-8 w-full">
            <ClinicaBelezaPanel className="p-5 md:p-8 max-w-lg">
              {erro && (
                <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                  {erro}
                </div>
              )}
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Nome do convênio *
              </label>
              <input
                type="text"
                value={novoNome}
                onChange={(e) => setNovoNome(toUpperCase(e.target.value))}
                placeholder="Ex.: Unimed, Particular, Santa Casa..."
                autoFocus
                className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 mb-6"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-6">
                Os valores praticados por convênio são definidos na página de Procedimentos.
              </p>
              <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4 border-t border-gray-100 dark:border-neutral-700">
                <button
                  type="button"
                  onClick={voltarLista}
                  className="flex-1 sm:flex-none py-2.5 px-6 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={criarConvenio}
                  disabled={salvando || !novoNome.trim()}
                  className="flex-1 sm:flex-none flex items-center justify-center gap-2 py-2.5 px-6 rounded-lg text-white text-sm font-medium disabled:opacity-50"
                  style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                >
                  <Save size={16} />
                  {salvando ? "Criando..." : "Criar convênio"}
                </button>
              </div>
            </ClinicaBelezaPanel>
          </div>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Convênios"
        subtitle="Planos cadastrados com código automático — preços nos procedimentos"
        newLabel="Novo convênio"
        onNew={abrirNovo}
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
                            onClick={() => excluirConvenio(c)}
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
              onPageChange={setPage}
              itemLabel="convênios"
            />
          </div>
        )}
        {erro && (
          <p className="mt-4 text-sm text-red-600 dark:text-red-400">{erro}</p>
        )}
      </ClinicaBelezaPageContent>
    </>
  );
}
