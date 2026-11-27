"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Layers, Plus, Search, Trash2 } from "lucide-react";
import { precoProcedimento } from "@/lib/convenio-precos";
import { entityName, procedureDuration, procedurePrice } from "@/lib/clinica-beleza-entities";
import {
  type CategoriaCatalogItem,
  procedureCategoriaLabel,
  procedureItemCategoriaSlug,
  stripCategoriaPrefixFromNome,
} from "@/lib/clinica-beleza-categories";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";

export interface ProcedureOption {
  id: number;
  name?: string;
  nome?: string;
  duration?: number;
  duracao_minutos?: number;
  price?: string;
  preco?: string | number;
  categoria?: string;
  category?: string;
}

interface Props {
  procedures: ProcedureOption[];
  selectedIds: number[];
  onAdd: (id: number) => void;
  onRemove: (id: number) => void;
  convenioId?: number | "";
  precosMap?: Record<number, number>;
  showSummary?: boolean;
  optional?: boolean;
  label?: string;
  hint?: string;
  categoriasCatalog?: CategoriaCatalogItem[];
  /** Esconde o título interno (quando a section card já tem). */
  hideLabel?: boolean;
}

const CHIPS_VISIVEIS = 4;

export function ProcedureMultiSelect({
  procedures,
  selectedIds,
  onAdd,
  onRemove,
  convenioId = "",
  precosMap = {},
  showSummary = false,
  optional = false,
  label,
  hint,
  categoriasCatalog,
  hideLabel = false,
}: Props) {
  const theme = useClinicaBelezaTheme();
  const params = useParams();
  const lojaSlug = (params?.slug as string) || "";
  const [catalogLoaded, setCatalogLoaded] = useState<CategoriaCatalogItem[]>([]);
  const catalog = categoriasCatalog ?? catalogLoaded;
  const [categoriaAtiva, setCategoriaAtiva] = useState("");
  const [busca, setBusca] = useState("");
  const [pickerAberto, setPickerAberto] = useState(false);
  const [maisCategoriasAberto, setMaisCategoriasAberto] = useState(false);
  const pickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (categoriasCatalog || !lojaSlug) return;
    let cancelled = false;
    void ClinicaBelezaAPI.procedures.categorias
      .list({ slug: lojaSlug })
      .then((data) => {
        if (!cancelled) setCatalogLoaded(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (!cancelled) setCatalogLoaded([]);
      });
    return () => {
      cancelled = true;
    };
  }, [categoriasCatalog, lojaSlug]);

  useEffect(() => {
    if (!pickerAberto && !maisCategoriasAberto) return;
    const onDoc = (e: MouseEvent) => {
      if (!pickerRef.current?.contains(e.target as Node)) {
        setPickerAberto(false);
        setMaisCategoriasAberto(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [pickerAberto, maisCategoriasAberto]);

  const categoriasDisponiveis = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of procedures) {
      if (selectedIds.includes(p.id)) continue;
      const slug = procedureItemCategoriaSlug(p);
      counts.set(slug, (counts.get(slug) || 0) + 1);
    }
    const cards = [...counts.entries()].map(([slug, count]) => ({
      value: slug,
      label: procedureCategoriaLabel(slug, catalog) || slug,
      count,
    }));
    return cards.sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "pt-BR"));
  }, [procedures, selectedIds, catalog]);

  const chipsPrincipais = categoriasDisponiveis.slice(0, CHIPS_VISIVEIS);
  const chipsExtras = categoriasDisponiveis.slice(CHIPS_VISIVEIS);

  const disponiveis = useMemo(() => {
    const q = busca.trim().toLowerCase();
    return procedures.filter((p) => {
      if (selectedIds.includes(p.id)) return false;
      if (categoriaAtiva && procedureItemCategoriaSlug(p) !== categoriaAtiva) return false;
      if (!q) return true;
      return entityName(p).toLowerCase().includes(q);
    });
  }, [procedures, selectedIds, categoriaAtiva, busca]);

  const selecionados = useMemo(
    () =>
      selectedIds
        .map((id) => procedures.find((p) => p.id === id))
        .filter((p): p is ProcedureOption => p != null),
    [selectedIds, procedures],
  );

  const resumo = useMemo(() => {
    let duracao = 0;
    let valor = 0;
    for (const id of selectedIds) {
      const proc = procedures.find((p) => p.id === id);
      if (proc) {
        duracao += procedureDuration(proc);
        const particular = Number(procedurePrice(proc)) || 0;
        valor += precoProcedimento(id, particular, convenioId, precosMap);
      }
    }
    return { duracao, valor };
  }, [selectedIds, procedures, convenioId, precosMap]);

  const rotulo = label ?? "Procedimentos";
  const dica = hint ?? (optional ? "(opcional)" : "");

  const chipClass = (ativo: boolean) =>
    `px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
      ativo
        ? "text-white border-transparent"
        : "border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-300 bg-white dark:bg-neutral-800"
    }`;

  return (
    <div ref={pickerRef} className="space-y-3">
      {!hideLabel ? (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {rotulo}
          {optional ? "" : " *"}{" "}
          {dica ? <span className="font-normal text-gray-400">{dica}</span> : null}
        </label>
      ) : null}

      {categoriasDisponiveis.length > 0 && (
        <div className="flex flex-wrap gap-1.5 items-center">
          <button
            type="button"
            onClick={() => setCategoriaAtiva("")}
            className={chipClass(!categoriaAtiva)}
            style={!categoriaAtiva ? { backgroundColor: theme.primary } : undefined}
          >
            Todas
          </button>
          {chipsPrincipais.map((cat) => (
            <button
              key={cat.value}
              type="button"
              onClick={() => setCategoriaAtiva(cat.value)}
              className={chipClass(categoriaAtiva === cat.value)}
              style={categoriaAtiva === cat.value ? { backgroundColor: theme.primary } : undefined}
            >
              {cat.label} ({cat.count})
            </button>
          ))}
          {chipsExtras.length > 0 ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setMaisCategoriasAberto((v) => !v)}
                className={chipClass(chipsExtras.some((c) => c.value === categoriaAtiva))}
                style={
                  chipsExtras.some((c) => c.value === categoriaAtiva)
                    ? { backgroundColor: theme.primary }
                    : undefined
                }
              >
                + Categorias
              </button>
              {maisCategoriasAberto ? (
                <div className="absolute z-20 mt-1 left-0 min-w-[200px] max-h-48 overflow-y-auto rounded-xl border border-gray-200 dark:border-neutral-600 bg-white dark:bg-neutral-900 shadow-lg p-1.5">
                  {chipsExtras.map((cat) => (
                    <button
                      key={cat.value}
                      type="button"
                      onClick={() => {
                        setCategoriaAtiva(cat.value);
                        setMaisCategoriasAberto(false);
                      }}
                      className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-gray-50 dark:hover:bg-neutral-800"
                    >
                      {cat.label} ({cat.count})
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
        <input
          type="search"
          value={busca}
          onChange={(e) => {
            setBusca(e.target.value);
            setPickerAberto(true);
          }}
          onFocus={() => setPickerAberto(true)}
          placeholder="Buscar procedimento..."
          className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700"
        />
      </div>

      {selecionados.length > 0 ? (
        <div className="space-y-2">
          {selecionados.map((proc) => {
            const slug = procedureItemCategoriaSlug(proc);
            const particular = Number(procedurePrice(proc)) || 0;
            const valorProc = precoProcedimento(proc.id, particular, convenioId, precosMap);
            const dur = procedureDuration(proc);
            return (
              <div
                key={proc.id}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl border border-gray-100 dark:border-neutral-700 bg-gray-50/80 dark:bg-neutral-800/40"
              >
                <span
                  className="flex h-9 w-9 items-center justify-center rounded-lg shrink-0"
                  style={{ backgroundColor: theme.primaryLight, color: theme.primary }}
                >
                  <Layers className="h-4 w-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                    {stripCategoriaPrefixFromNome(entityName(proc), slug, catalog)}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {procedureCategoriaLabel(slug, catalog)}
                    {dur > 0 ? ` · ${dur} min` : ""}
                    {valorProc > 0 ? ` · ${formatCurrency(valorProc)}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => onRemove(proc.id)}
                  className="p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
                  aria-label="Remover procedimento"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            );
          })}
        </div>
      ) : optional ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Nenhum procedimento — horário como <strong className="font-medium">somente consulta</strong>.
        </p>
      ) : null}

      <div className="relative">
        <button
          type="button"
          onClick={() => setPickerAberto((v) => !v)}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border-2 border-dashed text-sm font-semibold transition-colors"
          style={{ borderColor: theme.primary, color: theme.primary }}
        >
          <Plus className="h-4 w-4" />
          Adicionar procedimento
        </button>
        {pickerAberto ? (
          <div className="absolute z-20 mt-1.5 left-0 right-0 max-h-52 overflow-y-auto rounded-xl border border-gray-200 dark:border-neutral-600 bg-white dark:bg-neutral-900 shadow-xl">
            {disponiveis.length === 0 ? (
              <p className="px-3 py-3 text-sm text-gray-500">Nenhum procedimento nesta filtragem.</p>
            ) : (
              disponiveis.map((p) => {
                const slug = procedureItemCategoriaSlug(p);
                const particular = Number(procedurePrice(p)) || 0;
                const valor = precoProcedimento(p.id, particular, convenioId, precosMap);
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      onAdd(p.id);
                      setBusca("");
                      setPickerAberto(false);
                    }}
                    className="w-full text-left px-3 py-2.5 border-b last:border-b-0 border-gray-100 dark:border-neutral-700 hover:bg-gray-50 dark:hover:bg-neutral-800"
                  >
                    <span className="block text-sm font-medium text-gray-900 dark:text-gray-100">
                      {stripCategoriaPrefixFromNome(entityName(p), slug, catalog)}
                    </span>
                    <span className="text-xs text-gray-500">
                      {procedureCategoriaLabel(slug, catalog)}
                      {procedureDuration(p) > 0 ? ` · ${procedureDuration(p)} min` : ""}
                      {valor > 0 ? ` · ${formatCurrency(valor)}` : ""}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        ) : null}
      </div>

      {showSummary && selectedIds.length > 1 ? (
        <div className="flex items-center justify-between px-1 text-sm text-gray-600 dark:text-gray-400">
          <span>
            Duração: <strong>{resumo.duracao} min</strong>
          </span>
          {resumo.valor > 0 ? (
            <span>
              Valor: <strong>{formatCurrency(resumo.valor)}</strong>
            </span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
