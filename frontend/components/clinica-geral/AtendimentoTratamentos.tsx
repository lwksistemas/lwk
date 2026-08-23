'use client';

import { BuscaAdicionar, NuvemTags, SecaoTeal } from '@/components/clinica-geral/AtendimentoWidgets';
import { MEDICAMENTOS, toggleItem } from '@/lib/clinica-geral-atendimento';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { FichaAtendimento } from '@/lib/clinica-geral-types';

type Props = {
  ficha: FichaAtendimento;
  onChange: (patch: Partial<FichaAtendimento>) => void;
  onVerAnteriores?: () => void;
  onConfigurar?: () => void;
};

export function AtendimentoTratamentos({ ficha, onChange, onVerAnteriores, onConfigurar }: Props) {
  return (
    <SecaoTeal titulo="Tratamentos em andamento" onVerAnteriores={onVerAnteriores} onConfigurar={onConfigurar}>
      <NuvemTags
        opcoes={MEDICAMENTOS}
        selecionados={ficha.tratamentos.map((t) => t.nome)}
        onToggle={(nome) => onChange({ tratamentos: toggleItem(ficha.tratamentos, nome) })}
      />
      <BuscaAdicionar
        placeholder="Procure pelo medicamento ou princípio ativo"
        onAdd={(nome) => {
          if (ficha.tratamentos.some((t) => t.nome.toLowerCase() === nome.toLowerCase())) return;
          onChange({ tratamentos: toggleItem(ficha.tratamentos, nome) });
        }}
      />
      <ul className="space-y-2">
        {ficha.tratamentos.map((t) => (
          <li key={t.nome} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2 text-sm">
            <span>{t.nome}</span>
            <button type="button" className="text-xs" style={{ color: TEAL }} onClick={() => onChange({ tratamentos: toggleItem(ficha.tratamentos, t.nome) })}>
              Remover
            </button>
          </li>
        ))}
      </ul>
    </SecaoTeal>
  );
}
