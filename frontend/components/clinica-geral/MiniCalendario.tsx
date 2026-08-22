'use client';

import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { TEAL } from '@/lib/clinica-geral-theme';
import { monthGrid, parseISODate, toISODate } from '@/lib/clinica-geral-utils';

const WEEK = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
const MONTHS = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
];

type MiniCalendarioProps = {
  selected: string;
  onSelect: (iso: string) => void;
};

export function MiniCalendario({ selected, onSelect }: MiniCalendarioProps) {
  const selectedDate = parseISODate(selected);
  const [cursor, setCursor] = useState(() => ({
    year: selectedDate.getFullYear(),
    month: selectedDate.getMonth(),
  }));
  useEffect(() => {
    setCursor({ year: selectedDate.getFullYear(), month: selectedDate.getMonth() });
  }, [selected]);
  const today = toISODate(new Date());
  const cells = useMemo(() => monthGrid(cursor.year, cursor.month), [cursor]);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <button
          type="button"
          className="rounded p-1 text-slate-500 hover:bg-slate-100"
          onClick={() =>
            setCursor((c) =>
              c.month === 0 ? { year: c.year - 1, month: 11 } : { year: c.year, month: c.month - 1 },
            )
          }
          aria-label="Mês anterior"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <p className="text-sm font-medium capitalize text-slate-700">
          {MONTHS[cursor.month]} {cursor.year}
        </p>
        <button
          type="button"
          className="rounded p-1 text-slate-500 hover:bg-slate-100"
          onClick={() =>
            setCursor((c) =>
              c.month === 11 ? { year: c.year + 1, month: 0 } : { year: c.year, month: c.month + 1 },
            )
          }
          aria-label="Próximo mês"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-[11px] text-slate-400">
        {WEEK.map((d, i) => (
          <span key={`${d}-${i}`}>{d}</span>
        ))}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1 text-center text-sm">
        {cells.map((day, i) => {
          if (!day) return <span key={`e-${i}`} />;
          const iso = toISODate(new Date(cursor.year, cursor.month, day));
          const isSelected = iso === selected;
          const isToday = iso === today;
          return (
            <button
              key={iso}
              type="button"
              onClick={() => onSelect(iso)}
              className="h-7 rounded-full text-slate-700 hover:bg-slate-100"
              style={
                isSelected || isToday
                  ? { backgroundColor: TEAL, color: '#fff' }
                  : undefined
              }
            >
              {day}
            </button>
          );
        })}
      </div>
    </div>
  );
}
