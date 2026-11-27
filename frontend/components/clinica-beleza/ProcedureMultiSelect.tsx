"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Layers, Plus, Search, Trash2, X } from "lucide-react";
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
import {
  estadoAposAdicionarProcedimento,
  estadoFecharListaDisponiveis,
  estadoToggleCategoria,
  mostrarListaDisponiveis,
} from "@/components/clinica-beleza/procedure-picker-state";

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
  const [listaAberta, setListaAberta] = useState(false);
  const [maisCategoriasAberto, setMaisCategoriasAberto] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const filterState = { categoriaAtiva, busca, listaAberta };

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
    if (!maisCategoriasAberto) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setMaisCategoriasAberto(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [maisCategoriasAberto]);

  const categoriasDisponiveis = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of procedures) {
      const slug = procedureItemCategoriaSlug(p);
      counts.set(slug, (counts.get(slug) || 0) + 1);
    }
    const cards = [...counts.entries()].map(([slug, count]) => ({
      value: slug,
      label: procedureCategoriaLabel(slug, catalog) || slug,
      count,
    }));
    return cards.sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "pt-BR"));
  }, [procedures, catalog]);

  const chipsPrincipais = categoriasDisponiveis.slice(0, CHIPS_VISIVEIS);
  const chipsExtras = categoriasDisponiveis.slice(CHIPS_VISIVEIS);

  const mostrarDisponiveis = mostrarListaDisponiveis(filterState);

  const disponiveis = useMemo(() => {
    if (!mostrarDisponiveis) return [];
    const q = busca.trim().toLowerCase();
    return procedures.filter((p) => {
      if (selectedIds.includes(p.id)) return false;
      if (categoriaAtiva && procedureItemCategoriaSlug(p) !== categoriaAtiva) return false;
      if (q && !entityName(p).toLowerCase().includes(q)) return false;
      return true;
    });
  }, [procedures, selectedIds, categoriaAtiva, busca, mostrarDisponiveis]);

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
    `shrink-0 px-2.5 py-1 rounded-full text-[13px] font-medium border transition-colors whitespace-nowrap ${
      ativo
        ? "text-white border-transparent"
        : "border-[#E9D5E3] dark:border-neutral-600 text-gray-600 dark:text-gray-300 bg-white dark:bg-neutral-800"
    }`;

  const aplicarFiltro = (next: typeof filterState) => {
    setCategoriaAtiva(next.categoriaAtiva);
    setBusca(next.busca);
    setListaAberta(next.listaAberta);
  };

  const adicionar = (id: number) => {
    onAdd(id);
    aplicarFiltro(estadoAposAdicionarProcedimento());
    setMaisCategoriasAberto(false);
  };

  const fecharLista = () => {
    aplicarFiltro(estadoFecharListaDisponiveis(filterState));
    setMaisCategoriasAberto(false);
  };

  const ativarCategoria = (categoriaClicada: string) => {
    aplicarFiltro(estadoToggleCategoria(filterState, categoriaClicada));
    setMaisCategoriasAberto(false);
  };

  return (
    <div ref={rootRef} className="space-y-2">
      {!hideLabel ? (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {rotulo}
          {optional ? "" : " *"}{" "}
          {dica ? <span className="font-normal text-gray-400">{dica}</span> : null}
        </label>
      ) : null}

      {categoriasDisponiveis.length > 0 ? (
        <div className="flex w-full min-w-0 items-center gap-1.5">
          <div className="flex min-w-0 flex-1 basis-0 items-center gap-1.5 overflow-x-auto pb-0.5 scrollbar-thin">
            <button
              type="button"
              onClick={() => ativarCategoria("")}
              className={chipClass(listaAberta && !categoriaAtiva)}
              style={listaAberta && !categoriaAtiva ? { backgroundColor: theme.primary } : undefined}
            >
              Todas
            </button>
            {chipsPrincipais.map((cat) => (
              <button
                key={cat.value}
                type="button"
                onClick={() => ativarCategoria(cat.value)}
                className={chipClass(categoriaAtiva === cat.value)}
                style={categoriaAtiva === cat.value ? { backgroundColor: theme.primary } : undefined}
              >
                {cat.label} ({cat.count})
              </button>
            ))}
          </div>
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => {
                if (chipsExtras.length === 0) return;
                setMaisCategoriasAberto((v) => !v);
              }}
              className={chipClass(chipsExtras.some((c) => c.value === categoriaAtiva))}
              style={
                chipsExtras.some((c) => c.value === categoriaAtiva)
                  ? { backgroundColor: theme.primary }
                  : undefined
              }
              title={chipsExtras.length === 0 ? "Nenhuma categoria adicional" : "Mais categorias"}
            >
              + Categorias
            </button>
            {maisCategoriasAberto && chipsExtras.length > 0 ? (
              <div className="absolute z-20 mt-1 right-0 min-w-[200px] max-h-48 overflow-y-auto rounded-xl border border-gray-200 dark:border-neutral-600 bg-white dark:bg-neutral-900 shadow-lg p-1.5">
                {chipsExtras.map((cat) => (
                  <button
                    key={cat.value}
                    type="button"
                    onClick={() => ativarCategoria(cat.value)}
                    className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs hover:bg-gray-50 dark:hover:bg-neutral-800"
                  >
                    {cat.label} ({cat.count})
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
        <input
          type="search"
          value={busca}
          onChange={(e) => {
            const value = e.target.value;
            setBusca(value);
            if (value.trim()) setListaAberta(true);
          }}
          placeholder="Buscar procedimento..."
          className="w-full pl-8 pr-9 py-1.5 text-sm border border-[#E9D5E3] dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 min-h-[36px]"
        />
        {busca || listaAberta ? (
          <button
            type="button"
            onClick={fecharLista}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded text-gray-400 hover:text-gray-600"
            aria-label="Fechar lista de procedimentos"
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {mostrarDisponiveis ? (
        <div className="max-h-32 overflow-y-auto rounded-xl border border-[#E9D5E3] dark:border-neutral-600 bg-white dark:bg-neutral-900 divide-y divide-gray-100 dark:divide-neutral-700">
          {disponiveis.length === 0 ? (
            <p className="px-3 py-2.5 text-xs text-gray-500">Nenhum procedimento nesta filtragem.</p>
          ) : (
            disponiveis.map((p) => {
              const slug = procedureItemCategoriaSlug(p);
              const particular = Number(procedurePrice(p)) || 0;
              const valor = precoProcedimento(p.id, particular, convenioId, precosMap);
              const dur = procedureDuration(p);
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => adicionar(p.id)}
                  className="w-full flex items-center gap-2.5 px-2.5 py-1.5 text-left hover:bg-gray-50 dark:hover:bg-neutral-800 min-h-[44px]"
                >
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                      {stripCategoriaPrefixFromNome(entityName(p), slug, catalog)}
                    </span>
                    <span className="text-xs text-slate-500">
                      {procedureCategoriaLabel(slug, catalog)}
                      {dur > 0 ? ` · ${dur} min` : ""}
                    </span>
                  </span>
                  {valor > 0 ? (
                    <span className="text-[13px] font-bold shrink-0" style={{ color: theme.primary }}>
                      {formatCurrency(valor)}
                    </span>
                  ) : null}
                  <span
                    className="flex h-6 w-6 items-center justify-center rounded-full shrink-0 text-white"
                    style={{ backgroundColor: theme.primary }}
                    aria-hidden
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </span>
                </button>
              );
            })
          )}
        </div>
      ) : null}

      {selecionados.length > 0 ? (
        <div className={`space-y-1 ${mostrarDisponiveis ? "mt-0.5" : ""}`}>
          <p className="text-xs font-medium text-slate-500 dark:text-gray-400">
            Procedimentos selecionados ({selecionados.length})
          </p>
          <div className="max-h-[118px] overflow-y-auto space-y-1.5 pr-0.5">
            {selecionados.map((proc) => {
              const slug = procedureItemCategoriaSlug(proc);
              const particular = Number(procedurePrice(proc)) || 0;
              const valorProc = precoProcedimento(proc.id, particular, convenioId, precosMap);
              const dur = procedureDuration(proc);
              return (
                <div
                  key={proc.id}
                  className="flex items-center gap-2.5 px-2.5 rounded-xl border border-[#E9D5E3] dark:border-neutral-700 bg-[#FAF8FA] dark:bg-neutral-800/40 h-[52px] min-h-[48px] max-h-[56px]"
                >
                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-lg shrink-0"
                    style={{ backgroundColor: theme.primaryLight, color: theme.primary }}
                  >
                    <Layers className="h-3.5 w-3.5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate leading-tight">
                      {stripCategoriaPrefixFromNome(entityName(proc), slug, catalog)}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-gray-400 truncate mt-0.5">
                      {procedureCategoriaLabel(slug, catalog)}
                      {dur > 0 ? ` · ${dur} min` : ""}
                    </p>
                  </div>
                  {valorProc > 0 ? (
                    <span className="text-sm font-bold shrink-0 tabular-nums" style={{ color: theme.primary }}>
                      {formatCurrency(valorProc)}
                    </span>
                  ) : null}
                  <button
                    type="button"
                    onClick={() => onRemove(proc.id)}
                    className="p-1 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg shrink-0"
                    aria-label="Remover procedimento"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ) : optional && !mostrarDisponiveis ? (
        <p className="text-xs leading-snug text-slate-500 dark:text-gray-400">
          Categoria ou busca para adicionar · opcional na consulta.
        </p>
      ) : null}

      {showSummary && selectedIds.length > 1 ? (
        <div className="flex items-center justify-between px-1 text-xs text-gray-600 dark:text-gray-400">
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
