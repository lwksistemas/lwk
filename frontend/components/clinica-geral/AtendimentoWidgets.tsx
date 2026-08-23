'use client';

import { useState, type ReactNode } from 'react';
import { Settings, X } from 'lucide-react';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { ItemFicha } from '@/lib/clinica-geral-types';

export function SecaoTeal({
  titulo,
  onVerAnteriores,
  onConfigurar,
  children,
}: {
  titulo: string;
  onVerAnteriores?: () => void;
  onConfigurar?: () => void;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
      <div className="flex items-center justify-between gap-3 px-4 py-2 text-white" style={{ backgroundColor: TEAL }}>
        <h2 className="text-sm font-semibold">{titulo}</h2>
        <div className="flex items-center gap-3">
          {onVerAnteriores ? (
            <button type="button" onClick={onVerAnteriores} className="text-xs font-medium underline-offset-2 hover:underline">
              Ver anteriores
            </button>
          ) : null}
          {onConfigurar ? (
            <button type="button" onClick={onConfigurar} title="Configurações e fotos" aria-label="Configurações da seção">
              <Settings className="h-4 w-4 opacity-90" />
            </button>
          ) : null}
        </div>
      </div>
      <div className="space-y-4 p-4">{children}</div>
    </section>
  );
}

export function NuvemTags({
  opcoes,
  selecionados,
  onToggle,
}: {
  opcoes: string[];
  selecionados: string[];
  onToggle: (nome: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {opcoes.map((nome) => {
        const ativo = selecionados.includes(nome);
        return (
          <button
            key={nome}
            type="button"
            onClick={() => onToggle(nome)}
            className="rounded-full px-3 py-1 text-xs font-medium"
            style={
              ativo
                ? { backgroundColor: '#C5E1E0', color: '#0D6B6B' }
                : { backgroundColor: NAVY_SOFT, color: '#fff' }
            }
          >
            {nome}
          </button>
        );
      })}
    </div>
  );
}

const NAVY_SOFT = '#3B3A6A';

export function BuscaAdicionar({
  placeholder,
  onAdd,
}: {
  placeholder: string;
  onAdd: (nome: string) => void;
}) {
  const [texto, setTexto] = useState('');
  return (
    <div className="flex gap-2">
      <input
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        placeholder={placeholder}
        className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm outline-none focus:border-teal-500"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && texto.trim()) {
            onAdd(texto.trim());
            setTexto('');
          }
        }}
      />
      <button
        type="button"
        onClick={() => {
          if (!texto.trim()) return;
          onAdd(texto.trim());
          setTexto('');
        }}
        className="rounded-md px-3 py-2 text-sm font-medium text-white"
        style={{ backgroundColor: TEAL }}
      >
        Adicionar
      </button>
    </div>
  );
}

export function ListaItens({
  itens,
  statusOpcoes,
  campo,
  onChange,
  onRemove,
}: {
  itens: ItemFicha[];
  statusOpcoes: string[];
  campo: 'status' | 'duracao';
  onChange: (index: number, patch: Partial<ItemFicha>) => void;
  onRemove: (index: number) => void;
}) {
  if (!itens.length) return null;
  return (
    <div className="border-l-4 border-emerald-500 pl-3">
      {itens.map((item, i) => (
        <div key={`${item.nome}-${i}`} className="mb-3 rounded-md bg-slate-50 p-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex-1 text-sm font-medium text-slate-800">{item.nome}</span>
            <select
              value={item[campo] || statusOpcoes[0]}
              onChange={(e) => onChange(i, { [campo]: e.target.value })}
              className="rounded-md border border-slate-200 bg-white px-2 py-1 text-sm"
            >
              {statusOpcoes.map((op) => (
                <option key={op}>{op}</option>
              ))}
            </select>
            <button type="button" onClick={() => onRemove(i)} className="text-slate-400 hover:text-red-500" aria-label="Remover">
              <X className="h-4 w-4" />
            </button>
          </div>
          <textarea
            value={item.nota || ''}
            onChange={(e) => onChange(i, { nota: e.target.value })}
            rows={2}
            className="mt-2 w-full rounded-md border border-slate-200 px-2 py-1 text-sm outline-none"
          />
        </div>
      ))}
    </div>
  );
}
