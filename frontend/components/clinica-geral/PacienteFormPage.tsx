'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { createPaciente, getPaciente, updatePaciente, archivePaciente } from '@/lib/clinica-geral-api';
import type { ConvenioPaciente, Paciente, Responsavel } from '@/lib/clinica-geral-types';
import {
  EMPTY_CONVENIO,
  EMPTY_RESPONSAVEL,
  SEXO_LABEL,
  emptyPaciente,
} from '@/lib/clinica-geral-types';
import { ageFromISO, displayName } from '@/lib/clinica-geral-utils';

const TEAL = '#0D9B9B';

type PacienteFormPageProps = {
  mode: 'novo' | 'editar';
};

export function PacienteFormPage({ mode }: PacienteFormPageProps) {
  const params = useParams();
  const slug = params.slug as string;
  const id = mode === 'editar' ? Number(params.id) : 0;
  const router = useRouter();
  const base = `/loja/${slug}/clinica-geral/pacientes`;

  const [form, setForm] = useState<Paciente>(emptyPaciente());
  const [loading, setLoading] = useState(mode === 'editar');
  const [saving, setSaving] = useState(false);
  const [erro, setErro] = useState('');
  const [view, setView] = useState(mode === 'editar');

  useEffect(() => {
    if (mode !== 'editar' || !id) return;
    setLoading(true);
    getPaciente(id)
      .then(setForm)
      .catch(() => setErro('Paciente não encontrado.'))
      .finally(() => setLoading(false));
  }, [mode, id]);

  const set = (patch: Partial<Paciente>) => setForm((f) => ({ ...f, ...patch }));

  const salvar = async () => {
    if (!form.nome.trim()) {
      setErro('Nome é obrigatório.');
      return;
    }
    setSaving(true);
    setErro('');
    try {
      const payload = { ...form };
      delete (payload as { id?: number }).id;
      delete (payload as { created_at?: string }).created_at;
      if (mode === 'novo') {
        const created = await createPaciente(payload);
        router.replace(`${base}/${created.id}`);
      } else {
        await updatePaciente(id, payload);
        setView(true);
      }
    } catch {
      setErro('Não foi possível salvar o paciente.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="p-6 text-sm text-slate-500">Carregando ficha...</p>;
  }

  if (view) {
    const idade = ageFromISO(form.data_nascimento);
    return (
      <div className="grid gap-6 p-6 lg:grid-cols-[220px_1fr_240px]">
        <div className="space-y-4">
          <button
            type="button"
            className="w-full rounded-md py-2 text-sm font-medium text-white"
            style={{ backgroundColor: TEAL }}
            onClick={() => router.push(`/loja/${slug}/clinica-geral/pacientes/${id}/prontuario`)}
          >
            Ver prontuário
          </button>
          <div className="flex h-36 items-center justify-center rounded-full bg-slate-200 text-4xl text-slate-500">
            {(form.nome_social || form.nome).slice(0, 1).toUpperCase()}
          </div>
        </div>
        <div>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm">
            <Field label="Número do prontuário" value={form.numero_prontuario} />
            <Field label="Nome" value={displayName(form.nome, form.nome_social)} />
            <Field label="Nome social" value={form.nome_social} />
            <Field label="CPF" value={form.cpf} />
            <Field label="RG" value={form.rg} />
            <Field
              label="Data de nascimento"
              value={form.data_nascimento ? `${form.data_nascimento}${idade != null ? ` (${idade} anos)` : ''}` : ''}
            />
            <Field label="Sexo" value={SEXO_LABEL[form.sexo]} />
            <Field label="Estado civil" value={form.estado_civil} />
            <Field label="Telefone" value={form.telefone} />
            <Field label="E-mail" value={form.email} />
            <Field label="Alergias" value={form.alergias} />
          </dl>
          {form.alergias ? (
            <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">Alergias: {form.alergias}</p>
          ) : null}
          <div className="mt-8 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={async () => {
                if (!window.confirm('Arquivar este paciente?')) return;
                await archivePaciente(id);
                router.push(base);
              }}
              className="rounded-md border border-red-400 px-3 py-2 text-sm text-red-600"
            >
              Arquivar paciente
            </button>
            <button
              type="button"
              onClick={() => setView(false)}
              className="rounded-md border px-3 py-2 text-sm"
              style={{ borderColor: TEAL, color: TEAL }}
            >
              Editar
            </button>
          </div>
        </div>
        <div>
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Anexos</h3>
          <p className="text-xs text-slate-500">Documentos do prontuário entram na próxima etapa.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Número do prontuário" value={form.numero_prontuario} onChange={(v) => set({ numero_prontuario: v })} />
        <Input label="Médico de referência" value={form.medico_referencia} onChange={(v) => set({ medico_referencia: v })} />
      </div>
      <Input label="Nome" value={form.nome} onChange={(v) => set({ nome: v })} required />
      <Input label="Nome social" value={form.nome_social} onChange={(v) => set({ nome_social: v })} />
      <div className="grid gap-3 sm:grid-cols-4">
        <Input label="Data de nascimento" type="date" value={form.data_nascimento || ''} onChange={(v) => set({ data_nascimento: v || null })} />
        <Select
          label="Sexo"
          value={form.sexo}
          onChange={(v) => set({ sexo: v as Paciente['sexo'] })}
          options={Object.entries(SEXO_LABEL).map(([value, label]) => ({ value, label }))}
        />
        <Input label="Estado civil" value={form.estado_civil} onChange={(v) => set({ estado_civil: v })} />
        <Input label="RG" value={form.rg} onChange={(v) => set({ rg: v })} />
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Input label="CPF" value={form.cpf} onChange={(v) => set({ cpf: v })} />
        <Input label="Passaporte" value={form.passaporte} onChange={(v) => set({ passaporte: v })} />
        <Input label="Tipo sanguíneo" value={form.tipo_sanguineo} onChange={(v) => set({ tipo_sanguineo: v })} />
      </div>
      <Input label="Nome da mãe" value={form.nome_mae} onChange={(v) => set({ nome_mae: v })} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Telefone" value={form.telefone} onChange={(v) => set({ telefone: v })} />
        <Input label="E-mail" value={form.email} onChange={(v) => set({ email: v })} />
      </div>
      <Input label="Alergias" value={form.alergias} onChange={(v) => set({ alergias: v })} />

      <section>
        <h2 className="mb-3 text-base font-semibold text-slate-800">Responsáveis</h2>
        {form.responsaveis.map((r, i) => (
          <div key={i} className="mb-2 grid gap-2 sm:grid-cols-[1fr_1fr_1fr_1fr_auto]">
            <Input label="Nome do responsável" value={r.nome} onChange={(v) => patchList('responsaveis', i, { nome: v })} />
            <Input label="Profissão" value={r.profissao} onChange={(v) => patchList('responsaveis', i, { profissao: v })} />
            <Input label="Grau de parentesco" value={r.parentesco} onChange={(v) => patchList('responsaveis', i, { parentesco: v })} />
            <Input label="Telefone de contato" value={r.telefone} onChange={(v) => patchList('responsaveis', i, { telefone: v })} />
            <button type="button" className="self-end pb-2 text-red-500" onClick={() => removeItem('responsaveis', i)}>
              Remover
            </button>
          </div>
        ))}
        <button type="button" className="rounded-md border px-3 py-1.5 text-sm" style={{ borderColor: TEAL, color: TEAL }} onClick={() => addItem('responsaveis', EMPTY_RESPONSAVEL)}>
          Adicionar Responsável
        </button>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-slate-800">Convênios</h2>
        {form.convenios.map((c, i) => (
          <div key={i} className="mb-2 grid gap-2 sm:grid-cols-[1fr_1fr_1fr_1fr_auto]">
            <Input label="Convênio" value={c.convenio} onChange={(v) => patchList('convenios', i, { convenio: v })} />
            <Input label="Plano" value={c.plano} onChange={(v) => patchList('convenios', i, { plano: v })} />
            <Input label="Carteirinha" value={c.carteirinha} onChange={(v) => patchList('convenios', i, { carteirinha: v })} />
            <Input label="Validade" type="date" value={c.validade || ''} onChange={(v) => patchList('convenios', i, { validade: v || null })} />
            <button type="button" className="self-end pb-2 text-red-500" onClick={() => removeItem('convenios', i)}>
              Remover
            </button>
          </div>
        ))}
        <button type="button" className="rounded-md border px-3 py-1.5 text-sm" style={{ borderColor: TEAL, color: TEAL }} onClick={() => addItem('convenios', EMPTY_CONVENIO)}>
          Adicionar Convênio
        </button>
      </section>

      <section>
        <h2 className="mb-3 text-base font-semibold text-slate-800">Endereço</h2>
        <div className="grid gap-3 sm:grid-cols-4">
          <Input label="CEP" value={form.cep} onChange={(v) => set({ cep: v })} />
          <Input label="Logradouro" value={form.logradouro} onChange={(v) => set({ logradouro: v })} />
          <Input label="Número" value={form.numero} onChange={(v) => set({ numero: v })} />
          <Input label="Complemento" value={form.complemento} onChange={(v) => set({ complemento: v })} />
          <Input label="Bairro" value={form.bairro} onChange={(v) => set({ bairro: v })} />
          <Input label="Cidade" value={form.cidade} onChange={(v) => set({ cidade: v })} />
          <Input label="UF" value={form.uf} onChange={(v) => set({ uf: v })} />
        </div>
      </section>

      {erro && <p className="text-sm text-red-600">{erro}</p>}
      <div className="flex gap-2">
        <button type="button" onClick={() => (mode === 'editar' ? setView(true) : router.push(base))} className="rounded-md border border-slate-300 px-4 py-2 text-sm">
          Cancelar
        </button>
        <button
          type="button"
          disabled={saving}
          onClick={() => void salvar()}
          className="rounded-md px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          style={{ backgroundColor: TEAL }}
        >
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </div>
  );

  function addItem<K extends 'responsaveis' | 'convenios'>(key: K, item: Paciente[K][number]) {
    setForm((f) => ({ ...f, [key]: [...f[key], item] }));
  }

  function removeItem(key: 'responsaveis' | 'convenios', index: number) {
    setForm((f) => ({ ...f, [key]: f[key].filter((_, i) => i !== index) }));
  }

  function patchList(
    key: 'responsaveis' | 'convenios',
    index: number,
    patch: Partial<Responsavel> | Partial<ConvenioPaciente>,
  ) {
    setForm((f) => ({
      ...f,
      [key]: f[key].map((item, i) => (i === index ? { ...item, ...patch } : item)),
    }));
  }
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="text-slate-800">{value || '—'}</dd>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  type = 'text',
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  required?: boolean;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-slate-600">{label}</span>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-teal-500"
      />
    </label>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-slate-600">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-teal-500"
      >
        {options.map((o) => (
          <option key={o.value || 'vazio'} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
