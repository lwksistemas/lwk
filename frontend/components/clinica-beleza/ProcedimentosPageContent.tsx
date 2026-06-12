"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Pencil, Save, Stethoscope, Trash2 } from "lucide-react";
import {
  entityActive,
  entityName,
  procedureCategoria,
  procedureDescription,
  procedureDuration,
} from "@/lib/clinica-beleza-entities";
import { formatProcedimentoApiErrors } from "@/lib/clinica-beleza-form-errors";
import { formatCurrency } from "@/lib/financeiro-helpers";
import {
  CLINICA_FORM_INPUT,
  deleteClinicaBelezaEntity,
  saveClinicaBelezaEntity,
  useClinicaBelezaEntityList,
} from "@/lib/clinica-beleza-crud";
import {
  bloquearCriacaoDuplicadaOffline,
  deveVerificarDuplicataOffline,
  gerarIdTemporarioOffline,
  isBrowserOffline,
  isFetchNetworkError,
  temDuplicataNaLista,
} from "@/lib/clinica-beleza-offline";
import { buscarProcedimentosOffline, salvarProcedimentosOffline, adicionarNaFilaSync, getLojaSlug } from "@/lib/offline-db";
import { ClinicaBelezaPageContent, ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
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
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

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

  const saveOffline = async (body: Record<string, unknown>) => {
    const lojaSlug = getLojaSlug();
    if (deveVerificarDuplicataOffline(editing)) {
      const jaExisteLocal = temDuplicataNaLista(list, (p) =>
        entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
      );
      if (jaExisteLocal) {
        setError("Este procedimento já foi adicionado. Aguarde a sincronização.");
        return false;
      }
    }
    if (editing && editing.id > 0) {
      await adicionarNaFilaSync({
        tipo: "procedimento",
        payload: { action: "update", id: editing.id, body },
        lojaSlug,
      });
      const updatedList = list.map((p) =>
        p.id === editing.id
          ? { ...p, name: body.name as string, description: body.description as string | null, duration: body.duration as number }
          : p
      );
      setList(updatedList);
      await salvarProcedimentosOffline(updatedList);
    } else {
      await adicionarNaFilaSync({ tipo: "procedimento", payload: { action: "create", body }, lojaSlug });
      const tempId = gerarIdTemporarioOffline();
      const newProc: Procedure = {
        id: tempId,
        name: body.name as string,
        description: body.description as string | null,
        price: "0",
        duration: body.duration as number,
        categoria: body.category as string,
        active: true,
      };
      const updatedList = [newProc, ...list];
      setList(updatedList);
      await salvarProcedimentosOffline(updatedList);
    }
    return true;
  };

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
    setSaving(true);
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

    if (isBrowserOffline()) {
      try {
        const ok = await saveOffline(body);
        if (ok) {
          voltarLista();
          alert("Salvo offline. O procedimento será sincronizado quando você estiver online.");
        }
      } catch (err) {
        logger.warn("Erro ao salvar offline:", err);
        setError("Erro ao salvar localmente. Tente novamente.");
      }
      setSaving(false);
      return;
    }

    try {
      let procedureId: number;
      if (editing) {
        await saveClinicaBelezaEntity(`/procedures/${editing.id}/`, "PUT", body);
        procedureId = editing.id;
      } else {
        const created = await saveClinicaBelezaEntity("/procedures/", "POST", body) as { id?: number };
        procedureId = created?.id ?? 0;
      }
      if (procedureId > 0 && convenios.length > 0) {
        await ClinicaBelezaAPI.procedures.savePrecosConvenio(procedureId, buildPrecosPayload());
      }
      voltarLista();
      load();
      carregarMatrix();
    } catch (e: unknown) {
      const err = e && typeof e === "object" ? (e as Record<string, unknown>) : {};
      const msg = formatProcedimentoApiErrors(err) || (e instanceof Error ? e.message : "Erro ao salvar");
      if (isFetchNetworkError(msg)) {
        try {
          if (bloquearCriacaoDuplicadaOffline(editing, list, (p) =>
            entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
          )) {
            setError("Este procedimento já foi adicionado offline. Aguarde a sincronização.");
            setSaving(false);
            return;
          }
          const ok = await saveOffline(body);
          if (ok) {
            voltarLista();
            alert("Sem conexão. Procedimento salvo offline e será sincronizado quando você estiver online.");
          }
        } catch (err) {
          logger.warn("Erro ao salvar offline:", err);
          setError("Sem conexão. Não foi possível salvar offline. Tente novamente.");
        }
      } else {
        setError(msg);
      }
    } finally {
      setSaving(false);
    }
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
    return (
      <>
        <ClinicaBelezaStandardPageHeader
          title={editing ? "Editar Procedimento" : "Novo Procedimento"}
          subtitle={editing ? entityName(editing) : "Nome, categoria, duração e valores por convênio"}
          onBack={voltarLista}
          icon={Stethoscope}
        />
        <ClinicaBelezaPageContent>
          <ClinicaBelezaPanel className="p-6 md:p-8 max-w-2xl">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm mb-4">{error}</div>
            )}
            <div className="space-y-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                Dados do procedimento
              </p>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: toUpperCase(e.target.value) }))} className={CLINICA_FORM_INPUT} placeholder="Ex.: Limpeza de pele" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria *</label>
                <select value={form.categoria} onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))} className={CLINICA_FORM_INPUT}>
                  <option value="">Selecione...</option>
                  {PROCEDURE_CATEGORIA_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duração (min) *</label>
                <input type="number" min={1} value={form.duration} onChange={(e) => setForm((f) => ({ ...f, duration: e.target.value }))} className={CLINICA_FORM_INPUT} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} rows={2} className={`${CLINICA_FORM_INPUT} resize-none`} />
              </div>

              <div className="pt-2 border-t border-gray-200 dark:border-neutral-700">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.termo_consentimento_ativo}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, termo_consentimento_ativo: e.target.checked }))
                    }
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Exigir termo de consentimento esclarecido (assinatura digital)
                  </span>
                </label>
                {form.termo_consentimento_ativo && (
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Texto do termo
                    </label>
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
                      className={`${CLINICA_FORM_INPUT} resize-y font-mono text-xs`}
                    />
                  </div>
                )}
              </div>

              {convenios.length > 0 && (
                <div className="pt-2">
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Valor praticado por convênio (R$)
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {convenios.map((c) => (
                      <div key={c.id}>
                        <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 font-mono">
                          {c.codigo || c.nome}
                        </label>
                        <input
                          type="text"
                          inputMode="decimal"
                          value={precosConvenio[c.id] ?? ""}
                          onChange={(e) =>
                            setPrecosConvenio((prev) => ({ ...prev, [c.id]: e.target.value }))
                          }
                          className={CLINICA_FORM_INPUT}
                          placeholder="0,00"
                        />
                        <span className="text-xs text-gray-400 mt-0.5 block">{c.nome}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {convenios.length === 0 && (
                <p className="text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
                  Cadastre convênios antes de definir os valores praticados.
                </p>
              )}
            </div>
            <div className="flex gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-neutral-700">
              <button type="button" onClick={voltarLista} className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg border text-sm font-medium">
                <ArrowLeft size={16} />
                Cancelar
              </button>
              <button type="button" onClick={save} disabled={saving} className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg text-white text-sm font-medium disabled:opacity-50" style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}>
                <Save size={16} />
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </ClinicaBelezaPanel>
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
                        className="text-left px-4 md:px-6 py-3.5 font-semibold whitespace-nowrap font-mono text-xs"
                        title={c.nome}
                      >
                        {c.codigo || c.nome}
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
