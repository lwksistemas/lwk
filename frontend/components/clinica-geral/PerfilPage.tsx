'use client';

import { useEffect, useState } from 'react';
import { UserRound } from 'lucide-react';
import { ImageUploadMedia } from '@/components/ImageUploadMedia';
import { getUsuarioConsultorio, saveUsuarioConsultorio } from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { UsuarioConsultorio } from '@/lib/clinica-geral-types';
import { formatCpf, formatTelefone } from '@/lib/format-br';

const VAZIO: UsuarioConsultorio = {
  username: '',
  nome: '',
  email: '',
  tratamento: '',
  celular: '',
  telefone: '',
  conselho: '',
  uf: '',
  rg: '',
  cpf: '',
  data_nascimento: '',
  nacionalidade: '',
  sexo: '',
  sexo_label: 'Não informado',
  cbo: '',
  estado_civil: '',
  estado_civil_label: 'Não informado',
  foto_url: '',
};

const UFS = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG',
  'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
];

const CONSELHOS = ['CRM', 'CRO', 'CRF', 'CREFITO', 'COREN', 'CRP', 'CRN', 'CRFa', 'CRESS'];

function dataBr(iso?: string) {
  if (!iso || iso.length < 10) return '';
  const [y, m, d] = iso.slice(0, 10).split('-');
  return `${d}/${m}/${y}`;
}

function Campo({ label, valor }: { label: string; valor?: string }) {
  return (
    <div className="min-h-[2.75rem]">
      <p className="text-[13px] font-bold text-slate-700 dark:text-slate-200">{label}</p>
      <p className="mt-0.5 min-h-[1.25rem] text-sm text-slate-800 dark:text-slate-100">{valor || ''}</p>
    </div>
  );
}

