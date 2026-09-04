'use client';

import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { getPaciente, recepcionarConsulta } from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, Paciente } from '@/lib/clinica-geral-types';
import { emptyPaciente } from '@/lib/clinica-geral-types';

type RecepcionarModalProps = {
  consulta: Consulta;
  onClose: () => void;
  onDone: () => Promise<void>;
};

export function RecepcionarModal({ consulta, onClose, onDone }: RecepcionarModalProps) {
  const [form, setForm] = useState<Paciente>(emptyPaciente());
  const [convenio, setConvenio] = useState(consulta.convenio || 'PARTICULAR');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    getPaciente(consulta.paciente)
      .then(setForm)
      .catch(() => setErro('Não foi possível carregar o paciente.'))
      .finally(() => setLoading(false));
  }, [consulta.paciente]);

  const set = (patch: Partial<Paciente>) => setForm((f) => ({ ...f, ...patch }));

  const salvar = async () => {
    if (!form.nome.trim()) {
      setErro('Nome é obrigatório.');
      return;
    }
    setSaving(true);
    setErro('');
    try {
      await recepcionarConsulta(consulta.id, {
        numero_prontuario: form.numero_prontuario,
        nome: form.nome,
        nome_social: form.nome_social,
        cpf: form.cpf,
        rg: form.rg,
        rne: form.rne,
        passaporte: form.passaporte,
        pais_emissor: form.pais_emissor,
        nome_mae: form.nome_mae,
        telefone_fixo: form.telefone_fixo,
        telefone: form.telefone,
        email: form.email,
        quem_indicou: form.quem_indicou,
        alergias: form.alergias,
        convenio,
      });
      await onDone();
    } catch {
      setErro('Não foi possível recepcionar.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/35 p-4">
      <div className="flex max-h-[92vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <h2 className="text-lg font-semibold text-slate-800">Recepcionar Paciente</h2>
          <button type="button" onClick={onClose} aria-label="Fechar">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>
        {loading ? (
          <p className="p-6 text-sm text-slate-500">Carregando ficha...</p>
        ) : (
          <div className="grid flex-1 gap-6 overflow-auto p-5 md:grid-cols-[160px_1fr]">
            <div className="flex flex-col items-center gap-2">
              <div className="flex h-28 w-28 items-center justify-center rounded-full bg-slate-200 text-3xl text-slate-500">
                {(form.nome_social || form.nome).slice(0, 1).toUpperCase()}
              </div>
              <span className="text-xs text-slate-400">Foto na próxima etapa</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Número do prontuário" value={form.numero_prontuario} onChange={(v) => set({ numero_prontuario: v })} />
              <Field label="Nome" value={form.nome} onChange={(v) => set({ nome: v })} className="sm:col-span-2" />
              <Field label="Nome social" value={form.nome_social} onChange={(v) => set({ nome_social: v })} className="sm:col-span-2" />
              <Field label="CPF" value={form.cpf} onChange={(v) => set({ cpf: v })} />
              <Field label="RG" value={form.rg} onChange={(v) => set({ rg: v })} />
              <Field label="RNE" value={form.rne} onChange={(v) => set({ rne: v })} />
              <Field label="Passaporte" value={form.passaporte} onChange={(v) => set({ passaporte: v })} />
              <Field label="País emissor" value={form.pais_emissor} onChange={(v) => set({ pais_emissor: v })} />
              <Field label="Nome da mãe" value={form.nome_mae} onChange={(v) => set({ nome_mae: v })} className="sm:col-span-2" />
              <Field label="Telefone" value={form.telefone_fixo} onChange={(v) => set({ telefone_fixo: v })} />
              <Field label="Celular" value={form.telefone} onChange={(v) => set({ telefone: v })} />
              <label className="block text-sm">
                <span className="mb-1 block text-slate-500">Convênio</span>
                <select value={convenio} onChange={(e) => setConvenio(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2">
                  <option value="PARTICULAR">PARTICULAR</option>
                </select>
              </label>
              <Field label="Quem indicou" value={form.quem_indicou} onChange={(v) => set({ quem_indicou: v })} />
              <Field label="E-mail" value={form.email} onChange={(v) => set({ email: v })} className="sm:col-span-2" />
              <Field label="Alergias" value={form.alergias} onChange={(v) => set({ alergias: v })} className="sm:col-span-2" />
            </div>
          </div>
        )}
        {erro && <p className="px-5 pb-2 text-sm text-red-600">{erro}</p>}
        <div className="flex justify-end gap-2 border-t border-slate-100 px-5 py-3">
          <button type="button" onClick={onClose} className="rounded-md border border-slate-400 px-4 py-2 text-sm">
            Fechar
          </button>
          <button
            type="button"
            disabled={saving || loading}
            onClick={() => void salvar()}
            className="rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            style={{ backgroundColor: TEAL }}
          >
            {saving ? 'Recepcionando...' : 'Recepcionar'}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  className = '',
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  className?: string;
}) {
  return (
    <label className={`block text-sm ${className}`}>
      <span className="mb-1 block text-slate-500">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-teal-500"
      />
    </label>
  );
}
