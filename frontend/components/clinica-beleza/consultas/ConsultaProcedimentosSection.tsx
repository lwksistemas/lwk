"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, ChevronDown, ChevronUp, Loader2, Plus, Trash2 } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { toUpperCase } from "@/lib/format-br";
import type { ConsultaProcedimento } from "./consultas-types";

interface ProcedureOption {
  id: number;
  nome: string;
}

interface AppointmentProcedureItem {
  id: number;
  procedure: number;
  procedure_name: string;
  valor_efetivo: number;
}

const selectClass =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";

function extractApiError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  return fallback;
}

/** Controles compactos — inclusão/remoção dentro de Notas do atendimento (sem card grande). */
export function ConsultaProcedimentosSection({
  consultaId,
  somenteLeitura,
  procedimentosIniciais = [],
  onChanged,
}: {
  consultaId: number;
  somenteLeitura: boolean;
  procedimentosIniciais?: ConsultaProcedimento[];
  onChanged?: (consulta?: Record<string, unknown>) => void;
}) {
  const [itens, setItens] = useState<AppointmentProcedureItem[]>([]);
  const [catalogo, setCatalogo] = useState<ProcedureOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showManageList, setShowManageList] = useState(false);
  const [procedureId, setProcedureId] = useState<number | "">("");
  const [erro, setErro] = useState("");
  const [avisoTermo, setAvisoTermo] = useState("");

  const mapFromConsulta = useCallback((lista: ConsultaProcedimento[]): AppointmentProcedureItem[] => {
    return lista
      .filter((p) => p.appointment_procedure_id)
      .map((p) => ({
        id: p.appointment_procedure_id!,
        procedure: p.id,
        procedure_name: p.nome,
        valor_efetivo: Number(p.valor ?? 0),
      }));
  }, []);

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro("");
    try {
      const [lista, procs] = await Promise.all([
        ClinicaBelezaAPI.consultas.procedimentos.list(consultaId),
        ClinicaBelezaAPI.procedures.list({ active: true, page_size: 500 }),
      ]);
      setItens(Array.isArray(lista) ? lista : mapFromConsulta(procedimentosIniciais));
      setCatalogo(
        procs
          .map((p) => ({ id: p.id, nome: String((p as ProcedureOption).nome || "") }))
          .filter((p) => p.nome)
          .sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR")),
      );
    } catch {
      setItens(mapFromConsulta(procedimentosIniciais));
      setErro("Erro ao carregar procedimentos.");
    } finally {
      setLoading(false);
    }
  }, [consultaId, mapFromConsulta, procedimentosIniciais]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const idsJaAdicionados = useMemo(() => new Set(itens.map((i) => i.procedure)), [itens]);
  const opcoesDisponiveis = useMemo(
    () => catalogo.filter((p) => !idsJaAdicionados.has(p.id)),
    [catalogo, idsJaAdicionados],
  );

  const adicionar = async () => {
    if (!procedureId) {
      setErro("Selecione um procedimento.");
      return;
    }
    setSaving(true);
    setErro("");
    setAvisoTermo("");
    try {
      const res = await ClinicaBelezaAPI.consultas.procedimentos.add(consultaId, Number(procedureId));
      const lista = await ClinicaBelezaAPI.consultas.procedimentos.list(consultaId);
      setItens(Array.isArray(lista) ? lista : []);
      setProcedureId("");
      setShowAddForm(false);
      setShowManageList(false);
      onChanged?.(res.consulta);

      const added = (res.consulta?.procedures_list as ConsultaProcedimento[] | undefined)?.find(
        (p) => p.id === Number(procedureId),
      );
      if (added?.exige_termo) {
        setAvisoTermo("Procedimento incluído. Envie o termo de consentimento na aba correspondente.");
      }
    } catch (e: unknown) {
      setErro(extractApiError(e, "Erro ao adicionar procedimento."));
    } finally {
      setSaving(false);
    }
  };

  const remover = async (item: AppointmentProcedureItem) => {
    if (!confirm(`Remover "${item.procedure_name}" deste atendimento?`)) return;
    setSaving(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.consultas.procedimentos.remove(consultaId, item.id);
      const lista = await ClinicaBelezaAPI.consultas.procedimentos.list(consultaId);
      const fresh = await ClinicaBelezaAPI.consultas.get(consultaId);
      setItens(Array.isArray(lista) ? lista : []);
      onChanged?.(fresh as Record<string, unknown>);
      if ((Array.isArray(lista) ? lista : []).length === 0) setShowManageList(false);
    } catch (e: unknown) {
      setErro(extractApiError(e, "Erro ao remover procedimento."));
    } finally {
      setSaving(false);
    }
  };

  if (somenteLeitura) return null;

  const podeAdicionar = !loading && opcoesDisponiveis.length > 0;
  if (!loading && itens.length === 0 && !podeAdicionar && !showAddForm && !erro && !avisoTermo) {
    return null;
  }

  const toolbar = (
    <div className="flex flex-wrap items-center gap-2">
      {itens.length > 0 && (
        <button
          type="button"
          onClick={() => {
            setShowManageList((v) => !v);
            setShowAddForm(false);
          }}
          className="inline-flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
        >
          {showManageList ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          Gerenciar ({itens.length})
        </button>
      )}
      {podeAdicionar && (
        <button
          type="button"
          onClick={() => {
            setShowAddForm((v) => !v);
            setShowManageList(false);
            setErro("");
            setAvisoTermo("");
          }}
          disabled={saving}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-neutral-700 disabled:opacity-50"
        >
          <Plus size={14} />
          Procedimento
        </button>
      )}
    </div>
  );

  return (
    <div className="mb-4 space-y-3">
      <div className="flex flex-wrap items-center justify-end gap-2">{toolbar}</div>

      {erro && (
        <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs">
          {erro}
        </div>
      )}

      {avisoTermo && (
        <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-xs flex gap-2">
          <AlertTriangle size={14} className="shrink-0 mt-0.5" />
          <span>{avisoTermo}</span>
        </div>
      )}

      {showAddForm && (
        <div className="p-3 rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/40 dark:bg-purple-900/10 space-y-2">
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Incluir procedimento</label>
          <select
            value={procedureId}
            onChange={(e) => setProcedureId(e.target.value ? Number(e.target.value) : "")}
            className={selectClass}
            autoFocus
          >
            <option value="">Selecione...</option>
            {opcoesDisponiveis.map((p) => (
              <option key={p.id} value={p.id}>
                {toUpperCase(p.nome)}
              </option>
            ))}
          </select>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={adicionar}
              disabled={saving || !procedureId}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : null}
              Incluir
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAddForm(false);
                setProcedureId("");
                setErro("");
              }}
              disabled={saving}
              className="px-3 py-1.5 text-xs text-gray-600 dark:text-gray-400"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {showManageList && itens.length > 0 && (
        <ul className="rounded-lg border border-gray-200 dark:border-neutral-700 divide-y divide-gray-100 dark:divide-neutral-700 bg-gray-50/50 dark:bg-neutral-800/50">
          {itens.map((item) => (
            <li key={item.id} className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
              <span className="font-medium text-gray-800 dark:text-gray-200 truncate">
                {toUpperCase(item.procedure_name)}
              </span>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs tabular-nums text-gray-500">{formatCurrency(item.valor_efetivo)}</span>
                <button
                  type="button"
                  onClick={() => remover(item)}
                  disabled={saving}
                  className="p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
                  title="Remover"
                >
                  <Trash2 size={13} className="text-red-500" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
