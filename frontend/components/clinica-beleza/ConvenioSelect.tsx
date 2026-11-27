"use client";

import type { LucideIcon } from "lucide-react";
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
  /** Ícone à esquerda do select (ex.: modal de agendamento). */
  labelIcon?: LucideIcon;
}

export function ConvenioSelect({
  convenios,
  value,
  onChange,
  hint = "Define os preços dos procedimentos. Sugerido pelo cadastro do cliente, se houver.",
  className = "w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-neutral-600 rounded-lg dark:bg-neutral-700 focus:ring-2 focus:ring-pink-200 dark:focus:ring-pink-800 focus:border-pink-400 outline-none transition-colors",
  labelIcon: LabelIcon,
}: Props) {
  const particular = findConvenioParticular(convenios);
  const lista = ordenarConveniosComParticularPrimeiro(convenios);

  return (
    <div>
      <label
        className={`block font-medium text-gray-700 dark:text-gray-300 ${
          LabelIcon ? "text-xs text-slate-600 dark:text-gray-400 mb-0.5" : "text-sm mb-2"
        }`}
      >
        Convênio
      </label>
      <div className={LabelIcon ? "relative" : undefined}>
        {LabelIcon ? (
          <LabelIcon className="pointer-events-none absolute left-2.5 top-1/2 z-[1] h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
        ) : null}
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
      </div>
      {hint && <p className="text-xs text-gray-400 mt-1.5">{hint}</p>}
    </div>
  );
}
