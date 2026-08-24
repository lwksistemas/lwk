'use client';

import { useEffect, useState } from 'react';
import { Pencil, Trash2 } from 'lucide-react';
import {
  createFuncionario,
  deleteFuncionario,
  listFuncionarios,
  updateFuncionario,
} from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import { CARGO_FUNCIONARIO, type CargoFuncionario, type FuncionarioLoja } from '@/lib/clinica-geral-types';
import { formatTelefone } from '@/lib/format-br';

const inputClass = 'mt-0.5 w-full rounded border border-slate-300 px-2 py-1.5 text-sm font-normal';
const labelClass = 'block text-[13px] font-bold text-slate-700 dark:text-slate-200';

const VAZIO = {
  nome: '',
  cargo: 'recepcao' as CargoFuncionario,
  email: '',
  telefone: '',
};

export function FuncionariosPage() {
  const [lista, setLista] = useState<FuncionarioLoja[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [form, setForm] = useState<(typeof VAZIO & { id?: number }) | null>(null);
  const [salvando, setSalvando] = useState(false);

  const carregar = async () => {
    setLista(await listFuncionarios());
  };

  useEffect(() => {
    void carregar()
      .catch(() => setErro('Não foi possível carregar os funcionários.'))
      .finally(() => setLoading(false));
  }, []);

  const salvar = async () => {
    if (!form?.nome.trim()) return;
    setSalvando(true);
    setErro('');
    try {
      const payload = {
        nome: form.nome.trim(),
        cargo: form.cargo,
        email: form.email.trim(),
        telefone: form.telefone.trim(),
      };
      if (form.id) await updateFuncionario(form.id, payload);
      else await createFuncionario(payload);
      setForm(null);
      await carregar();
    } catch {
      setErro('Não foi possível salvar o funcionário.');
    } finally {
      setSalvando(false);
    }
  };

  const excluir = async (item: FuncionarioLoja) => {
    if (!confirm(`Excluir o funcionário "${item.nome}"?`)) return;
    try {
      await deleteFuncionario(item.id);
      await carregar();
    } catch {
      setErro('Não foi possível excluir o funcionário.');
    }
  };

  if (loading) return <p className="py-12 text-sm text-slate-500">Carregando funcionários...</p>;

  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-3">
        <h2 className="text-lg font-medium text-slate-800 dark:text-slate-100">Funcionários da loja</h2>
        <button
          type="button"
          className="rounded px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
          onClick={() => setForm({ ...VAZIO })}
        >
          Novo funcionário
        </button>
      </div>
      <p className="mb-6 text-sm text-slate-500">
        Cadastro da recepção, administração e demais funcionários do consultório.
      </p>
      {erro ? <p className="mb-4 text-sm text-red-600">{erro}</p> : null}

      {form ? (
        <div className="mb-6 max-w-2xl rounded-md border border-slate-200 p-4 dark:border-white/10">
          <p className="mb-3 text-sm font-medium">{form.id ? 'Editar funcionário' : 'Novo funcionário'}</p>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label className={`${labelClass} sm:col-span-2`}>
              Nome
              <input className={inputClass} value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
            </label>
            <label className={labelClass}>
              Cargo
              <select
                className={inputClass}
                value={form.cargo}
                onChange={(e) => setForm({ ...form, cargo: e.target.value as CargoFuncionario })}
              >
                {CARGO_FUNCIONARIO.map((c) => (
                  <option key={c.id} value={c.id}>{c.label}</option>
                ))}
              </select>
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
              E-mail
              <input className={inputClass} type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
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
        <p className="text-sm text-slate-400">Nenhum funcionário cadastrado.</p>
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-white/10">
          {lista.map((f) => (
            <li key={f.id} className="flex items-center justify-between gap-3 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{f.nome}</p>
                <p className="truncate text-xs text-slate-500">
                  {f.cargo_label}
                  {f.email ? ` · ${f.email}` : ''}
                  {f.telefone ? ` · ${f.telefone}` : ''}
                </p>
              </div>
              <div className="flex shrink-0">
                <button
                  type="button"
                  className="rounded p-1.5 text-slate-500 hover:bg-slate-50"
                  onClick={() =>
                    setForm({
                      id: f.id,
                      nome: f.nome,
                      cargo: f.cargo,
                      email: f.email,
                      telefone: f.telefone,
                    })
                  }
                >
                  <Pencil className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  className="rounded p-1.5 text-slate-500 hover:bg-red-50 hover:text-red-600"
                  onClick={() => void excluir(f)}
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
