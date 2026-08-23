'use client';

import { SecaoTeal } from '@/components/clinica-geral/AtendimentoWidgets';
import { calcIMC, calcSC } from '@/lib/clinica-geral-atendimento';
import type { ExameFisicoFicha, FichaAtendimento } from '@/lib/clinica-geral-types';

const VITAIS: { key: keyof ExameFisicoFicha; label: string; un: string }[] = [
  { key: 'peso', label: 'Peso', un: 'kg' },
  { key: 'altura', label: 'Altura', un: 'cm' },
  { key: 'sc', label: 'SC', un: 'm²' },
  { key: 'temperatura', label: 'Temperatura', un: '°C' },
  { key: 'imc', label: 'IMC', un: 'kg/m²' },
  { key: 'circ_abdominal', label: 'Circ. abdominal', un: 'cm' },
];

const QUALI: { key: keyof ExameFisicoFicha; label: string }[] = [
  { key: 'aspecto_geral', label: 'Aspecto Geral' },
  { key: 'mucosas', label: 'Mucosas' },
  { key: 'olhos_face', label: 'Olhos/Face' },
  { key: 'pescoco', label: 'Pescoço/Tireoide' },
  { key: 'cardiorespiratorio', label: 'Sist. cardiorespiratório' },
  { key: 'pele', label: 'Pele/Dermatológico' },
  { key: 'abdome_superior', label: 'Abdome superior' },
  { key: 'abdome_inferior', label: 'Abdome inferior' },
  { key: 'osteomuscular', label: 'Osteomuscular' },
  { key: 'membros', label: 'Membros' },
  { key: 'neurologico', label: 'Neurológico' },
  { key: 'outras', label: 'Outras observações' },
];

type Props = {
  ficha: FichaAtendimento;
  onChange: (patch: Partial<FichaAtendimento>) => void;
};

export function AtendimentoExameFisico({ ficha, onChange }: Props) {
  const set = (patch: Partial<ExameFisicoFicha>) => {
    const exame = { ...ficha.exame, ...patch };
    if (patch.peso !== undefined || patch.altura !== undefined) {
      exame.imc = calcIMC(exame.peso, exame.altura);
      exame.sc = calcSC(exame.peso, exame.altura);
    }
    onChange({ exame });
  };

  return (
    <SecaoTeal titulo="Exame físico">
      <div className="grid gap-3 sm:grid-cols-3">
        {VITAIS.map((c) => (
          <label key={c.key} className="text-sm">
            <span className="mb-1 block text-slate-600">
              {c.label} <span className="text-slate-400">{c.un}</span>
            </span>
            <input
              value={ficha.exame[c.key]}
              onChange={(e) => set({ [c.key]: e.target.value })}
              className="w-full rounded-md border border-slate-200 px-3 py-2 outline-none focus:border-teal-500"
            />
          </label>
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <fieldset className="rounded-md border border-slate-200 p-3">
          <legend className="px-1 text-sm text-slate-600">Pressão sentado</legend>
          <div className="grid grid-cols-2 gap-2">
            <Campo label="PAS" value={ficha.exame.pas_sentado} onChange={(v) => set({ pas_sentado: v })} />
            <Campo label="PAD" value={ficha.exame.pad_sentado} onChange={(v) => set({ pad_sentado: v })} />
          </div>
        </fieldset>
        <fieldset className="rounded-md border border-slate-200 p-3">
          <legend className="px-1 text-sm text-slate-600">Pressão deitado</legend>
          <div className="grid grid-cols-2 gap-2">
            <Campo label="PAS" value={ficha.exame.pas_deitado} onChange={(v) => set({ pas_deitado: v })} />
            <Campo label="PAD" value={ficha.exame.pad_deitado} onChange={(v) => set({ pad_deitado: v })} />
          </div>
        </fieldset>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {QUALI.map((c) => (
          <label key={c.key} className="text-sm">
            <span className="mb-1 block text-slate-600">{c.label}</span>
            <textarea
              value={ficha.exame[c.key]}
              onChange={(e) => set({ [c.key]: e.target.value })}
              placeholder={c.label}
              rows={2}
              className="w-full rounded-md border border-slate-200 px-3 py-2 outline-none focus:border-teal-500"
            />
          </label>
        ))}
      </div>
    </SecaoTeal>
  );
}

function Campo({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="text-sm">
      <span className="mb-1 block text-slate-500">{label} mmHg</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} className="w-full rounded-md border border-slate-200 px-3 py-2" />
    </label>
  );
}
