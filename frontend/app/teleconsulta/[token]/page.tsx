'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { AlertCircle, Video } from 'lucide-react';
import { JitsiSala } from '@/components/clinica-geral/JitsiSala';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import { TEAL } from '@/lib/clinica-geral-theme';

type SalaPublica = {
  paciente_nome: string;
  medico_nome: string;
  clinica_nome: string;
  tele_sala_url: string;
  sala: string;
};

export default function TeleconsultaPacientePage() {
  const params = useParams();
  const tokenRaw = String(params.token || '');
  let token = tokenRaw;
  try {
    token = decodeURIComponent(tokenRaw);
  } catch {
    token = tokenRaw;
  }

  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [sala, setSala] = useState<SalaPublica | null>(null);
  const [entrou, setEntrou] = useState(false);

  useEffect(() => {
    if (!token) return;
    void (async () => {
      try {
        const res = await fetch(`${getPrimaryApiBaseUrl()}/clinica-geral/teleconsulta/${encodeURIComponent(token)}/`);
        const data = await res.json();
        if (!res.ok) {
          setErro(data.error || 'Link inválido ou expirado.');
          return;
        }
        setSala(data);
      } catch {
        setErro('Não foi possível abrir a teleconsulta. Verifique a conexão.');
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  if (loading) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center p-6 text-sm text-slate-500">
        Carregando teleconsulta...
      </div>
    );
  }

  if (erro || !sala) {
    return (
      <div className="mx-auto flex min-h-[100dvh] max-w-md flex-col items-center justify-center p-6 text-center">
        <AlertCircle className="mb-3 h-10 w-10 text-red-500" />
        <h1 className="mb-2 text-lg font-semibold text-slate-800">Link indisponível</h1>
        <p className="text-sm text-slate-600">{erro || 'Esta teleconsulta não está disponível.'}</p>
      </div>
    );
  }

  if (entrou) {
    return (
      <div className="flex min-h-[100dvh] flex-col bg-slate-900">
        <p className="px-4 py-2 text-center text-xs text-white/70">
          {sala.clinica_nome} · {sala.medico_nome}
        </p>
        <div className="flex-1">
          <JitsiSala sala={sala.sala} displayName={sala.paciente_nome} altura={Math.max(420, (typeof window !== 'undefined' ? window.innerHeight : 640) - 40)} />
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-[100dvh] max-w-md flex-col justify-center p-6">
      <div className="rounded-2xl bg-white p-6 shadow-lg">
        <p className="mb-1 text-center text-sm font-medium" style={{ color: TEAL }}>
          {sala.clinica_nome}
        </p>
        <h1 className="mb-4 text-center text-xl font-semibold text-slate-800">Teleconsulta</h1>
        <p className="mb-1 text-sm text-slate-600">Olá, {sala.paciente_nome}.</p>
        <p className="mb-5 text-sm text-slate-600">
          {sala.medico_nome} está pronto para o atendimento. Permita câmera e microfone ao entrar.
        </p>
        <button
          type="button"
          onClick={() => setEntrou(true)}
          className="flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold text-white"
          style={{ backgroundColor: TEAL }}
        >
          <Video className="h-4 w-4" />
          Entrar na consulta
        </button>
      </div>
    </div>
  );
}
