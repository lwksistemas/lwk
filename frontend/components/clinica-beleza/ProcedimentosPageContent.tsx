"use client";

/**
 * Cadastro de Procedimentos - Clínica da Beleza
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Pencil, Trash2, X } from "lucide-react";
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
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import {
  bloquearCriacaoDuplicadaOffline,
  deveVerificarDuplicataOffline,
  gerarIdTemporarioOffline,
  isBrowserOffline,
  isFetchNetworkError,
  temDuplicataNaLista,
} from "@/lib/clinica-beleza-offline";
import { buscarProcedimentosOffline, salvarProcedimentosOffline, adicionarNaFilaSync, getLojaSlug } from "@/lib/offline-db";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from '@/components/clinica-beleza/ClinicaBelezaPageHeaderContext';
import { ClinicaBelezaRelatedLinks } from "@/components/clinica-beleza/ClinicaBelezaRelatedLinks";
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
  const router = useRouter();
  const slug = params.slug as string;
  const [list, setList] = useState<Procedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Procedure | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    price: "",
    duration: "30",
    categoria: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [showAllCategories, setShowAllCategories] = useState(false);
  useClinicaBelezaDark();

  const moduleKey = defaultCategoria || "";
  const presetCategoria = defaultCategoriaForModule(moduleKey) || defaultCategoria;

  const load = async () => {
    setLoading(true);
    try {
      if (!navigator.onLine) {
        const data = await buscarProcedimentosOffline();
        setList(Array.isArray(data) ? (data as Procedure[]) : []);
      } else {
        const qs = moduleKey && !showAllCategories ? `?categoria=${encodeURIComponent(moduleKey)}` : "";
        const res = await clinicaBelezaFetch(`/procedures${qs}`);
        const data = await res.json();
        if (res.ok) {
          const arr = Array.isArray(data) ? data : [];
          setList(arr);
          await salvarProcedimentosOffline(arr);
        } else setList([]);
      }
    } catch {
      setList([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (defaultCategoria) {
      setForm((f) => ({ ...f, categoria: defaultCategoria }));
    }
  }, [defaultCategoria]);

  useEffect(() => {
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showAllCategories, moduleKey]);

  useEffect(() => {
    const onSyncDone = () => {
      if (navigator.onLine) {
        // Aguardar um pouco para garantir que o backend processou
        setTimeout(() => load(), 500);
      }
    };
    window.addEventListener("offline-sync-done", onSyncDone);
    return () => window.removeEventListener("offline-sync-done", onSyncDone);
  }, []);

  const openNew = () => {
    setEditing(null);
    setForm({
      name: "",
      description: "",
      price: "",
      duration: "30",
      categoria: presetCategoria,
    });
    setError("");
    setShowModal(true);
  };

  const openEdit = (p: Procedure) => {
    setEditing(p);
    setForm({
      name: entityName(p),
      description: procedureDescription(p) || "",
      price: String(procedurePrice(p)),
      duration: String(procedureDuration(p)),
      categoria: procedureCategoria(p),
    });
    setError("");
    setShowModal(true);
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
        const lojaSlug = getLojaSlug();

        if (deveVerificarDuplicataOffline(editing)) {
          const jaExisteLocal = temDuplicataNaLista(list, (p) =>
            entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
          );
          if (jaExisteLocal) {
            setError("Este procedimento já foi adicionado. Aguarde a sincronização.");
            setSaving(false);
            return;
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
              ? { ...p, name: body.name, description: body.description, price: body.price, duration: body.duration }
              : p
          );
          setList(updatedList);
          await salvarProcedimentosOffline(updatedList);
        } else {
          await adicionarNaFilaSync({ tipo: "procedimento", payload: { action: "create", body }, lojaSlug });
          const tempId = gerarIdTemporarioOffline();
          const newProc: Procedure = {
            id: tempId,
            name: body.name,
            description: body.description,
            price: body.price,
            duration: body.duration,
            categoria: body.category,
            active: true,
          };
          const updatedList = [newProc, ...list];
          setList(updatedList);
          await salvarProcedimentosOffline(updatedList);
        }
        setShowModal(false);
        alert("Salvo offline. O procedimento será sincronizado quando você estiver online.");
      } catch (err) {
        logger.warn("Erro ao salvar offline:", err);
        setError("Erro ao salvar localmente. Tente novamente.");
      }
      setSaving(false);
      return;
    }

    try {
      if (editing) {
        const res = await clinicaBelezaFetch(`/procedures/${editing.id}/`, {
          method: "PUT",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(formatProcedimentoApiErrors(err as Record<string, unknown>) || "Erro ao atualizar");
        }
      } else {
        const res = await clinicaBelezaFetch("/procedures/", {
          method: "POST",
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(formatProcedimentoApiErrors(err as Record<string, unknown>) || "Erro ao cadastrar");
        }
      }
      setShowModal(false);
      load();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Erro ao salvar";
      if (isFetchNetworkError(msg)) {
        try {
          const lojaSlug = getLojaSlug();

          if (bloquearCriacaoDuplicadaOffline(editing, list, (p) =>
            entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
          )) {
            setError("Este procedimento já foi adicionado offline. Aguarde a sincronização.");
            setSaving(false);
            return;
          }
          
          if (editing && editing.id > 0) {
            await adicionarNaFilaSync({
              tipo: "procedimento",
              payload: { action: "update", id: editing.id, body },
              lojaSlug,
            });
            const updatedList = list.map((p) =>
              p.id === editing.id
                ? { ...p, name: body.name, description: body.description, price: body.price, duration: body.duration }
                : p
            );
            setList(updatedList);
            await salvarProcedimentosOffline(updatedList);
          } else {
            await adicionarNaFilaSync({ tipo: "procedimento", payload: { action: "create", body }, lojaSlug });
            const tempId = gerarIdTemporarioOffline();
            const newProc: Procedure = {
              id: tempId,
              name: body.name,
              description: body.description,
              price: body.price,
              duration: body.duration,
              active: true,
            };
            const updatedList = [newProc, ...list];
            setList(updatedList);
            await salvarProcedimentosOffline(updatedList);
          }
          setShowModal(false);
          alert("Sem conexão. Procedimento salvo offline e será sincronizado quando você estiver online.");
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
      await clinicaBelezaFetch(`/procedures/${p.id}/`, { method: "DELETE" });
      load();
    } catch {
      alert("Erro ao desativar.");
    }
  };

  useClinicaBelezaDark();

  const activeList = list.filter((p) => entityActive(p));
  const filteredList =
    moduleKey && !showAllCategories
      ? activeList.filter((p) => procedureMatchesModule(procedureCategoria(p), moduleKey))
      : activeList;
  const hiddenByCategoryCount =
    moduleKey && !showAllCategories ? activeList.length - filteredList.length : 0;

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title={title}
        subtitle={subtitle}
        backHref={backHref}
        newLabel="Novo Procedimento"
        onNew={openNew}
      />
      <ClinicaBelezaPageContent>

        {moduleKey && (
          <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
            <span className="px-2 py-1 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200">
              Filtro: {moduleKey === 'soroterapia' ? 'Soroterapia' : 'Estética'}
            </span>
            {hiddenByCategoryCount > 0 && (
              <button
                type="button"
                onClick={() => setShowAllCategories(!showAllCategories)}
                className="text-purple-700 dark:text-purple-300 underline"
              >
                {showAllCategories
                  ? 'Mostrar só deste módulo'
                  : `Mostrar todos (${activeList.length} cadastrados, ${hiddenByCategoryCount} em outras categorias)`}
              </button>
            )}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>
        ) : filteredList.length === 0 ? (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl p-8 text-center text-gray-500 dark:text-gray-400">
            {activeList.length === 0 ? (
              <>Nenhum procedimento cadastrado. Clique em &quot;Novo Procedimento&quot; para começar.</>
            ) : (
              <>
                Nenhum procedimento com categoria &quot;{presetCategoria}&quot;.
                {hiddenByCategoryCount > 0 && (
                  <>
                    {' '}
                    Existem {activeList.length} procedimento(s) em outras categorias —{' '}
                    <button
                      type="button"
                      className="text-purple-600 underline"
                      onClick={() => setShowAllCategories(true)}
                    >
                      ver todos
                    </button>
                    .
                  </>
                )}
              </>
            )}
          </div>
        ) : (
          <div className="bg-white/80 dark:bg-neutral-800/70 rounded-xl shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-gray-300">
                  <tr>
                    <th className="text-left p-3">Nome</th>
                    <th className="text-left p-3">Categoria</th>
                    <th className="text-left p-3">Duração</th>
                    <th className="text-left p-3">Preço</th>
                    <th className="w-24 p-3">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredList.map((p) => (
                    <tr key={p.id} className="border-t border-gray-100 dark:border-neutral-700">
                      <td className="p-3 font-medium text-gray-800 dark:text-gray-200">{entityName(p)}</td>
                      <td className="p-3 text-gray-600 dark:text-gray-400">{procedureCategoria(p) || '—'}</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{procedureDuration(p)} min</td>
                      <td className="p-3 text-gray-700 dark:text-gray-300">{formatCurrency(procedurePrice(p))}</td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => openEdit(p)}
                            className="p-2 text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 rounded"
                            title="Editar"
                          >
                            <Pencil size={18} />
                          </button>
                          <button
                            onClick={() => exclude(p)}
                            className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                            title="Desativar"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        <ClinicaBelezaRelatedLinks slug={slug} items={relatedLinks} />
      </ClinicaBelezaPageContent>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md border dark:border-neutral-700">
            <div className="flex justify-between items-center p-4 border-b dark:border-neutral-700">
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {editing ? "Editar Procedimento" : "Novo Procedimento"}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded">
                <X size={20} />
              </button>
            </div>
            <div className="p-4 space-y-3">
              {error && (
                <div className="p-2 rounded bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-sm">{error}</div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="Ex.: Limpeza de pele"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Duração (min) *</label>
                <input
                  type="number"
                  min={1}
                  value={form.duration}
                  onChange={(e) => setForm((f) => ({ ...f, duration: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Preço (R$) *</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={form.price}
                  onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                  placeholder="0,00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Descrição</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 resize-none"
                  placeholder="Descrição opcional"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Categoria</label>
                <select
                  value={form.categoria}
                  onChange={(e) => setForm((f) => ({ ...f, categoria: e.target.value }))}
                  className="w-full px-3 py-2 border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Selecione...</option>
                  {PROCEDURE_CATEGORIA_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex gap-2 p-4 border-t dark:border-neutral-700">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-700 text-gray-700 dark:text-gray-300"
              >
                Cancelar
              </button>
              <button
                onClick={save}
                disabled={saving}
                className="flex-1 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
              >
                {saving ? "Salvando..." : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      )}

    </>
  );
}
