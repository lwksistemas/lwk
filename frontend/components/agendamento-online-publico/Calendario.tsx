"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];
const SEMANA = ["D", "S", "T", "Q", "Q", "S", "S"];

function pad(n: number) {
  return String(n).padStart(2, "0");
}

export function ymd(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function parseYmd(s: string): Date {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(y, (m || 1) - 1, d || 1);
}

export function Calendario({
  diasDisponiveis,
  selecionado,
  onSelect,
}: {
  diasDisponiveis: string[];
  selecionado: string;
  onSelect: (dia: string) => void;
}) {
  const disponiveis = useMemo(() => new Set(diasDisponiveis), [diasDisponiveis]);
  const primeiro = diasDisponiveis[0] ? parseYmd(diasDisponiveis[0]) : new Date();
  const ultimo = diasDisponiveis.length ? parseYmd(diasDisponiveis[diasDisponiveis.length - 1]) : primeiro;
  const [cursor, setCursor] = useState(() =>
    selecionado ? new Date(parseYmd(selecionado).getFullYear(), parseYmd(selecionado).getMonth(), 1) : new Date(primeiro.getFullYear(), primeiro.getMonth(), 1),
  );

  const ano = cursor.getFullYear();
  const mes = cursor.getMonth();
  const inicioSemana = new Date(ano, mes, 1).getDay();
  const diasNoMes = new Date(ano, mes + 1, 0).getDate();

  const podeVoltar = ano > primeiro.getFullYear() || (ano === primeiro.getFullYear() && mes > primeiro.getMonth());
  const podeAvancar = ano < ultimo.getFullYear() || (ano === ultimo.getFullYear() && mes < ultimo.getMonth());

  const celulas: (number | null)[] = [
    ...Array.from({ length: inicioSemana }, () => null),
    ...Array.from({ length: diasNoMes }, (_, i) => i + 1),
  ];

  return (
    <div className="rounded-3xl border border-pink-100 bg-white p-3 shadow-sm sm:p-4">
      <div className="mb-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setCursor(new Date(ano, mes - 1, 1))}
          disabled={!podeVoltar}
          aria-label="Mês anterior"
          className="rounded-full p-2 text-gray-700 hover:bg-gray-100 disabled:opacity-30"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
        <p className="text-sm font-semibold text-gray-900">
          {MESES[mes]} {ano}
        </p>
        <button
          type="button"
          onClick={() => setCursor(new Date(ano, mes + 1, 1))}
          disabled={!podeAvancar}
          aria-label="Próximo mês"
          className="rounded-full p-2 text-gray-700 hover:bg-gray-100 disabled:opacity-30"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-medium text-gray-400">
        {SEMANA.map((d, i) => (
          <span key={i} className="py-1">{d}</span>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {celulas.map((dia, i) => {
          if (dia === null) return <span key={`v-${i}`} />;
          const chave = `${ano}-${pad(mes + 1)}-${pad(dia)}`;
          const livre = disponiveis.has(chave);
          const ativo = chave === selecionado;
          return (
            <button
              key={chave}
              type="button"
              disabled={!livre}
              onClick={() => onSelect(chave)}
              aria-pressed={ativo}
              aria-label={`${dia} de ${MESES[mes]}${livre ? "" : " (indisponível)"}`}
              className={`aspect-square rounded-full text-sm font-medium transition ${
                ativo ? "text-white shadow" : livre ? "text-gray-900 hover:bg-pink-50" : "cursor-not-allowed text-gray-300"
              }`}
              style={
                ativo
                  ? { backgroundColor: "var(--ao-primary)" }
                  : livre
                    ? { boxShadow: "inset 0 0 0 1px color-mix(in srgb, var(--ao-primary) 35%, white)" }
                    : undefined
              }
            >
              {dia}
            </button>
          );
        })}
      </div>
    </div>
  );
}
