'use client';

import { useEffect, useState } from 'react';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import {
  createEspecialidade,
  createProfissional,
  deleteEspecialidade,
  deleteProfissional,
  listEspecialidades,
  updateEspecialidade,
  updateProfissional,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { EspecialidadeEquipe, ProfissionalEquipe } from '@/lib/clinica-geral-types';
import { formatTelefone } from '@/lib/format-br';

const CONSELHOS = ['CRM', 'CRO', 'CRF', 'CREFITO', 'COREN', 'CRP', 'CRN', 'CRFa', 'CRESS'];
const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
  'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

const inputClass = 'mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal';
const labelClass = 'block text-[13px] font-bold text-slate-700 dark:text-slate-200';

type FormEsp = { id?: number; nome: string };
type FormProf = {
  id?: number;
  especialidade: number;
  nome: string;
  conselho: string;
  registro: string;
  uf: string;
  email: string;
  telefone: string;
  cbo: string;
};

const PROF_VAZIO = (especialidade: number): FormProf => ({
  especialidade,
  nome: '',
  conselho: '',
  registro: '',
  uf: '',
  email: '',
  telefone: '',
  cbo: '',
});

export function EspecialidadesPage() {
  const [lista, setLista] = useState<EspecialidadeEquipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [formEsp, setFormEsp] = useState<FormEsp | null>(null);
  const [formProf, setFormProf] = useState<FormProf | null>(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = async () => {
    const dados = await listEspecialidades();
    setLista(dados);
  };

  useEffect(() => {
    void carregar()
      .catch(() => setErro('Não foi possível carregar as especialidades.'))
      .finally(() => setLoading(false));
  }, []);

  const salvarEsp = async () => {
    if (!formEsp?.nome.trim()) return;
    setSalvando(true);
    setErro('');
    try {
      if (formEsp.id) await updateEspecialidade(formEsp.id, formEsp.nome.trim());
      else await createEspecialidade(formEsp.nome.trim());
      setFormEsp(null);
      await carregar();
    } catch {
      setErro('Não foi possível salvar a especialidade.');
    } finally {
      setSalvando(false);
    }
  };

  const excluirEsp = async (item: EspecialidadeEquipe) => {
    if (!confirm(`Excluir a especialidade "${item.nome}" e ocultar os profissionais dela?`)) return;
    try {
      await deleteEspecialidade(item.id);
      await carregar();
    } catch {
      setErro('Não foi possível excluir a especialidade.');
    }
  };

  const salvarProf = async () => {
    if (!formProf?.nome.trim()) return;
    setSalvando(true);
    setErro('');
    try {
      const payload = { ...formProf, nome: formProf.nome.trim() };
      if (formProf.id) await updateProfissional(formProf.id, payload);
      else await createProfissional(payload);
      setFormProf(null);
      await carregar();
    } catch {
      setErro('Não foi possível salvar o profissional.');
    } finally {
      setSalvando(false);
    }
  };

  const excluirProf = async (item: ProfissionalEquipe) => {
    if (!confirm(`Excluir o profissional "${item.nome}"?`)) return;
    try {
      await deleteProfissional(item.id);
      await carregar();
    } catch {
      setErro('Não foi possível excluir o profissional.');
    }
  };

  if (loading) return <p className="py-12 text-sm text-slate-500">Carregando especialidades...</p>;

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3">
        <h2 className="text-lg font-medium text-slate-800 dark:text-slate-100">Especialidades</h2>
        <button
          type="button"
          className="rounded px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
          onClick={() => {
            setFormProf(null);
            setFormEsp({ nome: '' });
          }}
        >
          Nova especialidade
        </button>
      </div>
      <p className="mb-6 text-sm text-slate-500">
        Cadastre as especialidades do consultório e os profissionais de cada uma.
      </p>
      {erro ? <p className="mb-4 text-sm text-red-600">{erro}</p> : null}

      {formEsp ? (
        <div className="mb-6 max-w-md rounded-md border border-slate-200 p-4 dark:border-white/10">
          <p className="mb-3 text-sm font-medium">{formEsp.id ? 'Editar especialidade' : 'Nova especialidade'}</p>
          <label className={labelClass}>
            Nome
            <input
              className={inputClass}
              value={formEsp.nome}
              onChange={(e) => setFormEsp({ ...formEsp, nome: e.target.value })}
            />
          </label>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" className="rounded px-3 py-1.5 text-sm text-slate-600" onClick={() => setFormEsp(null)}>
              Cancelar
            </button>
            <button
              type="button"
              disabled={salvando}
              className="rounded px-4 py-1.5 text-sm font-medium text-white disabled:opacity-60"
              style={{ backgroundColor: TEAL }}
              onClick={() => void salvarEsp()}
            >
              Salvar
            </button>
          </div>
        </div>
      ) : null}

      {formProf ? (
        <div className="mb-6 max-w-2xl rounded-md border border-slate-200 p-4 dark:border-white/10">
          <p className="mb-3 text-sm font-medium">{formProf.id ? 'Editar profissional' : 'Novo profissional'}</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className={`${labelClass} sm:col-span-2`}>
              Nome
              <input className={inputClass} value={formProf.nome} onChange={(e) => setFormProf({ ...formProf, nome: e.target.value })} />
            </label>
            <label className={labelClass}>
              Conselho
              <select className={inputClass} value={formProf.conselho} onChange={(e) => setFormProf({ ...formProf, conselho: e.target.value })}>
                <option value="" />
                {CONSELHOS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
            <label className={labelClass}>
              Registro
              <input className={inputClass} value={formProf.registro} onChange={(e) => setFormProf({ ...formProf, registro: e.target.value })} />
            </label>
            <label className={labelClass}>
              UF
              <select className={inputClass} value={formProf.uf} onChange={(e) => setFormProf({ ...formProf, uf: e.target.value })}>
                <option value="" />
                {UFS.map((uf) => (
                  <option key={uf} value={uf}>{uf}</option>
                ))}
              </select>
            </label>
            <label className={labelClass}>
              Código CBO
              <input className={inputClass} value={formProf.cbo} onChange={(e) => setFormProf({ ...formProf, cbo: e.target.value })} />
            </label>
            <label className={labelClass}>
              E-mail
              <input className={inputClass} type="email" value={formProf.email} onChange={(e) => setFormProf({ ...formProf, email: e.target.value })} />
            </label>
            <label className={labelClass}>
              Telefone
              <input
                className={inputClass}
                value={formatTelefone(formProf.telefone)}
                onChange={(e) => setFormProf({ ...formProf, telefone: formatTelefone(e.target.value) })}
              />
            </label>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" className="rounded px-3 py-1.5 text-sm text-slate-600" onClick={() => setFormProf(null)}>
              Cancelar
            </button>
            <button
              type="button"
              disabled={salvando}
              className="rounded px-4 py-1.5 text-sm font-medium text-white disabled:opacity-60"
              style={{ backgroundColor: TEAL }}
              onClick={() => void salvarProf()}
            >
              Salvar
            </button>
          </div>
        </div>
      ) : null}

      <div className="space-y-6">
        {lista.map((esp) => (
          <section key={esp.id} className="border-b border-slate-100 pb-5 dark:border-white/10">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{esp.nome}</h3>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  className="rounded p-1.5 text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5"
                  title="Renomear"
                  onClick={() => {
                    setFormProf(null);
                    setFormEsp({ id: esp.id, nome: esp.nome });
                  }}
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  className="rounded p-1.5 text-slate-500 hover:bg-red-50 hover:text-red-600"
                  title="Excluir especialidade"
                  onClick={() => void excluirEsp(esp)}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  className="ml-1 inline-flex items-center gap-1 rounded px-2.5 py-1 text-xs font-medium text-white"
                  style={{ backgroundColor: TEAL }}
                  onClick={() => {
                    setFormEsp(null);
                    setFormProf(PROF_VAZIO(esp.id));
                  }}
                >
                  <Plus className="h-3.5 w-3.5" />
                  Profissional
                </button>
              </div>
            </div>
            {esp.profissionais.length === 0 ? (
              <p className="text-sm text-slate-400">Nenhum profissional nesta especialidade.</p>
            ) : (
              <ul className="divide-y divide-slate-100 dark:divide-white/10">
                {esp.profissionais.map((p) => (
                  <li key={p.id} className="flex items-center justify-between gap-3 py-2">
                    <div className="min-w-0">
                      <p className="truncate text-sm text-slate-800 dark:text-slate-100">{p.nome}</p>
                      <p className="truncate text-xs text-slate-500">
                        {[p.conselho, p.registro, p.uf].filter(Boolean).join(' ') || 'Conselho não informado'}
                        {p.telefone ? ` · ${p.telefone}` : ''}
                      </p>
                    </div>
                    <div className="flex shrink-0">
                      <button
                        type="button"
                        className="rounded p-1.5 text-slate-500 hover:bg-slate-50"
                        onClick={() => {
                          setFormEsp(null);
                          setFormProf({
                            id: p.id,
                            especialidade: p.especialidade,
                            nome: p.nome,
                            conselho: p.conselho,
                            registro: p.registro,
                            uf: p.uf,
                            email: p.email,
                            telefone: p.telefone,
                            cbo: p.cbo,
                          });
                        }}
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        className="rounded p-1.5 text-slate-500 hover:bg-red-50 hover:text-red-600"
                        onClick={() => void excluirProf(p)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
