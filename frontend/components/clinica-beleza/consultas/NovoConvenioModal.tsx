"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { ClinicaBelezaPortraitModal } from "@/components/clinica-beleza/ClinicaBelezaPortraitModal";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";
import {
  CONVENIO_PARTICULAR_LABEL,
  findConvenioParticular,
  isConvenioParticularNome,
  ordenarConveniosComParticularPrimeiro,
} from "@/lib/convenio-precos";
import { toUpperCase } from "@/lib/format-br";

interface NovoConvenioModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

function extractApiError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  for (const val of Object.values(body)) {
    if (Array.isArray(val) && typeof val[0] === "string") return val[0];
    if (typeof val === "string") return val;
  }
  return fallback;
}

export function NovoConvenioModal({ open, onClose, onSuccess }: NovoConvenioModalProps) {
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [nome, setNome] = useState("");
  const [erro, setErro] = useState("");

  const loadConvenios = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.convenios.list();
      setConvenios(Array.isArray(data) ? data : []);
    } catch {
      setErro("Erro ao carregar convênios.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadConvenios();
      setIsCreating(false);
      setNome("");
      setErro("");
    }
  }, [open, loadConvenios]);

  const listaExibida = useMemo(() => {
    const ordenados = ordenarConveniosComParticularPrimeiro(convenios);
    if (findConvenioParticular(convenios)) return ordenados;
    return [
      { id: 0, nome: CONVENIO_PARTICULAR_LABEL, codigo: "PARTICULAR", is_active: true },
      ...ordenados,
    ];
  }, [convenios]);

  const resetForm = () => {
    setNome("");
    setIsCreating(false);
    setErro("");
  };

  const handleClose = () => {
    if (salvando) return;
    onClose();
  };

  const criarConvenio = async () => {
    if (!nome.trim()) {
      setErro("Informe o nome do convênio.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.convenios.create({ nome: nome.trim() });
      resetForm();
      await loadConvenios();
      onSuccess?.();
    } catch (e: unknown) {
      setErro(extractApiError(e, e instanceof Error ? e.message : "Erro ao criar convênio."));
    } finally {
      setSalvando(false);
    }
  };

  const excluirConvenio = async (c: ConvenioItem) => {
    if (isConvenioParticularNome(c.nome)) {
      setErro("O convênio Particular é padrão do sistema e não pode ser excluído.");
      return;
    }
    if (!confirm(`Excluir o convênio "${c.nome}"? Os preços vinculados nos procedimentos serão removidos.`)) {
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await ClinicaBelezaAPI.convenios.delete(c.id);
      await loadConvenios();
      onSuccess?.();
    } catch (e: unknown) {
      setErro(extractApiError(e, e instanceof Error ? e.message : "Erro ao excluir convênio."));
    } finally {
      setSalvando(false);
    }
  };

  return (
    <ClinicaBelezaPortraitModal
      open={open}
      onClose={handleClose}
      closeDisabled={salvando}
      title="Convênios"
      subtitle="Gerencie os convênios aceitos pela clínica"
      footer={
        <div className="flex justify-between gap-2">
          {!isCreating && (
            <button
              type="button"
              onClick={() => {
                setIsCreating(true);
                setNome("");
                setErro("");
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-white"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
            >
              <Plus size={14} />
              Novo convênio
            </button>
          )}
          <button
            type="button"
            onClick={handleClose}
            disabled={salvando}
            className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 ml-auto"
          >
            Fechar
          </button>
        </div>
      }
    >
      {erro && (
        <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          {erro}
        </div>
      )}

      {isCreating && (
        <div className="mb-4 p-3 rounded-lg border-2 border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Novo convênio</p>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Nome do convênio *
          </label>
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(toUpperCase(e.target.value))}
            placeholder="Ex.: Unimed, Santa Casa..."
            autoFocus
            className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 mb-3"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
            Os valores praticados por convênio são definidos na página de Procedimentos.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={criarConvenio}
              disabled={salvando || !nome.trim()}
              className="flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
            >
              {salvando ? <Loader2 size={14} className="animate-spin" /> : null}
              {salvando ? "Criando..." : "Criar convênio"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              disabled={salvando}
              className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">
          <Loader2 size={24} className="animate-spin mx-auto mb-2" />
          Carregando...
        </div>
      ) : (
        <ul className="space-y-2">
          {listaExibida.map((c) => {
            const padrao = isConvenioParticularNome(c.nome);
            const sintetico = c.id === 0;
            return (
              <li
                key={sintetico ? "particular-sistema" : c.id}
                className="flex items-center justify-between gap-2 p-3 rounded-lg bg-gray-50 dark:bg-neutral-800"
              >
                <div className="min-w-0">
                  <span className="font-medium text-sm text-gray-900 dark:text-gray-100 break-words">{c.nome}</span>
                  {padrao && (
                    <span className="ml-1.5 text-xs font-normal px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200 whitespace-nowrap">
                      Padrão
                    </span>
                  )}
                </div>
                {!padrao && !sintetico && (
                  <button
                    type="button"
                    onClick={() => excluirConvenio(c)}
                    disabled={salvando || isCreating}
                    className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40 shrink-0"
                    title="Excluir convênio"
                  >
                    <Trash2 size={14} className="text-red-500" />
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </ClinicaBelezaPortraitModal>
  );
}
