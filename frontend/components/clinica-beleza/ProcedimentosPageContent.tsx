"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Loader2, Pencil, Save, Stethoscope, Trash2 } from "lucide-react";
import {
  entityActive,
  entityName,
  procedureCategoria,
  procedureDescription,
  procedureDuration,
} from "@/lib/clinica-beleza-entities";
import { formatCurrency } from "@/lib/financeiro-helpers";
import {
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
  useClinicaBelezaEntityList,
} from "@/lib/clinica-beleza-crud";
import { isBrowserOffline } from "@/lib/clinica-beleza-offline";
import { buscarProcedimentosOffline, salvarProcedimentosOffline } from "@/lib/offline-db";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { useOfflineSave } from "@/hooks/clinica-beleza/useOfflineSave";
import { useLojaTheme } from "@/hooks/useLojaTheme";
import { logger } from "@/lib/logger";
import { toUpperCase } from "@/lib/format-br";
import {
  PROCEDURE_CATEGORIA_OPTIONS,
  defaultCategoriaForModule,
  procedureCategoriaLabel,
  procedureMatchesModule,
  resolveProcedureCategoriaSlug,
} from "@/lib/clinica-beleza-categories";
import {
  ClinicaBelezaAPI,
  type ConvenioItem,
  type ProcedureConvenioPrecoItem,
} from "@/lib/clinica-beleza-api";

interface Procedure {
  id: number;
  name?: string;
  nome?: string;
  description?: string | null;
  descricao?: string | null;
  price?: string;
  preco?: string;
  duration?: number;
  duracao_minutos?: number;
  active?: boolean;
  is_active?: boolean;
  categoria?: string;
  termo_consentimento?: string;
  termo_consentimento_ativo?: boolean;
}

const DEFAULT_TERMO_CONSENTIMENTO = `TERMO DE CONSENTIMENTO ESCLARECIDO

Eu, {paciente_nome}, inscrito(a) no CPF {paciente_cpf}, declaro ter sido esclarecido(a) sobre o(s) procedimento(s): {procedimentos}, a serem realizados pela profissional {profissional_nome} ({profissional_conselho}) na clínica {clinica_nome}.

Fui informado(a) sobre objetivos, benefícios, riscos, efeitos adversos, contraindicações e alternativas, e tive oportunidade de esclarecer minhas dúvidas.

Declaro que concordo com a realização do(s) procedimento(s) na data {data}.`;

const EMPTY_FORM = {
  name: "",
  description: "",
  duration: "30",
  categoria: "",
  termo_consentimento: DEFAULT_TERMO_CONSENTIMENTO,
  termo_consentimento_ativo: false,
};

function procedureToForm(p: Procedure) {
  return {
    name: entityName(p),
    description: procedureDescription(p) || "",
    duration: String(procedureDuration(p)),
    categoria: resolveProcedureCategoriaSlug(procedureCategoria(p)),
    termo_consentimento: (p.termo_consentimento || "").trim() || DEFAULT_TERMO_CONSENTIMENTO,
    termo_consentimento_ativo: !!p.termo_consentimento_ativo,
  };
}

export interface ProcedimentosPageContentProps {
  title?: string;
  subtitle?: string;
  defaultCategoria?: string;
  backHref?: string;
  relatedLinks?: { label: string; href: string }[];
}

