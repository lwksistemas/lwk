'use client';

import { useEffect, useState } from 'react';
import { createTarefa, deleteTarefa, listTarefas, toggleTarefa } from '@/lib/clinica-geral-api';
import type { Tarefa } from '@/lib/clinica-geral-types';

const TEAL = '#0D9B9B';

export function TarefasDoDia({ data }: { data: string }) {
  const [tarefas, setTarefas] = useState<Tarefa[]>([]);
  const [nova, setNova] = useState(false);
  const [texto, setTexto] = useState('');

  useEffect(() => {
    void listTarefas(data).then(setTarefas).catch(() => setTarefas([]));
  }, [data]);

  const add = async () => {
    const t = texto.trim();
    if (!t) return;
    const created = await createTarefa(data, t);
    setTarefas((prev) => [created, ...prev]);
    setTexto('');
    setNova(false);
  };

  return (
    <div className="border-t border-slate-100 px-4 py-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Tarefas do dia</h3>
        <button
          type="button"
          onClick={() => setNova((v) => !v)}
          className="text-lg leading-none"
          style={{ color: TEAL }}
          aria-label="Adicionar tarefa"
        >
          +
        </button>
      </div>
      {nova && (
        <div className="mb-2 flex gap-1">
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && void add()}
            placeholder="Nova tarefa"
            className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
          />
          <button type="button" onClick={() => void add()} className="text-xs font-medium" style={{ color: TEAL }}>
            Ok
          </button>
        </div>
      )}
      {tarefas.length === 0 ? (
        <p className="text-xs text-slate-500">Você não possui nenhuma tarefa agendada</p>
      ) : (
        <ul className="space-y-1">
          {tarefas.map((t) => (
            <li key={t.id} className="flex items-start gap-2 text-xs">
              <input
                type="checkbox"
                checked={t.concluida}
                onChange={async () => {
                  const next = await toggleTarefa(t);
                  setTarefas((prev) => prev.map((x) => (x.id === next.id ? next : x)));
                }}
              />
              <span className={t.concluida ? 'text-slate-400 line-through' : 'text-slate-700'}>{t.texto}</span>
              <button
                type="button"
                className="ml-auto text-slate-400 hover:text-red-500"
                onClick={async () => {
                  await deleteTarefa(t.id);
                  setTarefas((prev) => prev.filter((x) => x.id !== t.id));
                }}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