export function PerfilPage() {
  const [usuario, setUsuario] = useState<UsuarioConsultorio>(VAZIO);
  const [draft, setDraft] = useState<UsuarioConsultorio>(VAZIO);
  const [loading, setLoading] = useState(true);
  const [editando, setEditando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    void getUsuarioConsultorio()
      .then((dados) => {
        const next = { ...VAZIO, ...dados };
        setUsuario(next);
        setDraft(next);
      })
      .catch(() => {
        setUsuario(VAZIO);
        setDraft(VAZIO);
      })
      .finally(() => setLoading(false));
  }, []);

  const setCampo = (campo: keyof UsuarioConsultorio, valor: string) => {
    setDraft((atual) => ({ ...atual, [campo]: valor }));
  };

  const salvar = async () => {
    setSalvando(true);
    setErro('');
    try {
      const salvo = await saveUsuarioConsultorio({
        nome: draft.nome,
        email: draft.email,
        tratamento: draft.tratamento,
        celular: draft.celular,
        telefone: draft.telefone,
        conselho: draft.conselho,
        uf: draft.uf,
        rg: draft.rg,
        cpf: draft.cpf,
        data_nascimento: draft.data_nascimento,
        nacionalidade: draft.nacionalidade,
        sexo: draft.sexo,
        cbo: draft.cbo,
        estado_civil: draft.estado_civil,
        foto_url: draft.foto_url,
      });
      const next = { ...VAZIO, ...salvo };
      setUsuario(next);
      setDraft(next);
      setEditando(false);
    } catch {
      setErro('Não foi possível salvar o perfil.');
    } finally {
      setSalvando(false);
    }
  };

  if (loading) {
    return <p className="py-12 text-sm text-slate-500">Carregando perfil...</p>;
  }

  const dados = editando ? draft : usuario;

  return (
    <div>
      <div className="flex flex-col gap-8 lg:flex-row">
        <div className="shrink-0">
          <div className="relative">
            {dados.foto_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={dados.foto_url}
                alt=""
                className="h-36 w-36 rounded-full object-cover bg-slate-200"
              />
            ) : (
              <span className="flex h-36 w-36 items-center justify-center rounded-full bg-slate-200 text-slate-400 dark:bg-white/10">
                <UserRound className="h-16 w-16" strokeWidth={1.25} />
              </span>
            )}
            {editando ? (
              <div className="mt-3">
                <ImageUploadMedia
                  compact
                  folder="avatars"
                  buttonLabel="Alterar foto"
                  value={draft.foto_url}
                  onChange={(url) => setCampo('foto_url', url)}
                />
              </div>
            ) : null}
          </div>
        </div>

        <div className="grid min-w-0 flex-1 grid-cols-1 gap-x-16 gap-y-3 sm:grid-cols-2">
          {editando ? (
            <>
              <label className="block text-[13px] font-bold text-slate-700">
                Tratamento
                <select
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.tratamento || ''}
                  onChange={(e) => setCampo('tratamento', e.target.value)}
                >
                  <option value="" />
                  <option value="Dr.">Dr.</option>
                  <option value="Dra.">Dra.</option>
                  <option value="Sr.">Sr.</option>
                  <option value="Sra.">Sra.</option>
                </select>
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Nome
                <input
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.nome || ''}
                  onChange={(e) => setCampo('nome', e.target.value)}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                E-mail
                <input
                  type="email"
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.email || ''}
                  onChange={(e) => setCampo('email', e.target.value)}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Sexo
                <select
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.sexo || ''}
                  onChange={(e) => setCampo('sexo', e.target.value)}
                >
                  <option value="">Não informado</option>
                  <option value="M">Masculino</option>
                  <option value="F">Feminino</option>
                  <option value="I">Indefinido</option>
                </select>
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Celular
                <input
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={formatTelefone(draft.celular)}
                  onChange={(e) => setCampo('celular', formatTelefone(e.target.value))}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Telefone
                <input
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={formatTelefone(draft.telefone)}
                  onChange={(e) => setCampo('telefone', formatTelefone(e.target.value))}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Conselho
                <select
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.conselho || ''}
                  onChange={(e) => setCampo('conselho', e.target.value)}
                >
                  <option value="" />
                  {CONSELHOS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                UF
                <select
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.uf || ''}
                  onChange={(e) => setCampo('uf', e.target.value)}
                >
                  <option value="" />
                  {UFS.map((uf) => (
                    <option key={uf} value={uf}>{uf}</option>
                  ))}
                </select>
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                RG
                <input
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.rg || ''}
                  onChange={(e) => setCampo('rg', e.target.value)}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                CPF
                <input
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={formatCpf(draft.cpf)}
                  onChange={(e) => setCampo('cpf', formatCpf(e.target.value))}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Data de nascimento
                <input
                  type="date"
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={(draft.data_nascimento || '').slice(0, 10)}
                  onChange={(e) => setCampo('data_nascimento', e.target.value)}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Código CBO
                <input
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.cbo || ''}
                  onChange={(e) => setCampo('cbo', e.target.value)}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Nacionalidade
                <input
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.nacionalidade || ''}
                  onChange={(e) => setCampo('nacionalidade', e.target.value)}
                />
              </label>
              <label className="block text-[13px] font-bold text-slate-700">
                Estado civil
                <select
                  className="mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal"
                  value={draft.estado_civil || ''}
                  onChange={(e) => setCampo('estado_civil', e.target.value)}
                >
                  <option value="">Não informado</option>
                  <option value="solteiro">Solteiro(a)</option>
                  <option value="casado">Casado(a)</option>
                  <option value="divorciado">Divorciado(a)</option>
                  <option value="viuvo">Viúvo(a)</option>
                  <option value="uniao">União estável</option>
                </select>
              </label>
            </>
          ) : (
            <>
              <Campo label="Tratamento" valor={dados.tratamento} />
              <Campo label="Nome" valor={dados.nome} />
              <Campo label="E-mail" valor={dados.email} />
              <Campo label="Sexo" valor={dados.sexo_label || 'Não informado'} />
              <Campo label="Celular" valor={formatTelefone(dados.celular) || dados.celular} />
              <Campo label="Telefone" valor={formatTelefone(dados.telefone) || dados.telefone} />
              <Campo label="Conselho" valor={dados.conselho} />
              <Campo label="UF" valor={dados.uf} />
              <Campo label="RG" valor={dados.rg} />
              <Campo label="CPF" valor={formatCpf(dados.cpf) || dados.cpf} />
              <Campo label="Data de nascimento" valor={dataBr(dados.data_nascimento)} />
              <Campo label="Código CBO" valor={dados.cbo} />
              <Campo label="Nacionalidade" valor={dados.nacionalidade} />
              <Campo label="Estado civil" valor={dados.estado_civil_label || 'Não informado'} />
            </>
          )}
        </div>
      </div>

      {erro ? <p className="mt-4 text-sm text-red-600">{erro}</p> : null}

      <div className="mt-10 flex justify-end gap-2">
        {editando ? (
          <>
            <button
              type="button"
              className="rounded px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
              onClick={() => {
                setDraft(usuario);
                setEditando(false);
                setErro('');
              }}
            >
              Cancelar
            </button>
            <button
              type="button"
              disabled={salvando}
              className="rounded px-5 py-2 text-sm font-medium text-white disabled:opacity-60"
              style={{ backgroundColor: TEAL }}
              onClick={() => void salvar()}
            >
              {salvando ? 'Salvando...' : 'Salvar'}
            </button>
          </>
        ) : (
          <button
            type="button"
            className="rounded px-5 py-2 text-sm font-medium text-white"
            style={{ backgroundColor: TEAL }}
            onClick={() => setEditando(true)}
          >
            Editar
          </button>
        )}
      </div>
    </div>
  );
}
