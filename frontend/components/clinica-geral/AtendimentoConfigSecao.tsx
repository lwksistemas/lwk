'use client';

import { useMemo, useState } from 'react';
import { X } from 'lucide-react';
import { ESCALAS_MEDICAS, gravarEscalasOcultas, isAnexoImagem, lerEscalasOcultas, type AbaAtendimento } from '@/lib/clinica-geral-atendimento';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { PacienteAnexo } from '@/lib/clinica-geral-types';

type Props = {
  aba: AbaAtendimento;
  titulo: string;
  anexos: PacienteAnexo[];
  onEscalasChange?: () => void;
  onClose: () => void;
};

export function AtendimentoConfigSecao({ aba, titulo, anexos, onEscalasChange, onClose }: Props) {
  const fotos = useMemo(() => anexos.filter((a) => isAnexoImagem(a.nome, a.url)), [anexos]);
  const [ocultas, setOcultas] = useState(() => lerEscalasOcultas());
  const [foto, setFoto] = useState<PacienteAnexo | null>(null);

  const toggleEscala = (nome: string) => {
    const proxima = ocultas.includes(nome) ? ocultas.filter((n) => n !== nome) : [...ocultas, nome];
    setOcultas(proxima);
    gravarEscalasOcultas(proxima);
    onEscalasChange?.();
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="max-h-[85vh] w-full max-w-lg overflow-auto rounded-xl bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium" style={{ color: TEAL }}>
              Configurações
            </p>
            <h3 className="text-base font-semibold text-slate-800">{titulo}</h3>
          </div>
          <button type="button" onClick={onClose} aria-label="Fechar" className="text-slate-400 hover:text-slate-600">
            <X className="h-4 w-4" />
          </button>
        </div>

        {aba === 'EM' ? (
          <div className="mb-5">
            <p className="mb-2 text-sm font-medium text-slate-700">Escalas visíveis nesta tela</p>
            <ul className="grid grid-cols-2 gap-2 text-sm">
              {ESCALAS_MEDICAS.map((nome) => (
                <li key={nome}>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" checked={!ocultas.includes(nome)} onChange={() => toggleEscala(nome)} />
                    {nome}
                  </label>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div>
          <p className="mb-2 text-sm font-medium text-slate-700">Analisar fotos</p>
          {fotos.length === 0 ? (
            <p className="text-sm text-slate-400">Nenhuma foto anexada na ficha do paciente.</p>
          ) : (
            <div className="grid grid-cols-3 gap-2">
              {fotos.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setFoto(item)}
                  className="overflow-hidden rounded-md border border-slate-200 bg-slate-50"
                  title={item.nome}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={item.url} alt={item.nome} className="h-24 w-full object-cover" />
                  <span className="block truncate px-1 py-1 text-[10px] text-slate-500">{item.nome}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {foto ? (
        <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/70 p-4" onClick={() => setFoto(null)}>
          <figure className="max-h-[90vh] max-w-3xl" onClick={(e) => e.stopPropagation()}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={foto.url} alt={foto.nome} className="max-h-[80vh] w-auto rounded-md object-contain" />
            <figcaption className="mt-2 text-center text-sm text-white">{foto.nome}</figcaption>
          </figure>
        </div>
      ) : null}
    </div>
  );
}
