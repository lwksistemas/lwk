'use client';

import { useEffect, useState } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import {
  createTipoConsulta,
  deleteTipoConsulta,
  listTiposConsulta,
  updateTipoConsulta,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { TipoConsultaCatalogo } from '@/lib/clinica-geral-types';
import { formatBRL } from '@/lib/clinica-geral-utils';

const inputClass = 'mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal';
const labelClass = 'block text-[13px] font-bold text-slate-700 dark:text-slate-200';
const DURACOES = [0, 5, 10, 15, 20, 30, 45, 60];

const VAZIO = {
  nome: '',
  duracao_minutos: 0,
  valor: '',
};

function valorInput(valor: string | null | undefined) {
  if (!valor) return '';
  return String(valor).replace('.', ',');
}

export function TiposConsultaPage() {
  const [lista, setLista] = useState<TipoConsultaCatalogo[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [form, setForm] = useState<(typeof VAZIO & { id?: number }) | null>(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = async () => {
    setLista(await listTiposConsulta());
  };

  useEffect(() => {
    void carregar()
      .catch(() => setErro('Não foi possível carregar os tipos de consulta.'))
      .finally(() => setLoading(false));
  }, []);

  const salvar = async () => {
    if (!form?.nome.trim()) return;
    setSalvando(true);
    setErro('');
    try {
      const bruto = form.valor.replace(',', '.').trim();
      const payload = {
        nome: form.nome.trim(),
        duracao_minutos: form.duracao_minutos,
        valor: bruto ? bruto : null,
      };
      if (form.id) await updateTipoConsulta(form.id, payload);
      else await createTipoConsulta(payload);
      setForm(null);
      await carregar();
    } catch {
      setErro('Não foi possível salvar o tipo de consulta.');
    } finally {
      setSalvando(false);
    }
  };

  const excluir = async (item: TipoConsultaCatalogo) => {
    if (!confirm(`Excluir o tipo "${item.nome}"?`)) return;
    try {
      await deleteTipoConsulta(item.id);
      await carregar();
    } catch {
      setErro('Não foi possível excluir o tipo de consulta.');
    }
  };

  if (loading) return <p className="py-12 text-sm text-slate-500">Carregando tipos de consulta...</p>;

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3">
        <h2 className="text-lg font-medium text-slate-800 dark:text-slate-100">Tipos de consulta</h2>
        <button
          type="button"
          className="rounded px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
          onClick={() => setForm({ ...VAZIO })}
        >
          Novo tipo
        </button>
      </div>
      <p className="mb-6 text-sm text-slate-500">
        Primeira consulta, retorno, particular e tipos próprios usados no agendamento.
      </p>
      {erro ? <p className="mb-4 text-sm text-red-600">{erro}</p> : null}

      {form ? (
        <div className="mb-6 max-w-2xl rounded-md border border-slate-200 p-4 dark:border-white/10">
          <p className="mb-3 text-sm font-medium">{form.id ? 'Editar tipo' : 'Novo tipo'}</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className={`${labelClass} sm:col-span-2`}>
              Nome
              <input className={inputClass} value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
            </label>
            <label className={labelClass}>
              Duração
              <select
                className={inputClass}
                value={form.duracao_minutos}
                onChange={(e) => setForm({ ...form, duracao_minutos: Number(e.target.value) })}
              >
                {DURACOES.map((n) => (
                  <option key={n} value={n}>{n === 0 ? 'Padrão da agenda' : `${n} min`}</option>
                ))}
              </select>
            </label>
            <label className={labelClass}>
              Valor (opcional)
              <input
                className={inputClass}
                inputMode="decimal"
                placeholder="0,00"
                value={form.valor}
                onChange={(e) => setForm({ ...form, valor: e.target.value })}
              />
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
        <p className="text-sm text-slate-400">Nenhum tipo cadastrado.</p>
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-white/10">
          {lista.map((item) => (
            <li key={item.id} className="flex items-center justify-between gap-3 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{item.nome}</p>
                <p className="truncate text-xs text-slate-500">
                  {item.duracao_minutos ? `${item.duracao_minutos} min` : 'Duração padrão'}
                  {item.valor ? ` · ${formatBRL(item.valor)}` : ''}
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
                      duracao_minutos: item.duracao_minutos || 0,
                      valor: valorInput(item.valor),
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
