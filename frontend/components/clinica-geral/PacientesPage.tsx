'use client';

import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { archivePaciente, listPacientes } from '@/lib/clinica-geral-api';
import type { PacienteLista } from '@/lib/clinica-geral-types';
import { displayName } from '@/lib/clinica-geral-utils';

const TEAL = '#0D9B9B';
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
                letra === l ? 'border-transparent text-white' : 'border-slate-200 bg-white text-slate-600'
              }`}
              style={letra === l ? { backgroundColor: TEAL } : undefined}
            >
              {l === 'TODOS' ? 'Todos' : l}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-3 rounded bg-slate-100 px-4 py-2 text-sm text-slate-600">
        Pacientes — Total de {lista.length} paciente{lista.length === 1 ? '' : 's'} cadastrado
        {lista.length === 1 ? '' : 's'}
      </div>

      {erro && <p className="mb-3 text-sm text-red-600">{erro}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Carregando pacientes...</p>
      ) : lista.length === 0 ? (
        <p className="text-sm text-slate-500">Nenhum paciente encontrado.</p>
      ) : (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
          {lista.map((p) => (
            <li key={p.id} className="flex items-center gap-4 px-4 py-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-200 text-sm text-slate-600">
                {(p.nome_social || p.nome).slice(0, 1).toUpperCase()}
              </span>
              <button
                type="button"
                className="min-w-0 flex-1 text-left"
                onClick={() => router.push(`${base}/${p.id}`)}
              >
                <p className="font-medium text-slate-800">{displayName(p.nome, p.nome_social)}</p>
                <p className="text-sm text-slate-500">
                  {p.telefone || 'sem telefone'} · {p.email || 'sem e-mail'}
                </p>
              </button>
              <button
                type="button"
                onClick={() => void excluir(p.id, displayName(p.nome, p.nome_social))}
                className="text-sm text-red-500 hover:underline"
              >
                Excluir
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
