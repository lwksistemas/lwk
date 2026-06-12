"use client";

import { useEffect, useState } from "react";
import { Loader2, Save, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { toUpperCase } from "@/lib/format-br";

interface NovoConvenioModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function NovoConvenioModal({ open, onClose, onSuccess }: NovoConvenioModalProps) {
  const [nome, setNome] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (open) {
      setNome("");
      setErro("");
    }
  }, [open]);

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
      onSuccess?.();
      onClose();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao criar convênio.");
    } finally {
      setSalvando(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">Novo convênio</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Informe o nome; o código será gerado automaticamente
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={salvando}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500 disabled:opacity-40"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-6 py-5">
          {erro && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
              {erro}
            </div>
          )}
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Nome do convênio *
          </label>
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(toUpperCase(e.target.value))}
            placeholder="Ex.: Unimed, Particular, Santa Casa..."
            autoFocus
            className="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">
            Os valores praticados por convênio são definidos na página de Procedimentos.
          </p>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex flex-col-reverse sm:flex-row gap-3 justify-end">
          <button
            type="button"
            onClick={handleClose}
            disabled={salvando}
            className="py-2.5 px-6 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={criarConvenio}
            disabled={salvando || !nome.trim()}
            className="flex items-center justify-center gap-2 py-2.5 px-6 rounded-lg text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            {salvando ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {salvando ? "Criando..." : "Criar convênio"}
          </button>
        </div>
      </div>
    </div>
  );
}
