'use client';

import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { Archive, Clock, Trash2 } from 'lucide-react';
import { archivePaciente, listPacientes } from '@/lib/clinica-geral-api';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { PacienteLista } from '@/lib/clinica-geral-types';
import { displayName, toISODate } from '@/lib/clinica-geral-utils';

const LETRAS = ['TODOS', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')];

export function PacientesPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const search = useSearchParams();
  const q = search.get('q') || '';
  const letra = (search.get('letra') || 'TODOS').toUpperCase();
  const base = `/loja/${slug}/clinica-geral/pacientes`;

  const [lista, setLista] = useState<PacienteLista[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');

  const carregar = useCallback(async () => {
    setLoading(true);
    setErro('');
    try {
      setLista(await listPacientes({ letra, q }));
    } catch {
      setErro('Não foi possível carregar os pacientes.');
    } finally {
      setLoading(false);
    }
  }, [letra, q]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const setLetra = (l: string) => {
    const qs = new URLSearchParams();
    if (l !== 'TODOS') qs.set('letra', l);
    if (q) qs.set('q', q);
    const tail = qs.toString();
    router.replace(tail ? `${base}?${tail}` : base);
  };

  const excluir = async (id: number, nome: string) => {
    if (!window.confirm(`Arquivar ${nome}?`)) return;
    await archivePaciente(id);
    await carregar();
  };

  return (
    <div className="p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Link
          href={`${base}/novo`}
          className="rounded-md px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
        >
          Novo paciente
        </Link>
        <div className="flex flex-wrap gap-1">
          {LETRAS.map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => setLetra(l)}
              className={`min-w-8 rounded border px-1.5 py-1 text-xs ${
                letra === l ? 'border-transparent text-white' : 'border-slate-200 bg-white text-slate-600 dark:border-white/20 dark:bg-[#2F2E5B] dark:text-slate-100'
              }`}
              style={letra === l ? { backgroundColor: TEAL } : undefined}
            >
              {l === 'TODOS' ? 'Todos' : l}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-3 rounded bg-slate-100 px-4 py-2 text-sm text-slate-600 dark:bg-[#252448] dark:text-slate-200">
        Pacientes — Total de {lista.length} paciente{lista.length === 1 ? '' : 's'} cadastrado
        {lista.length === 1 ? '' : 's'}
      </div>

      {erro && <p className="mb-3 text-sm text-red-600">{erro}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Carregando pacientes...</p>
      ) : lista.length === 0 ? (
        <p className="text-sm text-slate-500">Nenhum paciente encontrado.</p>
      ) : (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white dark:divide-white/10 dark:border-white/10 dark:bg-[#1E1D3A]">
          {lista.map((p) => (
            <li key={p.id} className="flex items-center gap-4 px-4 py-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-200 text-sm text-slate-600 dark:bg-white/15 dark:text-slate-100">
                {(p.nome_social || p.nome).slice(0, 1).toUpperCase()}
              </span>
              <button
                type="button"
                className="min-w-0 flex-1 text-left"
                onClick={() => router.push(`${base}/${p.id}`)}
              >
                <p className="font-medium text-slate-800 dark:text-white">
                  {displayName(p.nome, p.nome_social)} ({p.numero_prontuario || p.id})
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-300">
                  {p.telefone || 'sem telefone'} · {p.email || 'sem e-mail'}
                </p>
              </button>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  title="Arquivar"
                  onClick={() => void excluir(p.id, displayName(p.nome, p.nome_social))}
                  className="rounded border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 dark:border-white/20 dark:text-slate-300 dark:hover:bg-white/10"
                >
                  <Archive className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  title="Agendar"
                  onClick={() =>
                    router.push(`/loja/${slug}/clinica-geral/agenda?data=${toISODate(new Date())}&nova=1&paciente=${p.id}`)
                  }
                  className="rounded border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 dark:border-white/20 dark:text-slate-300 dark:hover:bg-white/10"
                >
                  <Clock className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  title="Excluir"
                  onClick={() => void excluir(p.id, displayName(p.nome, p.nome_social))}
                  className="rounded border border-red-200 p-1.5 text-red-500 hover:bg-red-50 dark:border-red-400/40 dark:hover:bg-red-950/40"
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
