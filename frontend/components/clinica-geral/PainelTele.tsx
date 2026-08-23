'use client';

import { Copy, MessageCircle, Video } from 'lucide-react';
import { JitsiSala, salaJitsiDeUrl } from '@/components/clinica-geral/JitsiSala';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta } from '@/lib/clinica-geral-types';

type PainelTeleProps = {
  consulta: Consulta;
  info: string;
  medicoNome: string;
  emChamada: boolean;
  enviando: boolean;
  onGerar: () => void;
  onCopiar: () => void;
  onEnviar: () => void;
  onEntrar: () => void;
  onSair: () => void;
};

export function PainelTele({
  consulta,
  info,
  medicoNome,
  emChamada,
  enviando,
  onGerar,
  onCopiar,
  onEnviar,
  onEntrar,
  onSair,
}: PainelTeleProps) {
  const temSala = Boolean(consulta.tele_sala_url && consulta.tele_token);
  const sala = salaJitsiDeUrl(consulta.tele_sala_url);

  return (
    <section className="space-y-3">
      <p className="text-xs text-slate-500">Cota 10h/mês. O paciente abre o link no celular, sem instalar app.</p>
      {info ? <p className="text-sm text-slate-600">{info}</p> : null}
      <div className="flex flex-col gap-2">
        <button type="button" onClick={onGerar} className="rounded-md px-3 py-2 text-sm font-medium text-white" style={{ backgroundColor: TEAL }}>
          {temSala ? 'Atualizar sala' : 'Gerar sala'}
        </button>
        <button
          type="button"
          disabled={!temSala}
          onClick={onCopiar}
          className="flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-sm disabled:opacity-40"
        >
          <Copy className="h-3.5 w-3.5" />
          Copiar link
        </button>
        <button
          type="button"
          disabled={!consulta.paciente_telefone || enviando}
          onClick={onEnviar}
          className="flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-sm disabled:opacity-40"
        >
          <MessageCircle className="h-3.5 w-3.5" />
          {enviando ? 'Enviando...' : 'Enviar WhatsApp'}
        </button>
        <button
          type="button"
          disabled={!temSala}
          onClick={emChamada ? onSair : onEntrar}
          className="flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-sm font-medium disabled:opacity-40"
          style={{ borderColor: TEAL, color: TEAL }}
        >
          <Video className="h-3.5 w-3.5" />
          {emChamada ? 'Encerrar vídeo' : 'Entrar na sala'}
        </button>
      </div>
      {emChamada && sala ? <JitsiSala sala={sala} displayName={medicoNome || 'Médico'} altura={280} /> : null}
    </section>
  );
}
