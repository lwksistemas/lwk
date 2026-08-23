'use client';

import { BuscaAdicionar, ListaItens, NuvemTags, SecaoTeal } from '@/components/clinica-geral/AtendimentoWidgets';
import { DURACOES, QUEIXAS, toggleItem } from '@/lib/clinica-geral-atendimento';
import type { FichaAtendimento } from '@/lib/clinica-geral-types';

type Props = {
  ficha: FichaAtendimento;
  onChange: (patch: Partial<FichaAtendimento>) => void;
};

export function AtendimentoHma({ ficha, onChange }: Props) {
  return (
    <SecaoTeal titulo="História e motivo do atendimento">
      <div>
        <p className="mb-2 text-sm font-medium text-slate-700">Queixa principal e duração</p>
        <NuvemTags
          opcoes={QUEIXAS}
          selecionados={ficha.queixas.map((q) => q.nome)}
          onToggle={(nome) => onChange({ queixas: toggleItem(ficha.queixas, nome) })}
        />
      </div>
      <BuscaAdicionar
        placeholder="Qual queixa você procura?"
        onAdd={(nome) => {
          if (ficha.queixas.some((q) => q.nome.toLowerCase() === nome.toLowerCase())) return;
          onChange({ queixas: toggleItem(ficha.queixas, nome) });
        }}
      />
      <ListaItens
        itens={ficha.queixas}
        statusOpcoes={DURACOES}
        campo="duracao"
        onChange={(i, patch) =>
          onChange({ queixas: ficha.queixas.map((q, idx) => (idx === i ? { ...q, ...patch } : q)) })
        }
        onRemove={(i) => onChange({ queixas: ficha.queixas.filter((_, idx) => idx !== i) })}
      />
      <label className="block text-sm">
        <span className="mb-1 block font-medium text-slate-700">História da doença atual</span>
        <textarea
          value={ficha.historia_doenca}
          onChange={(e) => onChange({ historia_doenca: e.target.value })}
          rows={6}
          className="w-full rounded-md border border-slate-200 px-3 py-2 outline-none focus:border-teal-500"
        />
      </label>
    </SecaoTeal>
  );
}
