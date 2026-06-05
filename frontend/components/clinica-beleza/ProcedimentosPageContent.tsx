"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, Pencil, Save, Stethoscope, Trash2 } from "lucide-react";
import {
  entityActive,
  entityName,
  procedureCategoria,
  procedureDescription,
  procedureDuration,
  procedurePrice,
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
import { EntityListTable } from "@/components/clinica-beleza/EntityListTable";
import { EntityListLoadMore } from "@/components/clinica-beleza/EntityListLoadMore";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useClinicaBelezaFormRouting } from "@/hooks/clinica-beleza/useClinicaBelezaFormRouting";
import { logger } from "@/lib/logger";
import {
  PROCEDURE_CATEGORIA_OPTIONS,
  defaultCategoriaForModule,
  procedureMatchesModule,
} from "@/lib/clinica-beleza-categories";

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
}

const EMPTY_FORM = {
  name: "",
  description: "",
  price: "",
  duration: "30",
  categoria: "",
};

function procedureToForm(p: Procedure) {
  return {
    name: entityName(p),
    description: procedureDescription(p) || "",
    price: String(procedurePrice(p)),
    duration: String(procedureDuration(p)),
    categoria: procedureCategoria(p),
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
  subtitle = 'Serviços e procedimentos oferecidos',
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
  const listPath =
    moduleKey && !showAllCategories ? `/procedures/?categoria=${encodeURIComponent(moduleKey)}` : "/procedures/";

  const { list, setList, loading, load, loadMore, loadingMore, hasMore, totalCount } = useClinicaBelezaEntityList<Procedure>({
    path: listPath,
    fetchOffline: buscarProcedimentosOffline,
    saveOffline: salvarProcedimentosOffline,
    reloadDeps: [moduleKey, showAllCategories],
  });

  const [editing, setEditing] = useState<Procedure | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

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
      setError("");
      return;
    }
    if (editIdParam && list.length > 0) {
      const p = list.find((x) => String(x.id) === editIdParam);
      if (p) {
        setEditing(p);
        setForm(procedureToForm(p));
        setError("");
      }
    }
  }, [isFormView, isNovo, editIdParam, list, presetCategoria]);

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
          ? { ...p, name: body.name as string, description: body.description as string | null, price: body.price as string, duration: body.duration as number }
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
        price: body.price as string,
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
    const duration = parseInt(form.duration, 10);
    const price = parseFloat(form.price.replace(",", "."));
    if (isNaN(duration) || duration < 1) {
      setError("Duração deve ser um número positivo (minutos).");
      return;
    }
    if (isNaN(price) || price < 0) {
      setError("Preço inválido.");
      return;
    }
    setSaving(true);
    setError("");
    const body = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      price: price.toFixed(2),
      duration,
      active: true,
      category: (form.categoria.trim() || presetCategoria || "geral"),
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
      if (editing) {
        await saveClinicaBelezaEntity(`/procedures/${editing.id}/`, "PUT", body);
      } else {
        await saveClinicaBelezaEntity("/procedures/", "POST", body);
      }
      voltarLista();
      load();
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
          subtitle={editing ? entityName(editing) : "Cadastre serviços e valores"}
          onBack={voltarLista}
          icon={Stethoscope}
        />
        <ClinicaBelezaPageContent>
          <ClinicaBelezaPanel className="p-6 md:p-8 max-w-lg">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm mb-4">{error}</div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} className={CLINICA_FORM_INPUT} placeholder="Ex.: Limpeza de pele" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duração (min) *</label>
                <input type="number" min={1} value={form.duration} onChange={(e) => setForm((f) => ({ ...f, duration: e.target.value }))} className={CLINICA_FORM_INPUT} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço (R$) *</label>
                <input type="text" inputMode="decimal" value={form.price} onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))} className={CLINICA_FORM_INPUT} placeholder="0,00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} rows={2} className={`${CLINICA_FORM_INPUT} resize-none`} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
                <select value={form.categoria} onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))} className={CLINICA_FORM_INPUT}>
                  <option value="">Selecione...</option>
                  {PROCEDURE_CATEGORIA_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
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

        {loading ? (
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
          <ClinicaBelezaPanel>
            <EntityListTable
              rows={filteredList}
              rowKey={(p) => p.id}
              onRowClick={(p) => abrirEditar(p.id)}
              columns={[
                {
                  key: 'nome',
                  header: 'Nome',
                  render: (p) => <span className="font-medium text-gray-800 dark:text-gray-200">{entityName(p)}</span>,
                },
                {
                  key: 'categoria',
                  header: 'Categoria',
                  className: 'hidden sm:table-cell',
                  render: (p) => <span className="text-gray-600">{procedureCategoria(p) || '—'}</span>,
                },
                {
                  key: 'duracao',
                  header: 'Duração',
                  className: 'hidden md:table-cell',
                  render: (p) => <span>{procedureDuration(p)} min</span>,
                },
                {
                  key: 'preco',
                  header: 'Preço',
                  render: (p) => <span>{formatCurrency(procedurePrice(p))}</span>,
                },
              ]}
              trailingCell={(p) => (
                <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                  <button type="button" onClick={() => abrirEditar(p.id)} className="p-2 text-purple-600 hover:bg-purple-50 rounded" title="Editar">
                    <Pencil size={16} />
                  </button>
                  <button type="button" onClick={() => exclude(p)} className="p-2 text-red-600 hover:bg-red-50 rounded" title="Desativar">
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            />
            <EntityListLoadMore
              hasMore={hasMore}
              loading={loading}
              loadingMore={loadingMore}
              onLoadMore={loadMore}
              loadedCount={filteredList.length}
              totalCount={totalCount}
            />
          </ClinicaBelezaPanel>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>
    </>
  );
}