export function ProcedimentosPageContent({
  title = 'Procedimentos',
  subtitle = 'Serviços e valores praticados por convênio',
  defaultCategoria = '',
  backHref,
  relatedLinks = [],
}: ProcedimentosPageContentProps) {
  const params = useParams();
  const slug = params.slug as string;
  const { theme } = useLojaTheme(slug);
  const accentColor = theme.corPrimaria || CLINICA_BELEZA_PRIMARY;
  const { isNovo, editIdParam, isFormView, voltarLista, abrirNovo, abrirEditar } =
    useClinicaBelezaFormRouting();

  const [showAllCategories, setShowAllCategories] = useState(false);
  const moduleKey = defaultCategoria || "";
  const presetCategoria = defaultCategoriaForModule(moduleKey) || defaultCategoria;
  // Lista completa na API; filtro por módulo (estética/soroterapia) só no cliente (aliases + acentos).
  const listPath = "/procedures/";

  const { list, setList, loading, load, page, setPage, totalPages, pageSize, totalCount } = useClinicaBelezaEntityList<Procedure>({
    path: listPath,
    fetchOffline: buscarProcedimentosOffline,
    saveOffline: salvarProcedimentosOffline,
    reloadDeps: [moduleKey, showAllCategories],
  });

  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [precosMap, setPrecosMap] = useState<Record<string, string>>({});
  const [matrixLoading, setMatrixLoading] = useState(false);

  const [editing, setEditing] = useState<Procedure | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [precosConvenio, setPrecosConvenio] = useState<Record<number, string>>({});
  const [error, setError] = useState("");

  const { save: offlineSave, saving } = useOfflineSave<Procedure>({
    entityType: "procedimento",
    saveOnline: async (body, ed) => {
      let procedureId: number;
      if (ed) {
        await saveClinicaBelezaEntity(`/procedures/${ed.id}/`, "PUT", body);
        procedureId = ed.id;
      } else {
        const created = await saveClinicaBelezaEntity("/procedures/", "POST", body) as { id?: number };
        procedureId = created?.id ?? 0;
      }
      if (procedureId > 0 && convenios.length > 0) {
        await ClinicaBelezaAPI.procedures.savePrecosConvenio(
          procedureId,
          convenios.map((c) => {
            const raw = precosConvenio[c.id]?.trim();
            return {
              convenio: c.id,
              preco: raw ? raw.replace(",", ".") : null,
            };
          }),
        );
      }
    },
    list,
    setList,
    saveOffline: salvarProcedimentosOffline,
    buildNewEntity: (body, tempId) => ({
      id: tempId,
      name: body.name as string,
      description: body.description as string | null,
      price: "0",
      duration: body.duration as number,
      categoria: body.category as string,
      active: true,
    }),
    duplicatePredicate: (p) =>
      entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
    offlineMessage: "Salvo offline. O procedimento será sincronizado quando você estiver online.",
  });

  const carregarMatrix = useCallback(async () => {
    if (isBrowserOffline()) return;
    setMatrixLoading(true);
    try {
      const data = await ClinicaBelezaAPI.procedures.convenioPrecosMatrix();
      setConvenios(data.convenios || []);
      const map: Record<string, string> = {};
      for (const row of data.precos || []) {
        map[`${row.procedure}:${row.convenio}`] = row.preco;
      }
      setPrecosMap(map);
    } catch (e) {
      logger.warn("Erro ao carregar matriz de preços:", e);
    } finally {
      setMatrixLoading(false);
    }
  }, []);

  useEffect(() => {
    carregarMatrix();
  }, [carregarMatrix, list.length]);

  useEffect(() => {
    if (defaultCategoria && isNovo) {
      setForm((f) => ({ ...f, categoria: defaultCategoria }));
    }
  }, [defaultCategoria, isNovo]);

  useEffect(() => {
    if (!isFormView) return;
    if (isNovo) {
      setEditing(null);
      setForm({
        ...EMPTY_FORM,
        categoria: presetCategoria,
      });
      setPrecosConvenio({});
      setError("");
      return;
    }
    if (editIdParam && list.length > 0) {
      const p = list.find((x) => String(x.id) === editIdParam);
      if (p) {
        setEditing(p);
        setForm(procedureToForm(p));
        setError("");
        if (!isBrowserOffline() && p.id > 0) {
          ClinicaBelezaAPI.procedures.precosConvenio(p.id)
            .then((rows: ProcedureConvenioPrecoItem[]) => {
              const map: Record<number, string> = {};
              for (const r of rows) {
                if (r.preco != null && r.preco !== "") {
                  map[r.convenio] = String(r.preco);
                }
              }
              setPrecosConvenio(map);
            })
            .catch((e) => logger.warn("Erro ao carregar preços do procedimento:", e));
        }
      }
    }
  }, [isFormView, isNovo, editIdParam, list, presetCategoria]);

  const precoCelula = useMemo(() => {
    return (procId: number, convId: number) => {
      const key = `${procId}:${convId}`;
      const val = precosMap[key];
      return val != null && val !== "" ? formatCurrency(Number(val)) : "—";
    };
  }, [precosMap]);

  const buildPrecosPayload = () =>
    convenios.map((c) => {
      const raw = precosConvenio[c.id]?.trim();
      return {
        convenio: c.id,
        preco: raw ? raw.replace(",", ".") : null,
      };
    });

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    const categoria = form.categoria.trim() || presetCategoria;
    if (!categoria) {
      setError("Categoria é obrigatória.");
      return;
    }
    const duration = parseInt(form.duration, 10);
    if (isNaN(duration) || duration < 1) {
      setError("Duração deve ser um número positivo (minutos).");
      return;
    }
    const temAlgumPreco = convenios.some((c) => precosConvenio[c.id]?.trim());
    if (convenios.length > 0 && !temAlgumPreco) {
      setError("Informe o valor praticado em pelo menos um convênio.");
      return;
    }
    setError("");
    const body = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price: "0.00",
      duration,
      active: true,
      category: categoria,
      termo_consentimento: form.termo_consentimento_ativo ? form.termo_consentimento.trim() : "",
      termo_consentimento_ativo: form.termo_consentimento_ativo,
    };

    const result = await offlineSave(body, editing);
    if (!result.ok) {
      if (result.error) setError(result.error);
      return;
    }
    if (result.offline) {
      voltarLista();
      alert(result.message);
      return;
    }
    voltarLista();
    load();
    carregarMatrix();
  };

  const exclude = async (p: Procedure) => {
    if (!confirm(`Desativar o procedimento "${entityName(p)}"?`)) return;
    try {
      await deleteClinicaBelezaEntity(`/procedures/${p.id}/`);
      load();
      carregarMatrix();
    } catch {
      alert("Erro ao desativar.");
    }
  };

  const activeList = list.filter((p) => entityActive(p));
  const filteredList =
    moduleKey && !showAllCategories
      ? activeList.filter((p) => procedureMatchesModule(procedureCategoria(p), moduleKey))
      : activeList;
  const hiddenByCategoryCount =
    moduleKey && !showAllCategories ? activeList.length - filteredList.length : 0;

  if (isFormView) {
    const inputClass =
      "w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-0";
    const labelClass = "block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1";
    const sectionTitleClass =
      "text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-neutral-800 pb-2";

    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={editing ? "Editar procedimento" : "Novo procedimento"}
          subtitle={editing ? entityName(editing) : "Cadastro de procedimento da clínica"}
          onBack={voltarLista}
          icon={Stethoscope}
        />
        <ClinicaBelezaPageContent className="flex flex-col flex-1 min-h-0 !p-0 !bg-[#f7f2f4] dark:!bg-gray-950">
          <div className="flex flex-col flex-1 min-h-0 w-full">
            <div className="flex-1 min-h-0 overflow-y-auto p-4 md:p-6 lg:p-8 bg-[#f7f2f4] dark:bg-gray-950">
              {error && (
                <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
                  {error}
                </div>
              )}

              <ClinicaBelezaPanel className="p-5 md:p-6 lg:p-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full max-w-none">
                  <div className="space-y-4">
                    <p className={sectionTitleClass}>Dados do procedimento</p>
                    <div>
                      <label className={labelClass}>Nome *</label>
                      <input
                        value={form.name}
                        onChange={(e) => setForm((f) => ({ ...f, name: toUpperCase(e.target.value) }))}
                        className={inputClass}
                        placeholder="Ex.: Limpeza de pele"
                        autoFocus
                      />
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className={labelClass}>Categoria *</label>
                        <select
                          value={form.categoria}
                          onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))}
                          className={inputClass}
                        >
                          <option value="">Selecione...</option>
                          {PROCEDURE_CATEGORIA_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className={labelClass}>Duração (min) *</label>
                        <input
                          type="number"
                          min={1}
                          value={form.duration}
                          onChange={(e) => setForm((f) => ({ ...f, duration: e.target.value }))}
                          className={inputClass}
                        />
                      </div>
                    </div>
                    <div>
                      <label className={labelClass}>Descrição</label>
                      <textarea
                        value={form.description}
                        onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                        rows={4}
                        className={`${inputClass} resize-y min-h-[96px]`}
                        placeholder="Opcional"
                      />
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="space-y-4">
                      <p className={sectionTitleClass}>Termo de consentimento</p>
                      <label className="flex items-start gap-2.5 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.termo_consentimento_ativo}
                          onChange={(e) =>
                            setForm((f) => ({ ...f, termo_consentimento_ativo: e.target.checked }))
                          }
                          className="mt-0.5 rounded border-gray-300"
                          style={{ accentColor }}
                        />
                        <span className="text-xs text-gray-600 dark:text-gray-400 leading-snug">
                          Exigir termo de consentimento esclarecido (assinatura digital)
                        </span>
                      </label>
                      {form.termo_consentimento_ativo && (
                        <div>
                          <label className={labelClass}>Texto do termo</label>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                            Variáveis: {"{paciente_nome}"}, {"{paciente_cpf}"}, {"{profissional_nome}"},{" "}
                            {"{profissional_conselho}"}, {"{clinica_nome}"}, {"{procedimentos}"}, {"{data}"}
                          </p>
                          <textarea
                            value={form.termo_consentimento}
                            onChange={(e) =>
                              setForm((f) => ({ ...f, termo_consentimento: e.target.value }))
                            }
                            rows={10}
                            className={`${inputClass} resize-y font-mono text-xs min-h-[180px]`}
                          />
                        </div>
                      )}
                    </div>

                    <div className="space-y-4">
                      <p className={sectionTitleClass}>Valores por convênio</p>
                      {convenios.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {convenios.map((c) => (
                            <div key={c.id}>
                              <label className={`${labelClass}`}>{c.nome}</label>
                              <input
                                type="text"
                                inputMode="decimal"
                                value={precosConvenio[c.id] ?? ""}
                                onChange={(e) =>
                                  setPrecosConvenio((prev) => ({ ...prev, [c.id]: e.target.value }))
                                }
                                className={inputClass}
                                placeholder="0,00"
                              />
                              <span className="text-xs text-gray-400 mt-0.5 block">{c.nome}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
                          Cadastre convênios antes de definir os valores praticados.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </ClinicaBelezaPanel>
            </div>

            <div className="shrink-0 border-t border-gray-200 dark:border-neutral-700 bg-white/80 dark:bg-neutral-800/80 px-4 md:px-6 lg:px-8 py-4">
              <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-3 w-full">
                <button
                  type="button"
                  onClick={voltarLista}
                  className="sm:min-w-[120px] py-2.5 px-5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-neutral-800"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={save}
                  disabled={saving}
                  className="sm:min-w-[180px] flex items-center justify-center gap-2 py-2.5 px-5 rounded-lg text-white text-sm font-medium disabled:opacity-60"
                  style={{ backgroundColor: accentColor }}
                >
                  {saving ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                  {saving ? "Salvando..." : editing ? "Salvar alterações" : "Cadastrar procedimento"}
                </button>
              </div>
            </div>
          </div>
        </ClinicaBelezaPageContent>
      </>
    );
  }

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={subtitle}
        backHref={backHref}
        icon={Stethoscope}
        newLabel="Novo Procedimento"
        onNew={abrirNovo}
      />
      <ClinicaBelezaPageContent>
        {moduleKey && (
          <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
            <span className="px-2 py-1 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200">
              Filtro: {moduleKey === 'soroterapia' ? 'Soroterapia' : 'Estética'}
            </span>
            {hiddenByCategoryCount > 0 && (
              <button type="button" onClick={() => setShowAllCategories(!showAllCategories)} className="text-purple-700 dark:text-purple-300 underline">
                {showAllCategories ? 'Mostrar só deste módulo' : `Mostrar todos (${activeList.length} cadastrados)`}
              </button>
            )}
          </div>
        )}

        {loading || matrixLoading ? (
          <div className="text-center py-16 text-gray-500">Carregando...</div>
        ) : filteredList.length === 0 ? (
          <ClinicaBelezaPanel className="p-12 text-center text-gray-500 text-sm">
            {activeList.length === 0 ? (
              <>Nenhum procedimento cadastrado. Clique em <strong>Novo Procedimento</strong> para começar.</>
            ) : (
              <>Nenhum procedimento nesta categoria.</>
            )}
          </ClinicaBelezaPanel>
        ) : (
          <ClinicaBelezaPanel className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[480px]">
                <thead className="bg-gray-50 dark:bg-neutral-900/80 text-gray-600 dark:text-gray-400 border-b border-gray-200 dark:border-neutral-700">
                  <tr>
                    <th className="text-left px-4 md:px-6 py-3.5 font-semibold sticky left-0 bg-gray-50 dark:bg-neutral-900/80 z-10">
                      Procedimento
                    </th>
                    {convenios.map((c) => (
                      <th
                        key={c.id}
                        className="text-left px-4 md:px-6 py-3.5 font-semibold whitespace-nowrap text-xs"
                        title={c.nome}
                      >
                        {c.nome}
                      </th>
                    ))}
                    <th className="text-right px-4 md:px-6 py-3.5 font-semibold w-24">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredList.map((p) => (
                    <tr
                      key={p.id}
                      className="border-t border-gray-100 dark:border-neutral-700/80 hover:bg-[#F5E6EA]/30 dark:hover:bg-neutral-700/20 cursor-pointer"
                      onClick={() => abrirEditar(p.id)}
                    >
                      <td className="px-4 md:px-6 py-3.5 font-medium text-gray-800 dark:text-gray-200 sticky left-0 bg-white/90 dark:bg-neutral-800/90">
                        <span>{entityName(p)}</span>
                        {procedureCategoria(p) ? (
                          <span className="block text-xs font-normal text-gray-500 dark:text-gray-400 mt-0.5">
                            {procedureCategoriaLabel(procedureCategoria(p))}
                          </span>
                        ) : null}
                      </td>
                      {convenios.map((c) => (
                        <td key={c.id} className="px-4 md:px-6 py-3.5 text-gray-600 dark:text-gray-400 whitespace-nowrap">
                          {precoCelula(p.id, c.id)}
                        </td>
                      ))}
                      <td className="px-4 md:px-6 py-3.5" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-1">
                          <button type="button" onClick={() => abrirEditar(p.id)} className="p-2 text-purple-600 hover:bg-purple-50 rounded" title="Editar">
                            <Pencil size={16} />
                          </button>
                          <button type="button" onClick={() => exclude(p)} className="p-2 text-red-600 hover:bg-red-50 rounded" title="Desativar">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
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
              itemLabel="procedimentos"
            />
          </ClinicaBelezaPanel>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>
    </>
  );
}
