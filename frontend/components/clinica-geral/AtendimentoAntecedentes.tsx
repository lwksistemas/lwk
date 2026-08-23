'use client';

import { BuscaAdicionar, ListaItens, NuvemTags, SecaoTeal } from '@/components/clinica-geral/AtendimentoWidgets';
import { ANTECEDENTES_CIRURGICOS, ANTECEDENTES_CLINICOS, STATUS_ANTECEDENTE, toggleItem } from '@/lib/clinica-geral-atendimento';
import type { FichaAtendimento, ItemFicha } from '@/lib/clinica-geral-types';

type Props = {
  ficha: FichaAtendimento;
  onChange: (patch: Partial<FichaAtendimento>) => void;
};

function Bloco({
  titulo,
  opcoes,
  itens,
  onLista,
}: {
  titulo: string;
  opcoes: string[];
  itens: ItemFicha[];
  onLista: (itens: ItemFicha[]) => void;
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-slate-700">{titulo}</p>
      <NuvemTags opcoes={opcoes} selecionados={itens.map((i) => i.nome)} onToggle={(nome) => onLista(toggleItem(itens, nome))} />
      <BuscaAdicionar
        placeholder="O que você procura?"
        onAdd={(nome) => {
          if (itens.some((i) => i.nome.toLowerCase() === nome.toLowerCase())) return;
          onLista(toggleItem(itens, nome));
        }}
      />
      <ListaItens
        itens={itens}
        statusOpcoes={STATUS_ANTECEDENTE}
        campo="status"
        onChange={(i, patch) => onLista(itens.map((item, idx) => (idx === i ? { ...item, ...patch } : item)))}
        onRemove={(i) => onLista(itens.filter((_, idx) => idx !== i))}
      />
    </div>
  );
}

export function AtendimentoAntecedentes({ ficha, onChange }: Props) {
  return (
    <SecaoTeal titulo="Antecedentes pessoais">
      <Bloco
        titulo="Antecedentes clínicos"
        opcoes={ANTECEDENTES_CLINICOS}
        itens={ficha.antecedentes_clinicos}
        onLista={(antecedentes_clinicos) => onChange({ antecedentes_clinicos })}
      />
      <Bloco
        titulo="Antecedentes cirúrgicos"
        opcoes={ANTECEDENTES_CIRURGICOS}
        itens={ficha.antecedentes_cirurgicos}
        onLista={(antecedentes_cirurgicos) => onChange({ antecedentes_cirurgicos })}
      />
    </SecaoTeal>
  );
}
