'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ImageUploadMedia } from '@/components/ImageUploadMedia';
import { PacienteFichaView } from '@/components/clinica-geral/PacienteFichaView';
import {
  archivePaciente,
  createAnexoPaciente,
  createPaciente,
  deleteAnexoPaciente,
  getPaciente,
  listAnexosPaciente,
  listConsultasPaciente,
  updatePaciente,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { ConvenioPaciente, Consulta, Paciente, PacienteAnexo, Responsavel } from '@/lib/clinica-geral-types';
import {
  EMPTY_CONVENIO,
  EMPTY_RESPONSAVEL,
  ESTADO_CIVIL_OPCOES,
  SEXO_LABEL,
  TIPO_SANGUINEO_OPCOES,
  emptyPaciente,
} from '@/lib/clinica-geral-types';

type PacienteFormPageProps = {
  mode: 'novo' | 'editar';
};

export function PacienteFormPage({ mode }: PacienteFormPageProps) {
  const params = useParams();
  const slug = params.slug as string;
  const id = mode === 'editar' ? Number(params.id) : 0;
  const router = useRouter();
  const base = `/loja/${slug}/clinica/pacientes`;

  const [form, setForm] = useState<Paciente>(emptyPaciente());
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [anexos, setAnexos] = useState<PacienteAnexo[]>([]);
  const [loading, setLoading] = useState(mode === 'editar');
  const [saving, setSaving] = useState(false);
  const [erro, setErro] = useState('');
  const [view, setView] = useState(mode === 'editar');

  useEffect(() => {
    if (mode !== 'editar' || !id) return;
    setLoading(true);
    Promise.all([getPaciente(id), listConsultasPaciente(id), listAnexosPaciente(id)])
      .then(([paciente, agenda, docs]) => {
        setForm({
          ...emptyPaciente(),
          ...paciente,
          responsaveis: paciente.responsaveis || [],
          convenios: paciente.convenios || [],
        });
        setConsultas(agenda);
        setAnexos(docs);
      })
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
        const updated = await updatePaciente(id, payload);
        setForm(updated);
        setView(true);
      }
    } catch {
      setErro('Não foi possível salvar o paciente.');
    } finally {
      setSaving(false);
    }
  };

  const arquivar = async () => {
    if (!window.confirm('Arquivar este paciente?')) return;
    await archivePaciente(id);
    router.push(base);
  };

  const excluir = async () => {
    if (!window.confirm('Excluir este paciente? A ficha será arquivada e deixará de aparecer na lista.')) return;
    await archivePaciente(id);
    router.push(base);
  };

  if (loading) {
    return <p className="p-6 text-sm text-slate-500">Carregando ficha...</p>;
  }

  if (view) {
    return (
      <PacienteFichaView
        slug={slug}
        paciente={form}
        consultas={consultas}
        anexos={anexos}
        onVerProntuario={() => router.push(`${base}/${id}/prontuario`)}
        onEditar={() => setView(false)}
        onArquivar={() => void arquivar()}
        onExcluir={() => void excluir()}
        onAddAnexo={async (url, nome) => {
          const created = await createAnexoPaciente(id, nome, url);
          setAnexos((atual) => [created, ...atual]);
        }}
        onRemoveAnexo={async (anexoId) => {
          await deleteAnexoPaciente(anexoId);
          setAnexos((atual) => atual.filter((a) => a.id !== anexoId));
        }}
      />
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      <div className="flex flex-wrap items-start gap-6">
        <ImageUploadMedia
          label="Foto"
          folder="fotos"
          accept="image/*"
          value={form.foto_url}
          onChange={(url) => set({ foto_url: url })}
          patientId={id || null}
          patientNome={form.nome}
          patientCpf={form.cpf}
        />
        <div className="min-w-[240px] flex-1 grid gap-3 sm:grid-cols-2">
          <Input label="Número do prontuário" value={form.numero_prontuario} onChange={(v) => set({ numero_prontuario: v })} />
          <Input label="Médico de referência" value={form.medico_referencia} onChange={(v) => set({ medico_referencia: v })} />
        </div>
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
        <Select
          label="Estado civil"
          value={form.estado_civil}
          onChange={(v) => set({ estado_civil: v })}
          options={ESTADO_CIVIL_OPCOES.map((value) => ({ value, label: value || 'Não informado' }))}
        />
        <Select
          label="Tipo sanguíneo"
          value={form.tipo_sanguineo}
          onChange={(v) => set({ tipo_sanguineo: v })}
          options={TIPO_SANGUINEO_OPCOES.map((value) => ({ value, label: value || 'Não informado' }))}
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Input label="CPF" value={form.cpf} onChange={(v) => set({ cpf: v })} />
        <Input label="Nacionalidade" value={form.nacionalidade} onChange={(v) => set({ nacionalidade: v })} />
        <Input label="Profissão" value={form.profissao} onChange={(v) => set({ profissao: v })} />
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <Input label="RG" value={form.rg} onChange={(v) => set({ rg: v })} />
        <Input label="Passaporte" value={form.passaporte} onChange={(v) => set({ passaporte: v })} />
        <Input label="Nome da mãe" value={form.nome_mae} onChange={(v) => set({ nome_mae: v })} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Celular" value={form.telefone} onChange={(v) => set({ telefone: v })} />
        <Input label="E-mail" value={form.email} onChange={(v) => set({ email: v })} />
      </div>
      <Input label="Alergias" value={form.alergias} onChange={(v) => set({ alergias: v })} />
      <label className="block text-sm">
        <span className="mb-1 block text-slate-600">Observações</span>
        <textarea
          value={form.observacoes}
          onChange={(e) => set({ observacoes: e.target.value })}
          rows={4}
          className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-teal-500"
        />
      </label>

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
