"use client";

import { useMemo } from "react";
import { Search } from "lucide-react";

export interface PatientOption {
  id: number;
  nome: string;
  convenio?: number | null;
}

interface Props {
  patients: PatientOption[];
  busca: string;
  onBuscaChange: (value: string) => void;
  patientId: number | "";
  onSelect: (id: number) => void;
  onClear: () => void;
}

export function PatientSearchField({
  patients,
  busca,
  onBuscaChange,
  patientId,
  onSelect,
  onClear,
}: Props) {
  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    if (!q) return [];
    return patients.filter((p) => (p.nome || "").toLowerCase().includes(q)).slice(0, 50);
  }, [busca, patients]);

  const selecionado = patients.find((p) => p.id === patientId) || null;

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Cliente *
      </label>
      <div className="relative mb-2">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={busca}
          onChange={(e) => onBuscaChange(e.target.value)}
          placeholder="Buscar pelo nome..."
          className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors"
        />
      </div>
      {busca.trim() && filtrados.length > 0 && (
        <div className="border border-gray-200 dark:border-neutral-600 rounded-lg overflow-hidden mb-2 max-h-48 overflow-y-auto">
          {filtrados.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => { onSelect(p.id); onBuscaChange(""); }}
              className={`w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors border-b last:border-b-0 border-gray-100 dark:border-neutral-700 ${
                patientId === p.id ? "bg-pink-50 dark:bg-pink-900/20 font-medium" : ""
              }`}
            >
              {p.nome}
            </button>
          ))}
        </div>
      )}
      {busca.trim() && filtrados.length === 0 && (
        <p className="text-xs text-gray-400 mb-2">Nenhum cliente encontrado</p>
      )}
      {selecionado && (
        <div className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <span className="text-sm text-green-700 dark:text-green-400">
            Selecionado: <strong>{selecionado.nome}</strong>
          </span>
          <button
            type="button"
            onClick={onClear}
            className="ml-auto text-xs text-gray-400 hover:text-red-500"
          >
            Trocar
          </button>
        </div>
      )}
    </div>
  );
}
