'use client';

import { useEffect, useState } from 'react';
import { Search, X } from 'lucide-react';
import { createConsulta, createPaciente, listConveniosConsultorio, listPacientes, listTiposConsulta } from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { ConvenioConsultorio, Consulta, PacienteLista, TipoConsultaCatalogo } from '@/lib/clinica-geral-types';
import { MODALIDADE_LABEL, TIPO_CONSULTA_LABEL } from '@/lib/clinica-geral-types';
import { formatShortDate } from '@/lib/clinica-geral-utils';

type AgendamentoRapidoProps = {
  data: string;
  hora: string;
  pacienteInicial?: PacienteLista | null;
  onClose: () => void;
  onSaved: () => Promise<void>;
};

export function AgendamentoRapido({ data, hora, pacienteInicial, onClose, onSaved }: AgendamentoRapidoProps) {
  const [q, setQ] = useState('');
  const [opcoes, setOpcoes] = useState<PacienteLista[]>([]);
  const [paciente, setPaciente] = useState<PacienteLista | null>(pacienteInicial || null);
  const [telefone, setTelefone] = useState(pacienteInicial?.telefone || '');
  const [email, setEmail] = useState(pacienteInicial?.email || '');
  const [convenio, setConvenio] = useState('PARTICULAR');
  const [tipo, setTipo] = useState<Consulta['tipo']>('consulta');
  const [modalidade, setModalidade] = useState<Consulta['modalidade']>('presencial');
  const [tipos, setTipos] = useState<TipoConsultaCatalogo[]>([]);
  const [convenios, setConvenios] = useState<ConvenioConsultorio[]>([]);
  const [saving, setSaving] = useState(false);
  const [erro, setErro] = useState('');

  useEffect(() => {
    void Promise.all([listTiposConsulta(), listConveniosConsultorio()])
      .then(([listaTipos, listaConvenios]) => {
        setTipos(listaTipos);
        setConvenios(listaConvenios);
        if (listaTipos.some((t) => t.codigo === 'consulta')) setTipo('consulta');
        else if (listaTipos[0]) setTipo(listaTipos[0].codigo);
        const particular = listaConvenios.find((c) => c.tipo === 'particular') || listaConvenios[0];
        if (particular) setConvenio(particular.nome);
      })
      .catch(() => {
        setTipos([]);
        setConvenios([]);
      });
  }, []);

  useEffect(() => {
    if (!pacienteInicial) return;
    setPaciente(pacienteInicial);
    setQ(pacienteInicial.nome_social ? `${pacienteInicial.nome_social} (${pacienteInicial.nome})` : pacienteInicial.nome);
    setTelefone(pacienteInicial.telefone);
    setEmail(pacienteInicial.email);
  }, [pacienteInicial]);

  useEffect(() => {
    const t = setTimeout(() => {
      if (!q.trim() || paciente) {
        setOpcoes([]);
        return;
      }
      void listPacientes({ q: q.trim() }).then(setOpcoes).catch(() => setOpcoes([]));
    }, 250);
    return () => clearTimeout(t);
  }, [q, paciente]);

  const escolher = (p: PacienteLista) => {
    setPaciente(p);
    setQ(p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome);
    setTelefone(p.telefone);
    setEmail(p.email);
    setOpcoes([]);
  };

  const limpar = () => {
    setQ('');
    setOpcoes([]);
    setPaciente(null);
    setTelefone('');
    setEmail('');
    setConvenio('PARTICULAR');
    setTipo('consulta');
    setModalidade('presencial');
    setErro('');
  };

  const salvar = async () => {
    const nome = q.trim();
    if (!paciente && !nome) {
      setErro('Informe o nome do paciente.');
      return;
    }
    setSaving(true);
    setErro('');
    try {
      let pacienteId = paciente?.id;
      if (!pacienteId) {
        const created = await createPaciente({ nome, telefone, email });
        pacienteId = created.id;
      }
      await createConsulta({
        paciente: pacienteId,
        data,
        hora: `${hora}:00`,
        tipo,
        modalidade,
        convenio,
        status: 'agendado',
      });
      await onSaved();
    } catch {
      setErro('Não foi possível agendar.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex bg-black/25">
      <div className="flex h-full w-full max-w-md flex-col bg-white shadow-xl">
        <div className="flex items-start justify-between px-5 py-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Agendamento rápido</h2>
            <p className="mt-1 text-sm capitalize text-slate-500">
              {formatShortDate(data)}, às {hora}{' '}
              <button type="button" onClick={limpar} className="ml-2 text-xs text-slate-400 underline">
                limpar campos
              </button>
            </p>
          </div>
          <button type="button" onClick={onClose} aria-label="Fechar">
            <X className="h-5 w-5 text-slate-400" />
          </button>
        </div>
        <div className="flex-1 space-y-3 overflow-auto px-5 py-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPaciente(null);
              }}
              placeholder="Nome ou CPF do paciente"
              className="w-full rounded-md border border-slate-300 py-2 pl-9 pr-3 text-sm outline-none focus:border-teal-500"
            />
            {opcoes.length > 0 && (
              <ul className="absolute z-10 mt-1 w-full rounded-md border border-slate-200 bg-white shadow">
                {opcoes.map((p) => (
                  <li key={p.id}>
                    <button type="button" onClick={() => escolher(p)} className="w-full px-3 py-2 text-left text-sm hover:bg-teal-50">
                      {p.nome_social ? `${p.nome_social} (${p.nome})` : p.nome}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <input value={telefone} onChange={(e) => setTelefone(e.target.value)} placeholder="Celular" className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="E-mail" className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
          <select value={convenio} onChange={(e) => setConvenio(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
            {(convenios.length > 0 ? convenios.map((c) => c.nome) : ['PARTICULAR']).map((nome) => (
              <option key={nome} value={nome}>{nome}</option>
            ))}
          </select>
          <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
            {(tipos.length ? tipos.map((t) => [t.codigo, t.nome] as const) : Object.entries(TIPO_CONSULTA_LABEL)).map(([k, label]) => (
              <option key={k} value={k}>{label}</option>
            ))}
          </select>
          <select value={modalidade} onChange={(e) => setModalidade(e.target.value as Consulta['modalidade'])} className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm">
            {Object.entries(MODALIDADE_LABEL).map(([k, label]) => (
              <option key={k} value={k}>{label}</option>
            ))}
          </select>
          {erro && <p className="text-sm text-red-600">{erro}</p>}
        </div>
        <div className="flex gap-2 border-t border-slate-100 px-5 py-4">
          <button type="button" onClick={onClose} className="flex-1 rounded-md border border-slate-400 py-2 text-sm">
            Cancelar
          </button>
          <button
            type="button"
            disabled={saving}
            onClick={() => void salvar()}
            className="flex-1 rounded-md py-2 text-sm font-medium text-white disabled:opacity-60"
            style={{ backgroundColor: TEAL }}
          >
            {saving ? 'Agendando...' : 'Agendar'}
          </button>
        </div>
      </div>
    </div>
  );
}
