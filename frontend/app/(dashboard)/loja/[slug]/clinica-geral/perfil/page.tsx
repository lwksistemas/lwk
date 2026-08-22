'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { UserRound } from 'lucide-react';
import { getUsuarioConsultorio } from '@/lib/clinica-geral-api';
import type { UsuarioConsultorio } from '@/lib/clinica-geral-types';

const TEAL = '#0D9B9B';

export default function ClinicaGeralPerfilPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [usuario, setUsuario] = useState<UsuarioConsultorio | null>(null);

  useEffect(() => {
    void getUsuarioConsultorio()
      .then(setUsuario)
      .catch(() => setUsuario({ username: '', nome: '', email: '' }));
  }, []);

  return (
    <div className="mx-auto max-w-xl space-y-4 p-8">
      <div className="flex items-center gap-3">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
          <UserRound className="h-6 w-6 text-slate-500" />
        </span>
        <div>
          <h1 className="text-xl font-semibold text-slate-800">Meu perfil</h1>
          <p className="text-sm text-slate-500">Dados da conta usada neste consultório</p>
        </div>
      </div>
      <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm">
        <p className="text-slate-500">Nome</p>
        <p className="mb-3 font-medium text-slate-800">{usuario?.nome || '—'}</p>
        <p className="text-slate-500">Usuário</p>
        <p className="mb-3 font-medium text-slate-800">{usuario?.username || '—'}</p>
        <p className="text-slate-500">E-mail</p>
        <p className="font-medium text-slate-800">{usuario?.email || '—'}</p>
      </div>
      <Link
        href={`/loja/${slug}/trocar-senha`}
        className="inline-flex rounded-md px-4 py-2 text-sm font-medium text-white"
        style={{ backgroundColor: TEAL }}
      >
        Alterar senha
      </Link>
    </div>
  );
}
