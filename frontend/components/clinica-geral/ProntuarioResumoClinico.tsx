'use client';

import { useState, type ReactNode } from 'react';
import { BriefcaseMedical, ChevronRight, ClipboardList, MessageCircle, Paperclip, Video } from 'lucide-react';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Evolucao, Paciente, PacienteAnexo, Prescricao } from '@/lib/clinica-geral-types';

const ABAS = [
  { id: 'DIAG', label: 'DIAG' },
  { id: 'TRAT', label: 'TRAT' },
  { id: 'ALEG', label: 'ALEG' },
  { id: 'HAB', label: 'HAB' },
  { id: 'CIR', label: 'CIR' },
  { id: 'AF', label: 'AF' },
] as const;

type Painel = 'clinico' | 'evolucoes' | 'anexos' | 'chat' | 'tele';

type ProntuarioResumoClinicoProps = {
  paciente: Paciente;
  evolucoes: Evolucao[];
  prescricoes: Prescricao[];
  anexos: PacienteAnexo[];
};

export function ProntuarioResumoClinico({ paciente, evolucoes, prescricoes, anexos }: ProntuarioResumoClinicoProps) {
  const [aba, setAba] = useState<(typeof ABAS)[number]['id']>('DIAG');
  const [painel, setPainel] = useState<Painel>('clinico');
  const [aberto, setAberto] = useState(true);

  const diagnosticos = evolucoes.map((e) => e.avaliacao).filter(Boolean);
  const tratamentos = [
    ...evolucoes.map((e) => e.plano).filter(Boolean),
    ...prescricoes.flatMap((p) => p.itens.map((i) => i.medicamento).filter(Boolean)),
  ];
  const alergias = paciente.alergias.trim() ? [paciente.alergias] : [];

  const itens =
    aba === 'DIAG' ? diagnosticos : aba === 'TRAT' ? tratamentos : aba === 'ALEG' ? alergias : [];

  return (
    <aside className="flex min-h-[420px] border-l border-slate-200 bg-white">
      <div className="flex w-10 flex-col items-center gap-3 border-r border-slate-100 py-3 text-slate-400">
        <IconBtn ativo={painel === 'clinico'} title="Resumo clínico" onClick={() => setPainel('clinico')}>
          <BriefcaseMedical className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'evolucoes'} title="Evoluções" onClick={() => setPainel('evolucoes')}>
          <ClipboardList className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'anexos'} title="Anexos" onClick={() => setPainel('anexos')}>
          <Paperclip className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'chat'} title="Mensagens" onClick={() => setPainel('chat')}>
          <MessageCircle className="h-4 w-4" />
        </IconBtn>
        <IconBtn ativo={painel === 'tele'} title="Teleconsulta" onClick={() => setPainel('tele')}>
          <Video className="h-4 w-4" />
        </IconBtn>
      </div>

      <div className="w-64 min-w-[220px] p-3">
        {painel === 'clinico' ? (
          <>
            <button type="button" onClick={() => setAberto((v) => !v)} className="mb-3 flex w-full items-center justify-between text-left">
              <span className="text-xs font-bold tracking-wide text-slate-700">RESUMO CLÍNICO</span>
              <ChevronRight className={`h-4 w-4 text-slate-400 transition ${aberto ? 'rotate-90' : ''}`} />
            </button>
            {aberto ? (
              <>
                <div className="mb-3 flex flex-wrap gap-2 text-xs">
                  {ABAS.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setAba(item.id)}
                      className={`pb-0.5 ${aba === item.id ? 'font-semibold' : 'text-slate-400'}`}
                      style={aba === item.id ? { boxShadow: `inset 0 -2px 0 ${TEAL}`, color: TEAL } : undefined}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
                {itens.length === 0 ? (
                  <p className="text-sm text-slate-400">Ainda não há informações</p>
                ) : (
                  <ul className="space-y-2 text-sm text-slate-700">
                    {itens.map((texto, i) => (
                      <li key={`${aba}-${i}`} className="rounded-md bg-slate-50 px-2 py-1.5">
                        {texto}
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : null}
          </>
        ) : null}

        {painel === 'evolucoes' ? (
          <ListaSimples titulo="Evoluções" vazio="Nenhuma evolução." itens={evolucoes.map((e) => e.avaliacao || e.subjetivo || `Consulta #${e.consulta}`)} />
        ) : null}
        {painel === 'anexos' ? (
          <div>
            <p className="mb-2 text-xs font-bold tracking-wide text-slate-700">ANEXOS</p>
            {anexos.length === 0 ? (
              <p className="text-sm text-slate-400">Nenhum anexo.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {anexos.map((a) => (
                  <li key={a.id}>
                    <a href={a.url} target="_blank" rel="noreferrer" className="underline" style={{ color: TEAL }}>
                      {a.nome}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
        {painel === 'chat' ? <p className="text-sm text-slate-400">Mensagens entram na agenda e no WhatsApp do consultório.</p> : null}
        {painel === 'tele' ? <p className="text-sm text-slate-400">A teleconsulta abre no atendimento do horário marcado.</p> : null}
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
    <button
      type="button"
      title={title}
      onClick={onClick}
      className="rounded p-1.5"
      style={ativo ? { color: TEAL } : undefined}
    >
      {children}
    </button>
  );
}

function ListaSimples({ titulo, vazio, itens }: { titulo: string; vazio: string; itens: string[] }) {
  return (
    <div>
      <p className="mb-2 text-xs font-bold tracking-wide text-slate-700">{titulo.toUpperCase()}</p>
      {itens.length === 0 ? <p className="text-sm text-slate-400">{vazio}</p> : (
        <ul className="space-y-2 text-sm text-slate-700">
          {itens.map((texto, i) => (
            <li key={`${titulo}-${i}`}>{texto}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
