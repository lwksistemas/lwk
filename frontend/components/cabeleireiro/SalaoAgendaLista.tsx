'use client';

import { ChevronRight } from 'lucide-react';
import {
  SALAO_PRIMARY,
} from '@/components/cabeleireiro/salao-nav';
import {
  SALAO_STATUS_LABEL,
  type SalaoCalendarEvent,
} from '@/components/cabeleireiro/salao-agenda-mappers';

function parseLocal(iso: string): Date | null {
  if (!iso) return null;
  const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2}))?)?/);
  if (!m) {
    const d = new Date(iso);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  return new Date(
    Number(m[1]),
    Number(m[2]) - 1,
    Number(m[3]),
    Number(m[4] || 0),
    Number(m[5] || 0),
    Number(m[6] || 0),
  );
}

function formatHora(d: Date) {
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function formatDia(d: Date) {
  return d.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
  });
}

function labelStatus(evt: SalaoCalendarEvent): string {
  if (evt.extendedProps.isBloqueio) return 'Bloqueio';
  return SALAO_STATUS_LABEL[evt.extendedProps.status || ''] || 'Agendamento';
}

function tituloLista(evt: SalaoCalendarEvent): string {
  if (evt.extendedProps.isBloqueio) {
    return evt.title.replace(/^🚫\s*/, '');
  }
  const parts = [evt.extendedProps.patient_name, evt.extendedProps.procedure_name].filter(Boolean);
  return parts.length ? parts.join(' · ') : evt.title;
}

export function SalaoAgendaLista({
  eventos,
  onAbrir,
}: {
  eventos: SalaoCalendarEvent[];
  onAbrir: (evt: SalaoCalendarEvent) => void;
}) {
  const ordenados = eventos
    .map((evt) => {
      const start = parseLocal(evt.start);
      if (!start) return null;
      const end = parseLocal(evt.end) || start;
      return { evt, start, end };
    })
    .filter((x): x is { evt: SalaoCalendarEvent; start: Date; end: Date } => x != null)
    .sort((a, b) => a.start.getTime() - b.start.getTime());

  const grupos: { chave: string; label: string; items: typeof ordenados }[] = [];
  const mapa = new Map<string, typeof ordenados>();
  for (const item of ordenados) {
    const chave = `${item.start.getFullYear()}-${String(item.start.getMonth() + 1).padStart(2, '0')}-${String(item.start.getDate()).padStart(2, '0')}`;
    if (!mapa.has(chave)) mapa.set(chave, []);
    mapa.get(chave)!.push(item);
  }
  for (const [chave, items] of [...mapa.entries()].sort(([a], [b]) => a.localeCompare(b))) {
    grupos.push({ chave, label: formatDia(items[0].start), items });
  }

  if (ordenados.length === 0) {
    return (
      <p className="text-center text-sm text-gray-500 py-12">
        Nenhum agendamento ou bloqueio neste período.
      </p>
    );
  }

  const thClass =
    'text-left px-3 sm:px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500 whitespace-nowrap';
  const tdClass = 'px-3 sm:px-4 py-3 align-middle text-sm';

  return (
    <div className="space-y-6 pb-4">
      {grupos.map((grupo) => (
        <section key={grupo.chave}>
          <h3 className="sticky top-0 z-10 bg-white py-2 mb-1 text-sm font-semibold text-gray-800 capitalize border-b border-[#E8D5DC]">
            {grupo.label}
          </h3>
          <div className="overflow-x-auto rounded-lg border border-[#E8D5DC]">
            <table className="w-full min-w-[640px] text-sm border-collapse">
              <thead className="bg-[#FBF5F7] border-b border-[#E8D5DC]">
                <tr>
                  <th className={thClass}>Horário</th>
                  <th className={thClass}>Cliente / Descrição</th>
                  <th className={`${thClass} hidden sm:table-cell`}>Profissional</th>
                  <th className={`${thClass} hidden md:table-cell`}>Duração</th>
                  <th className={thClass}>Status</th>
                  <th className="w-10" aria-hidden />
                </tr>
              </thead>
              <tbody>
                {grupo.items.map(({ evt, start, end }) => {
                  const duracaoMin = Math.max(1, Math.round((end.getTime() - start.getTime()) / 60000));
                  const cor = evt.backgroundColor || SALAO_PRIMARY;
                  return (
                    <tr
                      key={String(evt.id)}
                      onClick={() => onAbrir(evt)}
                      className="border-t border-[#F3E4EA] hover:bg-[#FBF5F7] cursor-pointer transition-colors"
                    >
                      <td className={`${tdClass} tabular-nums whitespace-nowrap`}>
                        <span className="inline-flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: cor }} aria-hidden />
                          <span>
                            <span className="font-medium text-gray-900">{formatHora(start)}</span>
                            <span className="text-gray-400 mx-1">–</span>
                            <span className="text-gray-600">{formatHora(end)}</span>
                          </span>
                        </span>
                      </td>
                      <td className={tdClass}>
                        <p className="font-medium text-gray-900 truncate max-w-[220px] sm:max-w-none">
                          {tituloLista(evt)}
                        </p>
                        {evt.extendedProps.professional_name && (
                          <p className="sm:hidden text-xs text-gray-500 mt-0.5 truncate">
                            {evt.extendedProps.professional_name}
                          </p>
                        )}
                      </td>
                      <td className={`${tdClass} hidden sm:table-cell text-gray-600`}>
                        {evt.extendedProps.professional_name || '—'}
                      </td>
                      <td className={`${tdClass} hidden md:table-cell text-gray-600 tabular-nums`}>
                        {duracaoMin} min
                      </td>
                      <td className={tdClass}>
                        <span
                          className="inline-block text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap"
                          style={{ backgroundColor: `${cor}22`, color: cor }}
                        >
                          {labelStatus(evt)}
                        </span>
                      </td>
                      <td className="px-2 py-3 text-gray-400">
                        <ChevronRight size={18} className="mx-auto" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ))}
    </div>
  );
}
