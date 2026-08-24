'use client';

import { useEffect, useState } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import {
  createConvenioConsultorio,
  deleteConvenioConsultorio,
  listConveniosConsultorio,
  updateConvenioConsultorio,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import {
  TIPO_CONVENIO_CONSULTORIO,
  type ConvenioConsultorio,
  type TipoConvenioConsultorio,
} from '@/lib/clinica-geral-types';
import { formatTelefone } from '@/lib/format-br';

const inputClass = 'mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal';
const labelClass = 'block text-[13px] font-bold text-slate-700 dark:text-slate-200';

const VAZIO = {
  nome: '',
  tipo: 'convenio' as TipoConvenioConsultorio,
  registro_ans: '',
  telefone: '',
  observacoes: '',
};

export function ConveniosConsultorioPage() {
  const [lista, setLista] = useState<ConvenioConsultorio[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [form, setForm] = useState<(typeof VAZIO & { id?: number }) | null>(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = async () => {
    setLista(await listConveniosConsultorio());
  };

  useEffect(() => {
    void carregar()
      .catch(() => setErro('Não foi possível carregar os convênios.'))
      .finally(() => setLoading(false));
  }, []);

  const salvar = async () => {
    if (!form?.nome.trim()) return;
    setSalvando(true);
    setErro('');
    try {
      const payload = {
        nome: form.nome.trim(),
        tipo: form.tipo,
        registro_ans: form.registro_ans.trim(),
        telefone: form.telefone.trim(),
        observacoes: form.observacoes.trim(),
      };
      if (form.id) await updateConvenioConsultorio(form.id, payload);
      else await createConvenioConsultorio(payload);
      setForm(null);
      await carregar();
    } catch {
      setErro('Não foi possível salvar o convênio.');
    } finally {
      setSalvando(false);
    }
  };

  const excluir = async (item: ConvenioConsultorio) => {
    if (!confirm(`Excluir "${item.nome}"?`)) return;
    try {
      await deleteConvenioConsultorio(item.id);
      await carregar();
    } catch {
      setErro('Não foi possível excluir o convênio.');
    }
  };

  if (loading) return <p className="py-12 text-sm text-slate-500">Carregando convênios...</p>;

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3">
        <h2 className="text-lg font-medium text-slate-800 dark:text-slate-100">Convênios / Empresas</h2>
        <button
          type="button"
          className="rounded px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
          onClick={() => setForm({ ...VAZIO })}
        >
          Novo convênio
        </button>
      </div>
      <p className="mb-6 text-sm text-slate-500">
        Particular, convênios, empresas e administradoras de benefícios usados no agendamento.
      </p>
      {erro ? <p className="mb-4 text-sm text-red-600">{erro}</p> : null}

      {form ? (
        <div className="mb-6 max-w-2xl rounded-md border border-slate-200 p-4 dark:border-white/10">
          <p className="mb-3 text-sm font-medium">{form.id ? 'Editar' : 'Novo cadastro'}</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className={`${labelClass} sm:col-span-2`}>
              Nome
              <input className={inputClass} value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
            </label>
            <label className={labelClass}>
              Tipo
              <select
                className={inputClass}
                value={form.tipo}
                onChange={(e) => setForm({ ...form, tipo: e.target.value as TipoConvenioConsultorio })}
              >
                {TIPO_CONVENIO_CONSULTORIO.map((t) => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </label>
            <label className={labelClass}>
              Registro ANS
              <input className={inputClass} value={form.registro_ans} onChange={(e) => setForm({ ...form, registro_ans: e.target.value })} />
            </label>
            <label className={labelClass}>
              Telefone
              <input
                className={inputClass}
                value={formatTelefone(form.telefone)}
                onChange={(e) => setForm({ ...form, telefone: formatTelefone(e.target.value) })}
              />
            </label>
            <label className={`${labelClass} sm:col-span-2`}>
              Observações
              <input className={inputClass} value={form.observacoes} onChange={(e) => setForm({ ...form, observacoes: e.target.value })} />
            </label>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" className="rounded px-3 py-1.5 text-sm text-slate-600" onClick={() => setForm(null)}>
              Cancelar
            </button>
            <button
              type="button"
              disabled={salvando}
              className="rounded px-4 py-1.5 text-sm font-medium text-white disabled:opacity-60"
              style={{ backgroundColor: TEAL }}
              onClick={() => void salvar()}
            >
              Salvar
            </button>
          </div>
        </div>
      ) : null}

      {lista.length === 0 && !form ? (
        <p className="text-sm text-slate-400">Nenhum convênio cadastrado.</p>
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-white/10">
          {lista.map((item) => (
            <li key={item.id} className="flex items-center justify-between gap-3 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{item.nome}</p>
                <p className="truncate text-xs text-slate-500">
                  {item.tipo_label}
                  {item.registro_ans ? ` · ANS ${item.registro_ans}` : ''}
                  {item.telefone ? ` · ${item.telefone}` : ''}
                </p>
              </div>
              <div className="flex shrink-0">
                <button
                  type="button"
                  className="rounded p-1.5 text-slate-500 hover:bg-slate-50"
                  onClick={() =>
                    setForm({
                      id: item.id,
                      nome: item.nome,
                      tipo: item.tipo,
                      registro_ans: item.registro_ans,
                      telefone: item.telefone,
                      observacoes: item.observacoes,
                    })
                  }
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  className="rounded p-1.5 text-slate-500 hover:bg-red-50 hover:text-red-600"
                  onClick={() => void excluir(item)}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
