'use client';

import { useState, type ReactNode } from 'react';
import { BriefcaseMedical, ChevronRight, ClipboardList, MessageCircle, Paperclip, Video } from 'lucide-react';
import { PainelTele } from '@/components/clinica-geral/PainelTele';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Consulta, PacienteAnexo } from '@/lib/clinica-geral-types';

type Painel = 'clinico' | 'notas' | 'anexos' | 'chat' | 'tele';

type Props = {
  consulta: Consulta;
  anexos: PacienteAnexo[];
  teleInfo: string;
  onAbrirTele: () => void;
  onRegistrarTele: () => void;
};

export function AtendimentoPainelDireito({ consulta, anexos, teleInfo, onAbrirTele, onRegistrarTele }: Props) {
  const [painel, setPainel] = useState<Painel>('tele');

  return (
    <aside className="flex min-h-[420px] border-l border-slate-200 bg-white">
      <div className="flex w-10 flex-col items-center gap-3 border-r border-slate-100 py-3 text-slate-400">
        <IconBtn ativo={painel === 'clinico'} title="Resumo clínico" onClick={() => setPainel('clinico')}>
          <BriefcaseMedical className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'notas'} title="Notas" onClick={() => setPainel('notas')}>
          <ClipboardList className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'anexos'} title="Anexos" onClick={() => setPainel('anexos')}>
          <Paperclip className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'chat'} title="Mensagens" onClick={() => setPainel('chat')}>
          <MessageCircle className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'tele'} title="Telemedicina" onClick={() => setPainel('tele')}>
          <Video className="h-4 w-4" />
        </IconBtn>
      </div>
      <div className="w-64 min-w-[220px] p-3">
        {painel === 'tele' ? (
          <>
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-bold tracking-wide text-slate-700">TELEMEDICINA</span>
              <ChevronRight className="h-4 w-4 text-slate-400" />
            </div>
            {consulta.modalidade === 'tele' ? (
              <PainelTele consulta={consulta} info={teleInfo} onAbrir={onAbrirTele} onRegistrar={onRegistrarTele} />
            ) : (
              <p className="text-sm text-slate-400">Esse paciente não possui nenhuma Teleconsulta agendada.</p>
            )}
          </>
        ) : null}
        {painel === 'anexos' ? (
          anexos.length ? (
            <ul className="space-y-2 text-sm">
              {anexos.map((a) => (
                <li key={a.id}>
                  <a href={a.url} target="_blank" rel="noreferrer" className="underline" style={{ color: TEAL }}>
                    {a.nome}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400">Nenhum anexo.</p>
          )
        ) : null}
        {painel === 'clinico' || painel === 'notas' || painel === 'chat' ? (
          <p className="text-sm text-slate-400">Use as abas da esquerda para registrar o atendimento.</p>
        ) : null}
      </div>
    </aside>
  );
}

function IconBtn({
  ativo,
  title,
  onClick,
  children,
}: {
  ativo: boolean;
  title: string;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button type="button" title={title} onClick={onClick} className="rounded p-1.5" style={ativo ? { color: TEAL, boxShadow: `inset 3px 0 0 ${TEAL}` } : undefined}>
      {children}
    </button>
  );
}
