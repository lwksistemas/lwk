"use client";

import {
  CONVENIO_PARTICULAR_LABEL,
  findConvenioParticular,
  ordenarConveniosComParticularPrimeiro,
} from "@/lib/convenio-precos";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";

interface Props {
  convenios: ConvenioItem[];
  value: number | "";
  onChange: (id: number | "") => void;
  hint?: string;
  className?: string;
}

export function ConvenioSelect({
  convenios,
  value,
  onChange,
  hint = "Define os preços dos procedimentos. Sugerido pelo cadastro do cliente, se houver.",
  className = "w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors",
}: Props) {
  const particular = findConvenioParticular(convenios);
  const lista = ordenarConveniosComParticularPrimeiro(convenios);

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Convênio
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
        className={className}
      >
        {!particular && <option value="">{CONVENIO_PARTICULAR_LABEL}</option>}
        {lista.map((c) => (
          <option key={c.id} value={c.id}>{c.nome}</option>
        ))}
      </select>
      {hint && <p className="text-xs text-gray-400 mt-1.5">{hint}</p>}
    </div>
  );
}
